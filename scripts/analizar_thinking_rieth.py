"""Rieth, mismo despliegue de Gemma (self-dploy, desde el 16-oct): con thinking (`--thinking-plantilla`) vs sin thinking.

Uso:
    .venv/bin/python scripts/analizar_thinking_rieth.py [--con tf_rieth_k5_thinkpl] [--sin tf_rieth_k5_sd]
                                                        [--niveles 0 2] [--json data/processed/rieth_thinking.json]

Lee data/runs/<prefijo>_n<nivel>/registros.jsonl de cada brazo. Por nivel:
- Cobertura: casos (falla, corrida) válidos sobre 100, ERROR_LLM que siguen en registros.jsonl y casos que faltan.
  Si un caso aparece dos veces (reanudación), cuenta el último.
- Estados de la compuerta por brazo.
- Top-1/top-3 sobre casos evaluables (estado distinto de NO_DETECTADO, INVALIDO y ERROR_LLM), primero en cada brazo y
  luego en los casos emparejados por (falla, corrida), evaluables en ambos: discordantes, McNemar exacto y diferencia
  (con menos sin, en puntos porcentuales) con IC95 bootstrap por clusters de falla (`verify_claims.caida_bootstrap`).
- Por falla (las corridas de una falla se parecen: el tamaño efectivo son ~10 fallas, no 100 casos): aciertos top-3 y
  top-1 en cada brazo, rechazo medio de la compuerta y fallas en que gana cada brazo.
- Rechazo de la compuerta (evidencia rechazada / afirmaciones, casos con al menos una afirmación): media por caso,
  medias por falla, fallas con más / menos / igual rechazo con thinking y Wilcoxon sobre las medias por falla.
- Medianas por caso: reasoning_tokens, completion_tokens y segundos.
Con datos parciales imprime lo que haya y lo dice. No toca nada: solo lee; con --json guarda el resumen (registrar en
SHA256SUMS si se usa como fuente de un claim).
"""
import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_claims import EXCLUIDOS, RAIZ, caida_bootstrap, leer_jsonl  # noqa: E402

FALLAS = (1, 2, 5, 6, 7, 8, 10, 12, 13, 14)
CORRIDAS = range(1, 11)


def cargar(campana: str) -> tuple[dict, int] | None:
    """({(falla, corrida): registro} sin ERROR_LLM, ERROR_LLM que quedan en registros.jsonl); None si no existe."""
    ruta = RAIZ / "data" / "runs" / campana / "registros.jsonl"
    if not ruta.exists():
        return None
    regs = leer_jsonl(ruta)
    casos = {(r["falla"], r["corrida"]): r for r in regs if r["estado"] != "ERROR_LLM"}  # el último gana
    return casos, sum(r["estado"] == "ERROR_LLM" for r in regs)


def _evaluable(r: dict) -> bool:
    return r["estado"] not in EXCLUIDOS


def _rechazo(r: dict) -> float | None:
    return len(r.get("evidencia_rechazada", [])) / r["afirmaciones"] if r.get("afirmaciones") else None


