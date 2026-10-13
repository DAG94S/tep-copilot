"""Pruebas de la tubería de evaluación con el backend simulado (requieren data/raw/braatz)."""
import json

import pytest

from core import datos
from eval import correr, pipeline

pytestmark = pytest.mark.skipif(
    not (datos.BRAATZ / "d00.dat").exists(), reason="faltan datos: python3 scripts/descargar_datos.py"
)


def _campana(tmp_path, **kw):
    return correr.correr("t", "simulado", [1], [0, 1, 2], raiz_runs=tmp_path, **kw)


def test_simulado_de_punta_a_punta(tmp_path):
    regs = _campana(tmp_path)
    assert len(regs) == 3
    for r in regs:
        for clave in ("falla", "nivel", "estado", "indice_alarma", "columnas_tep_top", "sha256_mensajes", "parametros"):
            assert clave in r
    assert (tmp_path / "t" / "manifiesto.json").exists()
    objetos = [json.loads((tmp_path / "t" / "manifiesto.json").read_text())]
    objetos += [json.loads(l) for l in (tmp_path / "t" / "registros.jsonl").read_text().splitlines()]

    def revisar(o):
        if isinstance(o, dict):
            for k, v in o.items():
                assert not ("api" in k.lower() and v), k
                revisar(v)
        elif isinstance(o, list):
            for v in o:
                revisar(v)
    for o in objetos:
        revisar(o)


def test_invariancia_entre_niveles():
    casos = [pipeline.preparar_caso(1, n) for n in (0, 1, 2)]
    assert all(c.detectado for c in casos)
    assert len({c.indice_alarma for c in casos}) == 1
    assert len({tuple(c.columnas_tep_top) for c in casos}) == 1


def test_eco_pasa_la_compuerta():
    caso = pipeline.preparar_caso(1, 0)
    reg = pipeline.diagnosticar(caso, pipeline.ClienteEco(caso))
    assert reg["estado"] in ("VERIFICADO", "PARCIAL")


def test_continuar_no_duplica(tmp_path):
    _campana(tmp_path)
    with pytest.raises(SystemExit):
        _campana(tmp_path)
    regs = _campana(tmp_path, continuar=True)
    assert len(regs) == 3


def test_fusionar_system():
    base = pipeline.preparar_caso(1, 1)
    fus = pipeline.preparar_caso(1, 1, fusionar_system=True)
    assert [m["role"] for m in fus.mensajes] == ["user"]
    assert fus.mensajes[0]["content"].startswith(base.mensajes[0]["content"])
