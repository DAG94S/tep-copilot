"""Pruebas de la capa LLM: parseo, cliente (sin red), prompt sin fugas y cadena hasta la compuerta."""
import re

import numpy as np
import pytest

from core import compuerta
from llm import cliente as cl
from llm.cliente import ClienteLLM, ClienteSimulado, ErrorLLM
from llm.parseo import extraer_json, parsear
from llm.prompt import Fila, construir_mensajes
from twin import gemela

VALIDO = '{"causes": ["C1"], "evidence": [{"tag": "T1", "direction": "up"}], "explanation": "Level rose."}'


def test_extraer_json_con_cercos_y_texto():
    assert extraer_json(f"Claro:\n```json\n{VALIDO}\n```\nListo.")["causes"] == ["C1"]
    assert extraer_json(f"antes {VALIDO} después")["explanation"] == "Level rose."


def test_extraer_json_llaves_anidadas_y_en_cadenas():
    d = extraer_json('x {"a": {"b": {"c": 1}}, "s": "una } llave"} y {"otro": 2}')
    assert d == {"a": {"b": {"c": 1}}, "s": "una } llave"}


def test_extraer_json_sin_json():
    with pytest.raises(ValueError):
        extraer_json("no hay nada")


def test_parsear_valido():
    diag, err = parsear(VALIDO)
    assert err is None and diag.causas == ["C1"] and diag.evidencia[0].direccion == "up"


@pytest.mark.parametrize("texto", [
    VALIDO[:-1] + ', "action": "close"}',
    VALIDO.replace('"up"', '"sideways"'),
    "sin json",
])
def test_parsear_invalido(texto):
    diag, err = parsear(texto)
    assert diag is None and err


# --- cliente ---
class FakeResp:
    def __init__(self, status, datos):
        self.status_code, self._d, self.text = status, datos, str(datos)

    def json(self):
        return self._d


def _ok(*textos):
    return FakeResp(200, {"choices": [{"message": {"content": t}} for t in textos],
                          "usage": {"prompt_tokens": 10, "completion_tokens": 5}})


