"""recompuertar: relee textos guardados y re-aplica la compuerta sin LLM (caso sintético, sin datos TEP)."""
import json
from types import SimpleNamespace

import numpy as np

from eval import pipeline, recompuertar


def test_recompuertar_acepta_oscilacion(tmp_path, monkeypatch):
    texto = json.dumps({"causes": ["C10"], "evidence": [{"tag": "TI-1", "direction": "up"},
                                                         {"tag": "FI-3", "direction": "up"}],
                        "explanation": "Temperature rose."})
    reg = {"falla": 14, "nivel": 0, "calibracion": "d00", "estadistico": "t2", "estado": "PARCIAL",
           "textos": [texto], "afirmaciones": 2, "evidencia_verificada": [{"tag": "TI-1", "direction": "up"}],
           "evidencia_rechazada": [{"tag": "FI-3", "direction": "up", "motivo": "sin desviación"}]}
    no_det = {"falla": 3, "nivel": 0, "estado": "NO_DETECTADO"}
    camp = tmp_path / "c1"
    camp.mkdir()
    (camp / "registros.jsonl").write_text(json.dumps(reg) + "\n" + json.dumps(no_det) + "\n")
    (camp / "manifiesto.json").write_text(json.dumps({"argumentos": {"fusionar_system": False}}))
    caso = SimpleNamespace(detectado=True, tags=["TI-1", "FI-3"], codigos=["C10"], z=np.array([5.0, 0.5]),
                           z_rms=np.array([5.0, 4.5]), vista=SimpleNamespace(idv={"C10": 14}))
    monkeypatch.setattr(pipeline, "preparar_caso", lambda *a, **k: caso)
    recompuertar.main(["--campana", "c1", "--raiz", str(tmp_path)])
    sal = [json.loads(l) for l in (camp / "recompuertado.jsonl").read_text().splitlines()]
    assert sal[0]["estado"] == "VERIFICADO" and sal[0]["evidencia_rechazada"] == []
    assert sal[0]["evidencia_oscilante"][0]["tag"] == "FI-3" and sal[0]["acierto_top1"]
    assert sal[1]["estado"] == "NO_DETECTADO"
    assert json.loads((camp / "registros.jsonl").read_text().splitlines()[0])["estado"] == "PARCIAL"
