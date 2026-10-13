"""Pruebas del cliente Evolus con sesión falsa (sin red)."""
import json

import pytest

from evolus.cliente import ClienteEvolus, ErrorEvolus
from evolus.replay import ClienteReplay, Grabadora

KEY = "clave-secreta-123"


class Resp:
    def __init__(self, status=200, cuerpo=None, ctype="application/json"):
        self.status_code = status
        self._c = cuerpo
        self.headers = {"Content-Type": ctype}
        self.text = json.dumps(cuerpo)

    def json(self):
        return self._c


class Sesion:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []

    def request(self, metodo, url, headers=None, json=None, timeout=None):
        self.llamadas.append((metodo, url, headers, json))
        r = self.respuestas.pop(0)
        return r


def cliente(respuestas, **kw):
    s = Sesion(respuestas)
    pausas = []
    c = ClienteEvolus("https://x/api/v1", KEY, "app-1", sesion=s,
                      esperar=pausas.append, **kw)
    c.pausas = pausas
    return c, s


def test_cabeceras_y_url():
    c, s = cliente([Resp(200, [{"slug": "translate"}])])
    assert c.herramientas() == [{"slug": "translate"}]
    m, url, h, _ = s.llamadas[0]
    assert m == "GET" and url == "https://x/api/v1/ai-tools"
    assert h["X-ApiKey"] == KEY and h["X-Application-Id"] == "app-1"


def test_401_problem_json():
    c, _ = cliente([Resp(401, {"errorCode": "auth.unauthorized", "traceId": "t1"},
                         "application/problem+json")])
    with pytest.raises(ErrorEvolus) as e:
        c.herramientas()
    assert e.value.status == 401
    assert e.value.codigo == "auth.unauthorized" and e.value.traza == "t1"


def test_reintento_429_luego_exito():
    c, s = cliente([Resp(429, {}), Resp(200, {"output": "ok"})])
    assert c.ejecutar_herramienta("translate", "hola")["output"] == "ok"
    assert len(s.llamadas) == 2 and 1 in c.pausas
    assert s.llamadas[0][3] == {"text": "hola"}


def test_reintentos_agotados():
    c, s = cliente([Resp(503, {}), Resp(503, {}), Resp(503, {}), Resp(503, {})])
    with pytest.raises(ErrorEvolus) as e:
        c.herramientas()
    assert e.value.status == 503 and len(s.llamadas) == 4
    assert [p for p in c.pausas if p in (1, 2, 4)] == [1, 2, 4]


def test_creditos_acumulados():
    c, _ = cliente([Resp(200, {"creditsConsumed": 1.5}),
                    Resp(200, {"creditsConsumed": 2.0}), Resp(200, {"x": 1})])
    for _ in range(3):
        c.ejecutar_herramienta("translate", "a")
    assert c.creditos_consumidos == pytest.approx(3.5)


def test_esperar_ejecucion_completa():
    c, _ = cliente([Resp(200, {"status": "Running"}), Resp(200, {"status": "Completed", "r": 1})])
    assert c.esperar_ejecucion("w", "e")["status"] == "Completed"


def test_esperar_ejecucion_timeout():
    c, _ = cliente([Resp(200, {"status": "Running"})] * 10)
    with pytest.raises(ErrorEvolus):
        c.esperar_ejecucion("w", "e", timeout=4, intervalo=2)


def test_grabadora_y_replay(tmp_path):
    ruta = tmp_path / "g.jsonl"
    c, _ = cliente([Resp(200, [{"slug": "t"}]),
                    Resp(200, {"output": "hola", "creditsConsumed": 1.0})],
                   grabadora=Grabadora(ruta))
    a = c.herramientas()
    b = c.ejecutar_herramienta("translate", "hi", {"target": "es", "style": "x"})
    assert KEY not in ruta.read_text() and "X-ApiKey" not in ruta.read_text()
    r = ClienteReplay(ruta)
    assert r.herramientas() == a
    assert r.ejecutar_herramienta("translate", "hi", {"style": "x", "target": "es"}) == b
    assert r.creditos_consumidos == 1.0
    with pytest.raises(KeyError, match="grabaci"):
        r.ejecutar_herramienta("translate", "otro")
