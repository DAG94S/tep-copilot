"""Evaluación sobre las simulaciones independientes de Rieth (requieren data/processed/rieth y Braatz)."""
import json
import shutil

import pytest

from core import datos
from eval import correr, pipeline

pytestmark = pytest.mark.skipif(
    not (datos.RIETH / "faultfree_train.npz").exists() or not any(datos.RIETH.glob("*.npz"))
    or not (datos.BRAATZ / "d00.dat").exists(),
    reason="faltan datos: Rieth (scripts/convertir_rieth.py) o Braatz",
)


def test_preparar_caso_rieth_detecta_idv1():
    caso = pipeline.preparar_caso(1, 0, corrida=1)
    assert caso.detectado and caso.fuente == "rieth" and caso.corrida == 1
    assert caso.indice_alarma >= datos.INICIO_FALLA_RIETH_TRAIN
    reg = pipeline.diagnosticar(caso, pipeline.ClienteEco(caso))
    assert reg["fuente"] == "rieth" and reg["corrida"] == 1


def test_registro_braatz_sin_campos_nuevos():
    caso = pipeline.preparar_caso(1, 0)
    assert caso.fuente == "braatz" and caso.corrida is None
    reg = pipeline.diagnosticar(caso, pipeline.ClienteEco(caso))
    assert "fuente" not in reg and "corrida" not in reg


def test_cli_rieth_simulado_y_continuar():
    campana = "pytest_rieth_unico"
    carpeta = correr.RAIZ_RUNS.parent / "dev" / campana
    shutil.rmtree(carpeta, ignore_errors=True)
    args = ["--campana", campana, "--backend", "simulado", "--fuente", "rieth", "--fallas", "1,6",
            "--corridas", "1-2", "--niveles", "0,2", "--dev"]
    try:
        correr.main(args)
        regs = [json.loads(l) for l in (carpeta / "registros.jsonl").read_text().splitlines()]
        assert len(regs) == 8
        assert [(r["falla"], r["corrida"], r["nivel"]) for r in regs[:4]] == [(1, 1, 0), (1, 1, 2), (1, 2, 0), (1, 2, 2)]
        assert len({(r["falla"], r["corrida"], r["nivel"]) for r in regs}) == 8
        correr.main(args + ["--continuar"])
        assert len((carpeta / "registros.jsonl").read_text().splitlines()) == 8
        man = json.loads((carpeta / "manifiesto.json").read_text())
        assert man["argumentos"]["fuente"] == "rieth" and man["argumentos"]["corridas"] == "1-2"
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