def _med(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return float(statistics.median(xs)) if xs else None


def _media(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


def _pct(x) -> str:
    return "—" if x is None else f"{x:.0%}"


def resumen_brazo(casos: dict, errores: int) -> dict:
    ev = [r for r in casos.values() if _evaluable(r)]
    return {
        "validos": len(casos),
        "error_llm_en_registros": errores,
        "faltan": [list(k) for k in sorted({(f, c) for f in FALLAS for c in CORRIDAS} - casos.keys())],
        "estados": dict(Counter(r["estado"] for r in casos.values())),
        "evaluables": len(ev),
        "top1": sum(bool(r["acierto_top1"]) for r in ev),
        "top3": sum(bool(r["acierto_top3"]) for r in ev),
        "rechazo_medio": _media(_rechazo(r) for r in ev),
        "mediana_reasoning_tokens": _med(r["uso"].get("reasoning_tokens") for r in casos.values()),
        "mediana_completion_tokens": _med(r["uso"].get("completion_tokens") for r in casos.values()),
        "mediana_segundos": _med(r["segundos"] for r in casos.values()),
        "parametros": sorted({json.dumps(r["parametros"], sort_keys=True) for r in casos.values()}),
    }


def _discordantes(par) -> tuple[int, int]:
    """(solo acierta con thinking, solo acierta sin)."""
    return sum(x and not y for _, x, y in par), sum(y and not x for _, x, y in par)


def comparar(con: dict, sin: dict) -> dict:
    """Casos emparejados por (falla, corrida), evaluables en ambos brazos."""
    from scipy.stats import binomtest, wilcoxon  # perezoso
    ks = sorted(k for k in con.keys() & sin.keys() if _evaluable(con[k]) and _evaluable(sin[k]))
    out = {"emparejados": len(ks), "fallas_emparejadas": len({f for f, _ in ks})}
    for clave in ("acierto_top1", "acierto_top3"):
        par = [(k[0], bool(con[k][clave]), bool(sin[k][clave])) for k in ks]
        d_con, d_sin = _discordantes(par)
        dif, lo, hi = caida_bootstrap(par) if par else (None, None, None)
        out[clave] = {
            "con": sum(x for _, x, _ in par), "sin": sum(y for _, _, y in par),
            "solo_con": d_con, "solo_sin": d_sin,
            "mcnemar_p": binomtest(d_con, d_con + d_sin, 0.5).pvalue if d_con + d_sin else 1.0,
            "diferencia_pp": dif, "ic95_pp": [lo, hi],
        }
    # por falla
    filas = []
    for f in sorted({f for f, _ in ks}):
        kf = [k for k in ks if k[0] == f]
        filas.append({
            "falla": f, "n": len(kf),
            "top3_con": sum(bool(con[k]["acierto_top3"]) for k in kf),
            "top3_sin": sum(bool(sin[k]["acierto_top3"]) for k in kf),
            "top1_con": sum(bool(con[k]["acierto_top1"]) for k in kf),
            "top1_sin": sum(bool(sin[k]["acierto_top1"]) for k in kf),
            "rechazo_con": _media(_rechazo(con[k]) for k in kf),
            "rechazo_sin": _media(_rechazo(sin[k]) for k in kf),
        })
    out["por_falla"] = filas
    for clave in ("top3", "top1"):
        out[f"fallas_{clave}_gana_con_sin_empate"] = [
            sum(r[f"{clave}_con"] > r[f"{clave}_sin"] for r in filas),
            sum(r[f"{clave}_con"] < r[f"{clave}_sin"] for r in filas),
            sum(r[f"{clave}_con"] == r[f"{clave}_sin"] for r in filas)]
    # rechazo: medias por falla (clusters), solo fallas con rechazo definido en ambos brazos
    rf = [(r["rechazo_con"], r["rechazo_sin"]) for r in filas if None not in (r["rechazo_con"], r["rechazo_sin"])]
    out["fallas_rechazo_mayor_menor_igual_con"] = [sum(x > y for x, y in rf), sum(x < y for x, y in rf),
                                                   sum(x == y for x, y in rf)]
    difs = [x - y for x, y in rf if x != y]
    out["rechazo_fallas_wilcoxon_p"] = wilcoxon([x for x, _ in rf], [y for _, y in rf]).pvalue if len(difs) >= 1 else None
    rk = [(_rechazo(con[k]), _rechazo(sin[k])) for k in ks]
    rk = [(x, y) for x, y in rk if x is not None and y is not None]
    out["rechazo_medio_casos_con_sin"] = [_media(x for x, _ in rk), _media(y for _, y in rk)]
    return out


def imprimir_brazo(nombre: str, campana: str, b: dict) -> None:
    print(f"  {nombre:4} {campana}: {b['validos']}/100 válidos, {b['error_llm_en_registros']} ERROR_LLM en registros,"
          f" faltan {len(b['faltan'])}")
    print(f"       estados {b['estados']}")
    print(f"       top-1 {b['top1']}/{b['evaluables']}, top-3 {b['top3']}/{b['evaluables']},"
          f" rechazo medio {_pct(b['rechazo_medio'])}")
    m = {k: "—" if b[f"mediana_{k}"] is None else f"{b[f'mediana_{k}']:.0f}"
         for k in ("reasoning_tokens", "completion_tokens", "segundos")}
    print(f"       medianas por caso: reasoning {m['reasoning_tokens']}, completion {m['completion_tokens']},"
          f" segundos {m['segundos']}")
    if len(b["parametros"]) > 1:
        print(f"       AVISO: {len(b['parametros'])} juegos de parámetros distintos")


def imprimir_comparacion(c: dict) -> None:
    print(f"  emparejados: {c['emparejados']} casos en {c['fallas_emparejadas']} fallas")
    for clave, et in (("acierto_top3", "top-3"), ("acierto_top1", "top-1")):
        x = c[clave]
        dif = "—" if x["diferencia_pp"] is None else \
            f"{x['diferencia_pp']:+.0f} pp [{x['ic95_pp'][0]:+.0f}, {x['ic95_pp'][1]:+.0f}]"
        print(f"  {et}: con {x['con']} / sin {x['sin']}; solo con {x['solo_con']} vs solo sin {x['solo_sin']}"
              f" (McNemar p={x['mcnemar_p']:.2f}); diferencia {dif} (IC95 bootstrap por falla)")
    g3, g1 = c["fallas_top3_gana_con_sin_empate"], c["fallas_top1_gana_con_sin_empate"]
    print(f"  fallas en que gana con / sin / empate: top-3 {g3[0]}/{g3[1]}/{g3[2]}, top-1 {g1[0]}/{g1[1]}/{g1[2]}")
    rm = c["rechazo_medio_casos_con_sin"]
    rr = c["fallas_rechazo_mayor_menor_igual_con"]
    p = c["rechazo_fallas_wilcoxon_p"]
    print(f"  rechazo medio (casos emparejados) con {_pct(rm[0])} / sin {_pct(rm[1])};"
          f" fallas con más / menos / igual rechazo con thinking: {rr[0]}/{rr[1]}/{rr[2]}"
          f" (Wilcoxon sobre medias por falla p={'—' if p is None else f'{p:.2g}'})")
    print("  | falla | n | top-3 con | top-3 sin | top-1 con | top-1 sin | rechazo con | rechazo sin |")
    print("  |---|---|---|---|---|---|---|---|")
    for r in c["por_falla"]:
        print(f"  | {r['falla']} | {r['n']} | {r['top3_con']} | {r['top3_sin']} | {r['top1_con']} | {r['top1_sin']} |"
              f" {_pct(r['rechazo_con'])} | {_pct(r['rechazo_sin'])} |")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--con", default="tf_rieth_k5_thinkpl", help="prefijo de campaña con thinking")
    p.add_argument("--sin", default="tf_rieth_k5_sd", help="prefijo de campaña sin thinking")
    p.add_argument("--niveles", type=int, nargs="+", default=[0, 2])
    p.add_argument("--json", type=Path, default=None, help="guarda el resumen en este archivo")
    a = p.parse_args()

    salida = {"con": a.con, "sin": a.sin, "niveles": {}}
    completo = True
    for n in a.niveles:
        camp_con, camp_sin = f"{a.con}_n{n}", f"{a.sin}_n{n}"
        dc, ds = cargar(camp_con), cargar(camp_sin)
        print(f"\n## Nivel {n}")
        nivel = {}
        for nombre, camp, d in (("con", camp_con, dc), ("sin", camp_sin, ds)):
            if d is None:
                print(f"  {nombre:4} {camp}: no existe todavía")
                completo = False
                continue
            nivel[nombre] = resumen_brazo(*d)
            imprimir_brazo(nombre, camp, nivel[nombre])
            completo &= nivel[nombre]["validos"] == 100 and nivel[nombre]["error_llm_en_registros"] == 0
        if dc and ds:
            nivel["comparacion"] = comparar(dc[0], ds[0])
            imprimir_comparacion(nivel["comparacion"])
        salida["niveles"][n] = nivel
    salida["completo"] = completo
    if not completo:
        print("\nDATOS PARCIALES: no usar como fuente de un claim.")
    if a.json:
        a.json.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nresumen en {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
