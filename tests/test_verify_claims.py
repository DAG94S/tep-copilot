"""Pruebas de scripts/verify_claims.py: campo opcional `reintentos` de claims.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import verify_claims as vc  # noqa: E402


def _reg(falla, nivel, estado, top1=False, top3=False):
    return {"falla": falla, "nivel": nivel, "estado": estado, "acierto_top1": top1, "acierto_top3": top3,
            "afirmaciones": 2, "evidencia_rechazada": []}


def _escribir(ruta, regs):
    ruta.write_text("\n".join(json.dumps(r) for r in regs) + "\n", encoding="utf-8")


def _claims(tmp_path, valor, con_reintentos=True):
    c = {"id": "combinado_n0_top1", "valor": valor, "fuente": "base.jsonl", "descripcion": "x"}
    if con_reintentos:
        c["reintentos"] = "rei.jsonl"
    ruta = tmp_path / "claims.json"
    ruta.write_text(json.dumps([c]), encoding="utf-8")
    return ruta


def test_reintentos_sustituyen_invalidos(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_reg(1, 0, "VERIFICADO", True, True), _reg(2, 0, "INVALIDO")])
    _escribir(tmp_path / "rei.jsonl", [_reg(1, 0, "BLOQUEADO"), _reg(2, 0, "VERIFICADO", True, True)])
    res = vc.verificar_afirmaciones(tmp_path, _claims(tmp_path, "2/2"))
    assert res == [("combinado_n0_top1", "OK", "2/2", "2/2")]


def test_sin_campo_reintentos_no_combina(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_reg(1, 0, "VERIFICADO", True, True), _reg(2, 0, "INVALIDO")])
    res = vc.verificar_afirmaciones(tmp_path, _claims(tmp_path, "1/1", con_reintentos=False))
    assert res[0][1] == "OK"


def test_reintentos_ausentes_falla(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_reg(1, 0, "VERIFICADO", True, True)])
    res = vc.verificar_afirmaciones(tmp_path, _claims(tmp_path, "1/1"))
    assert res[0][1] == "FALLA" and "reintentos ausentes" in res[0][3]


def test_readme_marcadores(tmp_path):
    claims = tmp_path / "claims.json"
    claims.write_text(json.dumps([{"id": "a", "valor": "3/12", "fuente": "x", "descripcion": "x"}]), encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("ok <!--claim:a-->3/12<!--/claim--> mal <!--claim:a-->4/12<!--/claim--> "
                      "falta <!--claim:zzz-->1<!--/claim-->", encoding="utf-8")
    res = vc.verificar_readme(readme, claims)
    assert [(i, e) for i, e, _, _ in res] == [("a", "OK"), ("a", "FALLA"), ("zzz", "FALLA")]


# ---------- métricas operativas (latencia, tokens, coste, alarmas) ----------

def _caso(falla, estado, seg=None, pt=1000, ct=100, idx=170):
    r = {"falla": falla, "nivel": 0, "estado": estado, "indice_alarma": idx}
    if estado != "NO_DETECTADO":
        r.update(segundos=seg, uso={"prompt_tokens": pt, "completion_tokens": ct})
    return r


def _un_claim(tmp_path, id_, valor, **extra):
    ruta = tmp_path / "claims.json"
    ruta.write_text(json.dumps([{"id": id_, "valor": valor, "fuente": "base.jsonl", "descripcion": "x", **extra}]),
                    encoding="utf-8")
    return ruta


def test_latencia_y_tokens_ignoran_no_detectado(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_caso(1, "VERIFICADO", 10), _caso(2, "PARCIAL", 20), _caso(3, "PARCIAL", 30),
                                        _caso(4, "NO_DETECTADO")])
    assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "latencia_p50_s", "20 s"))[0][1] == "OK"
    assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "latencia_p95_s", "29 s"))[0][1] == "OK"
    assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "tokens_por_caso_mediana", "1100"))[0][1] == "OK"


def test_evolus_latencia_max(tmp_path):
    _escribir(tmp_path / "base.jsonl", [{"segundos": 7.25}, {"segundos": 29.6}])
    assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "evolus_latencia_max_s", "30 s"))[0][1] == "OK"


def test_coste_usa_auxiliar(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_caso(1, "VERIFICADO", 10, pt=1000, ct=100)])
    uso = {"by_model": [{"model": "Gemma-4-31B-IT", "prompt_tokens": 1000, "completion_tokens": 100,
                         "input_cost": 0.001, "cached_input_cost": 0.0, "output_cost": 0.002}]}
    (tmp_path / "uso.json").write_text(json.dumps(uso), encoding="utf-8")
    res = vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "coste_por_incidente", "$0.00300", auxiliar="uso.json"))
    assert res[0][1:] == ("OK", "$0.00300", "$0.00300")


def test_auxiliar_ausente_o_no_declarado_falla(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_caso(1, "VERIFICADO", 10)])
    res = vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "coste_por_incidente", "$0", auxiliar="no_existe.json"))
    assert res[0][1] == "FALLA" and "auxiliar ausente" in res[0][3]
    res = vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "coste_por_incidente", "$0"))
    assert res[0][1] == "FALLA" and "requiere `auxiliar`" in res[0][3]


def test_alarmas_por_tarjeta_mediana(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_caso(1, "VERIFICADO", 1), _caso(2, "PARCIAL", 1), _caso(3, "NO_DETECTADO", idx=900)])
    aux = {"por_falla": {"1": {"indice_alarma": 170, "eventos": 2}, "2": {"indice_alarma": 170, "eventos": 5},
                         "3": {"indice_alarma": 900, "eventos": 99}}}
    (tmp_path / "al.json").write_text(json.dumps(aux), encoding="utf-8")
    res = vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "alarmas_por_tarjeta_mediana", "3.5", auxiliar="al.json"))
    assert res[0][1] == "OK"
    aux["por_falla"]["2"]["indice_alarma"] = 171      # índice distinto: el auxiliar no corresponde a la fuente
    (tmp_path / "al.json").write_text(json.dumps(aux), encoding="utf-8")
    res = vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "alarmas_por_tarjeta_mediana", "3.5", auxiliar="al.json"))
    assert res[0][1] == "FALLA"


def test_anticipacion(tmp_path):
    _escribir(tmp_path / "base.jsonl", [_caso(1, "VERIFICADO", 1), _caso(2, "PARCIAL", 1), _caso(3, "VERIFICADO", 1),
                                        _caso(4, "NO_DETECTADO", idx=900)])
    fila = lambda t, p, i, n: {"indice_alarma": 170, "tarjeta_min": t, "primera_alarma_min": p, "inundacion_min": i,
                               "alarmas_2h_tras_tarjeta": n}
    aux = {"por_falla": {"1": fila(30, 45, 40, 7), "2": fila(30, 3, None, 12), "3": fila(30, 30, 1000, 4),
                         "4": fila(0, 0, 5, 99)}}
    (tmp_path / "an.json").write_text(json.dumps(aux), encoding="utf-8")
    esperado = {"anticipacion_inundaciones": "2/2", "anticipacion_minutos": "10, 970",
                "tarjeta_antes_primera_alarma": "1", "alarmas_2h_tras_tarjeta_max": "12"}
    for id_, v in esperado.items():
        assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, id_, v, auxiliar="an.json"))[0][1] == "OK", id_
    aux["por_falla"]["3"]["indice_alarma"] = 171      # el auxiliar no corresponde a la campaña
    (tmp_path / "an.json").write_text(json.dumps(aux), encoding="utf-8")
    assert vc.verificar_afirmaciones(tmp_path, _un_claim(tmp_path, "anticipacion_minutos", "10, 970", auxiliar="an.json"))[0][1] == "FALLA"


# ---------- fuente-lista, pareado/McNemar y bootstrap por clusters ----------

def _rieth(falla, corrida, nivel, top3, estado="VERIFICADO"):
    return {"falla": falla, "corrida": corrida, "nivel": nivel, "estado": estado,
            "acierto_top1": False, "acierto_top3": top3}


def test_fuente_lista_concatena_y_falla_si_falta(tmp_path):
    _escribir(tmp_path / "a.jsonl", [_reg(1, 0, "VERIFICADO", True, True)])
    _escribir(tmp_path / "b.jsonl", [_reg(2, 0, "VERIFICADO", False, True), _reg(3, 0, "VERIFICADO", False, False)])
    c = {"id": "campana_v2_n0_top3", "valor": "2/3", "fuente": ["a.jsonl", "b.jsonl"], "descripcion": "x"}
    ruta = tmp_path / "claims.json"
    ruta.write_text(json.dumps([c]), encoding="utf-8")
    assert vc.verificar_afirmaciones(tmp_path, ruta)[0][1] == "OK"
    c["fuente"] = ["a.jsonl", "falta.jsonl"]
    ruta.write_text(json.dumps([c]), encoding="utf-8")
    res = vc.verificar_afirmaciones(tmp_path, ruta)
    assert res[0][1] == "FALLA" and "falta.jsonl" in res[0][3]


def _pareado_sintetico():
    # 3 fallas x 2 corridas. n0 acierta en 5 de 6; n2 en 2 de 6. Discordantes: 3 (solo n0) vs 0.
    n0 = {(1, 1): 1, (1, 2): 1, (2, 1): 1, (2, 2): 1, (3, 1): 1, (3, 2): 0}
    n2 = {(1, 1): 1, (1, 2): 0, (2, 1): 0, (2, 2): 0, (3, 1): 1, (3, 2): 0}
    return ([_rieth(f, c, 0, bool(v)) for (f, c), v in n0.items()] +
            [_rieth(f, c, 2, bool(v)) for (f, c), v in n2.items()])


def test_pareado_y_mcnemar(tmp_path):
    regs = _pareado_sintetico()
    assert vc.METRICAS["rieth_top3_pareado_n0_n2"](regs) == "3 vs 0"
    assert vc.METRICAS["rieth_top3_mcnemar_p_n0_n2"](regs) == "0.25"      # binomial exacta 2*0.5^3
    # un caso no evaluable en n2 sale del emparejamiento
    regs.append(_rieth(4, 1, 0, True))
    regs.append(_rieth(4, 1, 2, False, "ERROR_LLM"))
    assert vc.METRICAS["rieth_top3_pareado_n0_n2"](regs) == "3 vs 0"


def test_bootstrap_por_clusters_determinista():
    par = vc._pareado(_pareado_sintetico(), 0, 2)
    r1, r2 = vc.caida_bootstrap(par), vc.caida_bootstrap(par)
    assert r1 == r2                                   # misma semilla, mismo resultado
    caida, lo, hi = r1
    assert caida == 50.0                              # 3 de 6 casos
    assert lo <= caida <= hi
    assert lo >= 0 and hi <= 100                      # la caída por falla va de 0 a 100 pp
    # sin variación entre fallas, el IC colapsa en el punto
    plano = [(f, True, False) for f in (1, 2, 3) for _ in range(2)]
    assert vc.caida_bootstrap(plano) == (100.0, 100.0, 100.0)
    assert vc.METRICAS["rieth_top3_caida_ic95_n0_n2"](_pareado_sintetico()).startswith("50 pp [")
