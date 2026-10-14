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