def test_completar_url_cabeceras_esquema_y_extra_body(monkeypatch):
    visto = {}

    def post(url, json, headers, timeout):
        visto.update(url=url, json=json, headers=headers)
        return _ok("hola")

    monkeypatch.setattr(cl.requests, "post", post)
    c = ClienteLLM("http://h:8000/v1/", "m", api_key="K", extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    r = c.completar([{"role": "user", "content": "x"}], esquema={"type": "object"}, semilla=7)
    assert visto["url"] == "http://h:8000/v1/chat/completions"
    assert visto["headers"]["Authorization"] == "Bearer K"
    assert visto["json"]["response_format"]["json_schema"] == {"name": "diagnostico", "schema": {"type": "object"}, "strict": True}
    assert visto["json"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert visto["json"]["seed"] == 7
    assert r.textos == ["hola"] and r.uso == {"prompt_tokens": 10, "completion_tokens": 5}


def test_sin_api_key_ni_esquema(monkeypatch):
    visto = {}
    monkeypatch.setattr(cl.requests, "post", lambda url, json, headers, timeout: visto.update(j=json, h=headers) or _ok("a"))
    ClienteLLM("http://h/v1", "m").completar([])
    assert "Authorization" not in visto["h"] and "response_format" not in visto["j"]


def test_relleno_hasta_n_si_el_servidor_devuelve_uno(monkeypatch):
    semillas = []
    monkeypatch.setattr(cl.requests, "post",
                        lambda url, json, headers, timeout: semillas.append(json.get("seed")) or _ok(f"t{len(semillas)}"))
    r = ClienteLLM("http://h/v1", "m").completar([], n=3, semilla=10)
    assert r.textos == ["t1", "t2", "t3"] and semillas == [10, 11, 12]
    assert r.uso["prompt_tokens"] == 30


def test_reintento_tras_503(monkeypatch):
    respuestas = [FakeResp(503, "busy"), _ok("bien")]
    esperas = []
    monkeypatch.setattr(cl.requests, "post", lambda *a, **k: respuestas.pop(0))
    r = ClienteLLM("http://h/v1", "m", esperar=esperas.append).completar([])
    assert r.textos == ["bien"] and esperas == [1]


def test_error_tras_agotar_reintentos(monkeypatch):
    llamadas, esperas = [], []
    monkeypatch.setattr(cl.requests, "post", lambda *a, **k: llamadas.append(1) or FakeResp(503, "busy"))
    with pytest.raises(ErrorLLM) as e:
        ClienteLLM("http://h/v1", "m", esperar=esperas.append).completar([])
    assert e.value.status == 503 and len(llamadas) == 4 and esperas == [1, 2, 4]


def test_error_400_no_reintenta(monkeypatch):
    llamadas = []
    monkeypatch.setattr(cl.requests, "post", lambda *a, **k: llamadas.append(1) or FakeResp(400, "mal"))
    with pytest.raises(ErrorLLM):
        ClienteLLM("http://h/v1", "m", esperar=lambda s: None).completar([])
    assert len(llamadas) == 1


def test_desde_env(tmp_path, monkeypatch):
    for k in ("X_ENDPOINT", "X_API_KEY", "X_MODEL"):
        monkeypatch.delenv(k, raising=False)
    env = tmp_path / ".env"
    env.write_text("# c\nX_ENDPOINT=http://e/v1\nX_MODEL=gemma\nX_API_KEY=abc\n")
    c = cl.desde_env("X", str(env))
    assert (c.base_url, c.modelo, c.api_key) == ("http://e/v1", "gemma", "abc")
    monkeypatch.setenv("X_MODEL", "otro")
    assert cl.desde_env("X", str(env)).modelo == "otro"


def test_cliente_simulado_circular():
    s = ClienteSimulado(["a", "b"])
    assert s.completar([], n=3).textos == ["a", "b", "a"]
    assert s.completar([]).textos == ["b"]


# --- prompt ---
def _filas():
    return [Fila(i, 10.0 - i, (-1) ** i * (5.0 - i / 3), 100.0 + i * 1.23456, 90.0 + i) for i in range(6)]


def _texto(msgs):
    return "\n".join(m["content"] for m in msgs)


@pytest.mark.parametrize("nivel", (0, 1, 2))
def test_prompt_contiene_tags_y_codigos(nivel):
    vista = gemela.construir(nivel)
    t = _texto(construir_mensajes(vista, _filas()))
    assert all(v.tag in t for v in vista.variables)
    assert all(c.codigo in t for c in vista.catalogo)


@pytest.mark.parametrize("nivel", (1, 2))
def test_prompt_sin_fugas(nivel):
    t = _texto(construir_mensajes(gemela.construir(nivel), _filas()))
    golpes = [p for p in gemela.FUGAS[nivel] if re.search(p, t)]
    assert golpes == []


def test_prompt_orden_formato_y_ejemplo():
    vista = gemela.construir(2)
    msgs = construir_mensajes(vista, _filas())
    assert [m["role"] for m in msgs] == ["system", "user"]
    u = msgs[1]["content"]
    primera = vista.variables[0]
    assert f"{primera.tag} | {primera.descripcion} | {primera.unidad} | 90 | 100 | +5 | 10" in u
    assert "C00" in u and "XX-000" in u
    assert "C00" not in {c.codigo for c in vista.catalogo}
    assert "XX-000" not in {v.tag for v in vista.variables}


# --- cadena ---
def test_humo_simulado_parseo_compuerta():
    vista = gemela.construir(1)
    tag, codigo = vista.variables[3].tag, vista.catalogo[0].codigo
    texto = ('```json\n{"causes": ["%s"], "evidence": [{"tag": "%s", "direction": "up"}], '
             '"explanation": "The level rose steadily."}\n```' % (codigo, tag))
    r = ClienteSimulado([texto]).completar(construir_mensajes(vista, _filas()), n=1)
    diag, err = parsear(r.textos[0])
    assert err is None
    z = np.zeros(52)
    z[3] = 6.0
    v = compuerta.verificar(diag, tags=[x.tag for x in vista.variables],
                            codigos={c.codigo for c in vista.catalogo}, z=z)
    assert v.estado == "VERIFICADO"


def test_extraer_json_ignora_bloques_de_pensamiento():
    from llm.parseo import extraer_json
    texto = '<thought>The user wants {"ok": true} ...</thought>\n{"causes": ["C1"]}'
    assert extraer_json(texto) == {"causes": ["C1"]}
    with pytest.raises(ValueError):
        extraer_json('<thought>cortado por max_tokens {"ok": true}')


def test_desde_env_lee_extra_body_y_timeout(tmp_path, monkeypatch):
    from llm.cliente import desde_env
    env = tmp_path / ".env"
    env.write_text('X_ENDPOINT=http://h/v1\nX_MODEL=m\nX_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}\nX_TIMEOUT=300\n')
    c = desde_env(prefijo="X", ruta_env=str(env))
    assert c.extra_body == {"chat_template_kwargs": {"enable_thinking": False}} and c.timeout == 300.0


def test_sin_soporte_de_n_pide_de_a_una(monkeypatch):
    import llm.cliente as cl
    cuerpos = []

    class R:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "{}"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    monkeypatch.setattr(cl.requests, "post", lambda url, json, headers, timeout: (cuerpos.append(json), R())[1])
    c = cl.ClienteLLM("http://h/v1", "m", soporta_n=False)
    assert len(c.completar([{"role": "user", "content": "x"}], n=3, temperatura=0.7).textos) == 3
    assert len(cuerpos) == 3 and all("n" not in b for b in cuerpos)
