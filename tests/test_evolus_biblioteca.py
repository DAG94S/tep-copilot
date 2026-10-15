"""Biblioteca de Evolus y verificador del agente con sesión falsa (sin red)."""
import hashlib
import json

import pytest

from evolus.biblioteca import (formatos_documento, importar_url, listar_documentos,
                               subir_documento)
from evolus.cliente import ClienteEvolus
from evolus.replay import Grabadora
from scripts import evolus_verificar_agente as ver

KEY = "clave-secreta-123"


class Resp:
    def __init__(self, status=200, cuerpo=None):
        self.status_code, self._c = status, cuerpo
        self.headers = {"Content-Type": "application/json"}
        self.text = json.dumps(cuerpo)

    def json(self):
        return self._c


class Sesion:
    def __init__(self, respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def request(self, metodo, url, headers=None, json=None, timeout=None, **kw):
        self.llamadas.append((metodo, url, headers, json, kw))
        return self.respuestas.pop(0)


def cliente(respuestas, grab=None):
    s = Sesion(respuestas)
    return ClienteEvolus("https://x/api/v1", KEY, "app-1", sesion=s, esperar=lambda t: None, grabadora=grab), s


def test_subir_multipart_y_grabacion_sin_cabeceras(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("# hola\n", encoding="utf-8")
    graba = tmp_path / "i.jsonl"
    c, s = cliente([Resp(201, {"id": "d1"})], Grabadora(graba))
    assert subir_documento(c, "lib1", doc) == {"id": "d1"}
    m, url, h, js, kw = s.llamadas[0]
    assert m == "POST" and url == "https://x/api/v1/memories/lib1/documents?language=en"
    assert js is None and kw["files"]["file"][0] == "doc.md" and kw["files"]["file"][1] == b"# hola\n"
    assert "Content-Type" not in h
    linea = graba.read_text(encoding="utf-8")
    assert KEY not in linea and "X-ApiKey" not in linea
    reg = json.loads(linea)
    assert reg["peticion"]["sha256"] == hashlib.sha256(b"# hola\n").hexdigest()
    assert "# hola" not in linea


def test_importar_listar_formatos():
    c, s = cliente([Resp(201, {}), Resp(200, [{"id": "d1", "status": "Indexed"}]), Resp(200, [".md"])])
    importar_url(c, "lib1", "T", "https://e.org/a")
    assert s.llamadas[0][3] == {"title": "T", "url": "https://e.org/a"}
    assert listar_documentos(c, "lib1")[0]["status"] == "Indexed"
    assert formatos_documento(c) == [".md"]
    assert s.llamadas[2][1].endswith("/memories/document-formats")


def test_verificador_coincide_y_no_coincide():
    esperado = ver.normalizar("linea uno  \nlinea dos\n")
    ag = {"name": ver.NOMBRE, "prompt": "linea uno\nlinea dos  \n", "modelDisplayName": "Gemma"}
    v, a, modelo, _ = ver.comparar([ag], esperado)
    assert v == "coincide" and modelo == "Gemma"
    assert ver.comparar([{**ag, "prompt": "otra"}], esperado)[0] == "no coincide"
    assert ver.comparar([], esperado)[0] == "no encontrado"


def test_verificador_main_get_only(capsys):
    esperado = ver.prompt_esperado((ver.RAIZ / "evolus" / "agente_instrucciones.md").read_text(encoding="utf-8"))
    c, s = cliente([Resp(200, [{"name": ver.NOMBRE, "prompt": esperado}])])
    assert ver.main(c) == 0
    assert s.llamadas[0][0] == "GET" and s.llamadas[0][1].endswith("/agents")
