"""Pruebas del agente de Evolus con sesión falsa (sin red)."""
import json

import pytest

from evolus.agente import AgenteReplay, ClienteAgente
from evolus.cliente import ErrorEvolus
from evolus.mensaje import mensaje_aprobado
from evolus.replay import Grabadora

KEY = "clave-secreta-123"


class Resp:
    def __init__(self, status=200, cuerpo=None, cabeceras=None):
        self.status_code = status
        self._c = cuerpo
        self.headers = {"Content-Type": "application/json", **(cabeceras or {})}
        self.text = json.dumps(cuerpo)

    def json(self):
        return self._c


class Sesion:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def request(self, metodo, url, headers=None, json=None, timeout=None):
        self.llamadas.append((metodo, url, headers, json, timeout))
        return self.respuestas.pop(0)


def cliente(respuestas, **kw):
    s = Sesion(respuestas)
    pausas = []
    c = ClienteAgente("https://x/v1", KEY, sesion=s, esperar=pausas.append, **kw)
    c.pausas = pausas
    return c, s


def modelos(*ids):
    return Resp(200, {"object": "list", "data": [{"id": i} for i in ids]})


def completion(texto="hola"):
    return Resp(200, {"model": "app:ag", "choices": [{"message": {"role": "assistant", "content": texto}}],
                      "usage": {"total_tokens": 7}}, {"X-Conversation-Id": "conv-1"})


def test_modelos_y_cabecera():
    c, s = cliente([modelos("a:b")])
    assert c.modelos() == [{"id": "a:b"}]
    m, url, h, _, t = s.llamadas[0]
    assert m == "GET" and url == "https://x/v1/models"
    assert h["Authorization"] == f"Bearer {KEY}" and t == 180


def test_modelo_por_defecto_uno():
    c, _ = cliente([modelos("a:b")])
    assert c.modelo_por_defecto() == "a:b"


def test_modelo_por_defecto_fijado_no_llama():
    c, s = cliente([], modelo="x:y")
    assert c.modelo_por_defecto() == "x:y" and not s.llamadas


@pytest.mark.parametrize("ids,frag", [((), "ningún"), (("a:1", "b:2"), "varios")])
def test_modelo_por_defecto_error(ids, frag):
    c, _ = cliente([modelos(*ids)])
    with pytest.raises(ErrorEvolus, match=frag):
        c.modelo_por_defecto()


def test_chat_cuerpo_grabacion_y_conversacion(tmp_path):
    ruta = tmp_path / "i.jsonl"
    c, s = cliente([modelos("a:b"), completion("texto")], grabadora=Grabadora(ruta))
    r = c.chat("mensaje")
    assert r["texto"] == "texto" and r["conversacion"] == "conv-1"
    assert r["modelo"] == "app:ag" and r["uso"] == {"total_tokens": 7}
    _, url, _, cuerpo, _ = s.llamadas[1]
    assert url == "https://x/v1/chat/completions"
    assert cuerpo == {"model": "a:b", "messages": [{"role": "user", "content": "mensaje"}]}
    assert isinstance(cuerpo["messages"][0]["content"], str)
    g = ruta.read_text()
    assert KEY not in g and "Authorization" not in g and "conv-1" in g


def test_reintento_503():
    c, s = cliente([Resp(503, {}), completion("ok")], modelo="a:b")
    assert c.chat("x")["texto"] == "ok"
    assert len(s.llamadas) == 2 and 1 in c.pausas


def test_error_4xx():
    c, _ = cliente([Resp(401, {"error": {"message": "bad key"}})], modelo="a:b")
    with pytest.raises(ErrorEvolus, match="bad key"):
        c.chat("x")


REG = {"falla": 6, "nivel": 2, "indice_alarma": 173, "estado": "PARCIAL", "confianza": 0.8,
       "causas": ["C26", "C89", "C16"], "idv_predichos": [6, 7, 1],
       "evidencia_verificada": [{"tag": "FI-288", "direction": "down"}],
       "evidencia_rechazada": [{"tag": "PV-790", "direction": "up"}],
       "evidencia_oscilante": [{"tag": "JI-704", "direction": "down"}],
       "acierto_top1": True, "acierto_top3": True}


def test_mensaje_sin_fuga_y_determinista():
    m = mensaje_aprobado(REG)
    assert m == mensaje_aprobado(dict(REG))
    assert "acierto" not in m.lower() and "IDV(6)" not in m and "IDV(7)" not in m
    assert "case" not in m.lower() and "disguise" not in m.lower() and "6" not in m.split("Alarm")[0]
    assert "C26, C89, C16" in m and "FI-288 (down)" in m
    assert "PV-790 (up) [rejected]" in m and "JI-704 (down) [oscillating]" in m


def test_mensaje_causa_aprobada_si_aparece():
    r = {**REG, "nivel": 0, "causas": ["IDV(6)", "IDV(7)"]}
    assert "IDV(6)" in mensaje_aprobado(r)


def test_replay(tmp_path):
    ruta = tmp_path / "i.jsonl"
    c, _ = cliente([modelos("a:b"), completion("texto")], grabadora=Grabadora(ruta))
    r = c.chat("mensaje")
    rp = AgenteReplay(ruta)
    r2 = rp.chat("mensaje")
    assert r2["texto"] == r["texto"] and r2["conversacion"] == "conv-1"
    with pytest.raises(KeyError, match="grabaci"):
        rp.chat("otro")


def test_error_del_modelo_como_texto():
    texto = "Your model 'gemma-4-31b-it' could not answer: The model endpoint could not be reached or did not answer in time."
    c, _ = cliente([Resp(200, {"choices": [{"message": {"content": texto}}]})], modelo="a:b")
    with pytest.raises(ErrorEvolus, match="no respondió"):
        c.chat("x")
