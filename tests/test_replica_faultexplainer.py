import json

import pandas as pd
import pytest

from eval import replica_faultexplainer as r

pytestmark = pytest.mark.skipif(not r.disponibles(), reason="faltan los CSV de FaultExplainer (scripts/descargar_faultexplainer.py)")


@pytest.fixture(scope="module")
def modelo():
    return r.ModeloFE()


def test_deteccion_reproduce_paper(modelo):
    no_det = [i for i in range(1, 16) if not r.analizar(modelo, i)["detectada"]]
    assert no_det == [3, 4, 9, 15]


def test_indices_y_top6_coinciden_con_su_csv_precalculado(modelo):
    for i in (1, 7, 13):
        fp = pd.read_csv(r.DATOS / "frontend_public" / f"fault{i}.csv")
        a = r.analizar(modelo, i)
        assert a["indice_alarma"] == r.indice_alarma(fp["anomaly"].values)
        t2 = fp.loc[a["indice_alarma"], [c for c in fp.columns if c.startswith("t2_") and c != "t2_stat"]]
        ref = [c[3:] for c in t2.sort_values(ascending=False).head(6).index]
        assert set(a["top"]) == set(ref)


def test_prompt_contiene_literal_prompts_py(modelo):
    a = r.analizar(modelo, 1)
    msgs = r.construir_mensajes(r.comparacion(modelo, a["df"], a["indice_alarma"], a["top"]))
    assert len(msgs) == 1 and msgs[0]["role"] == "user" and isinstance(msgs[0]["content"], str)
    txt = msgs[0]["content"]
    for frag in ("You are a helpful AI chatbot trained to assist with monitoring the Tennessee Eastman process",
                 "From the list of 16 predefined root causes (provided below), identify the three most likely causes",
                 "15. IDV(15) Condenser Cooling Water Valve & Sticking",
                 "The top feature changes are\nFeature: "):
        assert frag in txt
    assert "  - Faulty Data: Value = " in txt and "  - Percentage Changes: Value Change = " in txt
    assert "Standard Deviation" not in txt.split("The top feature changes")[1]


def test_extraccion_idv():
    e = r.extraer_idv("The most likely causes are IDV(6), IDV(1) and IDV(7). IDV(6) fits best.")
    assert e["extraidos"] == [6, 1, 7] and not e["requiere_revision_alias"]
    assert r.extraer_idv("Causes: IDV 4, IDV-11")["requiere_revision_alias"]
    assert r.extraer_idv("IDV(2), IDV(5), IDV(8), IDV(9)")["requiere_revision_alias"]
    assert r.extraer_idv("IDV(2), IDV(5), IDV(20)")["requiere_revision_alias"]
    p = r.puntuar(6, ["IDV(1), IDV(6), IDV(7)"])
    assert p["acierto_top3"] and not p["acierto_top1"]


def test_corrida_humo_simulado(tmp_path):
    regs = r.correr("humo", "simulado", [1, 3, 6], raiz_runs=tmp_path)
    por = {x["falla"]: x for x in regs}
    assert por[3]["estado"] == "NO_DETECTADO"
    assert por[1]["acierto_top3"] and por[6]["acierto_top3"] and por[1]["muestras"][0]["texto"]
    assert json.loads((tmp_path / "humo" / "manifiesto.json").read_text())["tipo"] == "replica_faultexplainer"
    assert "Fallas detectadas" in r.resumen(regs)
    # --continuar no repite fallas hechas
    assert len(r.correr("humo", "simulado", [1, 6], continuar=True, raiz_runs=tmp_path)) == 3
