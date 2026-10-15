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


def test_combinar_reintentos_sustituye_solo_invalidos():
    base = [_reg(14, 0, "VERIFICADO", True, True, verif=2), _reg(14, 1, "INVALIDO"), _reg(15, 2, "INVALIDO"),
            _reg(1, 0, "PARCIAL", False, True, verif=1)]
    rei = [_reg(14, 0, "BLOQUEADO", rech=1), _reg(14, 1, "VERIFICADO", False, True, verif=3)]
    comb = da.combinar_reintentos(base, rei)
    assert comb[0] is base[0]                      # no INVALIDO: intacto aunque haya reintento
    assert comb[1] is rei[1]                       # INVALIDO: sustituido
    assert comb[2]["estado"] == "INVALIDO"         # sin reintento: se queda INVALIDO
    assert comb[3] is base[3] and len(comb) == len(base)
    assert base[1]["estado"] == "INVALIDO"         # la entrada no se muta


# ---------- replay en vivo ----------
def test_estado_en_antes_del_inicio():
    e = da.estado_en(-5, [0, 1, 2], 10, 8)
    assert (e["minuto"], e["acumuladas"], e["en_ventana"], e["inundacion"], e["tarjeta"]) == (-15.0, 0, 0, False, False)


def test_estado_en_cuenta_ventana_y_acumuladas():
    ev = [0, 1, 1, 5, 6]
    e = da.estado_en(5, ev, None, None)
    assert e["acumuladas"] == 4 and e["en_ventana"] == 1          # ventana (1, 5]: solo la muestra 5
    e = da.estado_en(4, ev, None, None)
    assert e["acumuladas"] == 3 and e["en_ventana"] == 2          # ventana (0, 4]: las dos de la muestra 1
    assert da.estado_en(6, ev, None, None)["minuto"] == 18.0


def test_estado_en_banderas_conmutan_exactamente():
    assert not da.estado_en(7, [], 10, 8)["inundacion"] and da.estado_en(8, [], 10, 8)["inundacion"]
    assert not da.estado_en(9, [], 10, 8)["tarjeta"] and da.estado_en(10, [], 10, 8)["tarjeta"]


def test_estado_en_sin_tarjeta_ni_inundacion():
    e = da.estado_en(500, [1], None, None)
    assert e["tarjeta"] is False and e["inundacion"] is False


def test_tag_en_vista_con_vista_falsa():
    import numpy as np
    from types import SimpleNamespace as NS
    v = NS(origen=np.array([3, 0, 6]),
           variables=[NS(tag="A", descripcion="dA"), NS(tag="B", descripcion="dB"), NS(tag="C", descripcion="dC")])
    assert da.tag_en_vista(v, 6) == ("C", "dC") and da.tag_en_vista(v, 0) == ("B", "dB")


def test_salida_evolus_y_anticipacion_con_archivos_temporales(tmp_path, monkeypatch):
    carpeta = tmp_path / "ev"
    carpeta.mkdir()
    (carpeta / "resultados.jsonl").write_text(json.dumps({"falla": 6, "nivel": 0, "texto": "x"}) + "\n")
    monkeypatch.setattr(da, "RUNS", tmp_path)
    monkeypatch.setattr(da, "CAMPANA_EVOLUS", "ev")
    assert da.salida_evolus(6, 0)["texto"] == "x"
    assert da.salida_evolus(6, 2) is None and da.salida_evolus(1, 0) is None
    ant = tmp_path / "ant.json"
    ant.write_text(json.dumps({"por_falla": {"1": {"tarjeta_min": 3}}}))
    monkeypatch.setattr(da, "ANTICIPACION", ant)
    assert da.anticipacion(1) == {"tarjeta_min": 3} and da.anticipacion(2) is None
    monkeypatch.setattr(da, "ANTICIPACION", tmp_path / "no.json")
    assert da.anticipacion(1) is None


def test_linea_de_tiempo_coincide_con_anticipacion_json():
    import pytest
    ant = da.leer_json(da.RAIZ / "data" / "processed" / "anticipacion.json").get("por_falla", {})
    if not ant:
        pytest.skip("anticipacion.json no disponible")
    try:
        for f, entry in ant.items():
            lt = da.linea_de_tiempo(int(f), 0, entry["indice_alarma"])
            assert lt["tarjeta_rel"] * 3 == entry["tarjeta_min"]
            inund = lt["inundacion_rel"]
            assert (None if inund is None else inund * 3) == entry["inundacion_min"]
            ms = [e["muestra"] for e in lt["eventos"]]
            assert (min(ms) * 3 if ms else None) == entry["primera_alarma_min"]
    except OSError:
        pytest.skip("datos Braatz locales ausentes")
