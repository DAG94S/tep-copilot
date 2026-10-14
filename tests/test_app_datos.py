"""Pruebas de las funciones puras de app/datos_app.py (sin Streamlit)."""
import json

from app import datos_app as da


def _reg(falla, nivel, estado, top1=False, top3=False, verif=0, rech=0, osc=0):
    return {"falla": falla, "nivel": nivel, "estado": estado, "acierto_top1": top1, "acierto_top3": top3,
            "afirmaciones": verif + rech + osc, "evidencia_verificada": [{}] * verif,
            "evidencia_rechazada": [{}] * rech, "evidencia_oscilante": [{}] * osc}


def test_resumen_por_nivel_excluye_invalidos_y_no_detectados():
    regs = [_reg(1, 0, "VERIFICADO", True, True, verif=4), _reg(2, 0, "PARCIAL", False, True, verif=3, rech=1),
            _reg(3, 0, "NO_DETECTADO"), _reg(4, 0, "INVALIDO"), _reg(1, 1, "BLOQUEADO", rech=2)]
    n0, n1 = da.resumen_por_nivel(regs)
    assert (n0["nivel"], n0["casos"], n0["detectadas"], n0["evaluables"]) == (0, 4, 3, 2)
    assert (n0["top1"], n0["top3"]) == (1, 2)
    assert (n0["afirmaciones"], n0["rechazadas"]) == (8, 1) and n0["tasa_rechazo"] == 1 / 8
    assert n0["estados"]["INVALIDO"] == 1 and n0["estados"]["NO_DETECTADO"] == 1
    assert n1["tasa_rechazo"] == 1.0


def test_tasa_none_sin_afirmaciones():
    assert da.resumen_por_nivel([_reg(1, 0, "NO_DETECTADO")])[0]["tasa_rechazo"] is None


def test_tabla_y_totales_replica():
    regs = [{"falla": 1, "detectada": True, "estado": "RESPONDIDO", "acierto_top3": True, "aciertos_muestras": 5},
            {"falla": 2, "detectada": True, "estado": "RESPONDIDO", "acierto_top3": False, "aciertos_muestras": 1},
            {"falla": 3, "detectada": False, "estado": "NO_DETECTADO"}]
    base = {"A": (1,), "B": (1, 2)}
    filas = da.tabla_replica(regs, base)
    assert filas[2]["gemma"] is None and filas[2]["A"] is None
    assert da.totales_replica(filas, base) == {"detectadas": 2, "Gemma": 1, "A": 1, "B": 2}


def test_archivo_efectivo_prefiere_recompuertado(tmp_path):
    (tmp_path / "registros.jsonl").write_text("")
    assert da.archivo_efectivo(tmp_path).name == "registros.jsonl"
    (tmp_path / "recompuertado.jsonl").write_text("")
    assert da.archivo_efectivo(tmp_path).name == "recompuertado.jsonl"


def test_leer_jsonl_ausente_y_presente(tmp_path):
    assert da.leer_jsonl(tmp_path / "no.jsonl") == []
    p = tmp_path / "a.jsonl"
    p.write_text(json.dumps({"a": 1}) + "\n\n" + json.dumps({"a": 2}) + "\n")
    assert [r["a"] for r in da.leer_jsonl(p)] == [1, 2]


def test_sha256_registrado(tmp_path):
    (tmp_path / "SHA256SUMS").write_text("abc123  data/runs/x/registros.jsonl\ndef456  data/otro.txt\n")
    f = tmp_path / "data" / "runs" / "x" / "registros.jsonl"
    f.parent.mkdir(parents=True)
    f.write_text("")
    assert da.sha256_registrado(f, raiz=tmp_path) == "abc123"
    assert da.sha256_registrado(tmp_path / "data" / "nada.txt", raiz=tmp_path) is None


def test_campanas_reales_coinciden_con_el_registro():
    regs = da.leer_jsonl(da.archivo_efectivo(da.RUNS / da.CAMPANA_PRINCIPAL))
    if not regs:
        return
    assert [f["nivel"] for f in da.resumen_por_nivel(regs)] == [0, 1, 2]
