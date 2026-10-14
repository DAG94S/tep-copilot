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
