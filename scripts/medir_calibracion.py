"""Mide cómo cambia la calibración (d00 vs normal ampliado) en falsas alarmas y detección.

Uso:
    python3 scripts/medir_calibracion.py

Compara dos calibraciones: `d00` (500 muestras) y `ampliado` (920: d00 + tramos previos a la falla
de d01..d21 de ENTRENAMIENTO; nunca *_te). Para cada una ajusta PCA (90%, α=0,01) y límites de
alarma (percentil 99,9, retardo 2), y mide en d00_te (normal) y en las fallas 1..21 de *_te.
Adicional: variante con el percentil 99 empírico del SPE de calibración en lugar de Jackson-Mudholkar.
Guarda data/processed/calibracion.json (con los SHA-256 de los .dat usados, de SHA256SUMS).
"""
import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from core import alarmas, datos, pca_t2  # noqa: E402

SALIDA = RAIZ / "data" / "processed" / "calibracion.json"
FALLAS = range(1, 22)


def _sha() -> dict:
    d = {}
    for linea in (RAIZ / "SHA256SUMS").read_text().splitlines():
        h, _, ruta = linea.partition("  ")
        d[ruta.strip()] = h
    return d


def _deteccion(modelo, lim_spe: float, x: np.ndarray, t2_lim: float) -> dict:
    """Primera alarma (6 consecutivas) por T² y SPE con límites explícitos."""
    q = pca_t2.spe(modelo, x)
    t = pca_t2.t2(modelo, x)

    def primera(sobre):
        racha = 0
        for i, f in enumerate(sobre):
            racha = racha + 1 if f else 0
            if racha >= pca_t2.CONSECUTIVAS:
                return i
        return None
    return {"t2": primera(t > t2_lim), "spe": primera(q > lim_spe),
            "cualquiera": primera((t > t2_lim) | (q > lim_spe))}


def evaluar(normal: np.ndarray, spe_empirico: bool = False) -> dict:
    modelo = pca_t2.ajustar(normal)
    lim_spe = modelo.limite_spe
    if spe_empirico:
        lim_spe = float(np.percentile(pca_t2.spe(modelo, normal), 99))
    lim_alarma = alarmas.ajustar_limites(normal, 99.9)
    x0 = datos.cargar(0, prueba=True)
    ev = alarmas.eventos(lim_alarma, x0, retardo=2)
    normal_te = {
        "frac_t2_sobre_limite": float(np.mean(pca_t2.t2(modelo, x0) > modelo.limite_t2)),
        "frac_spe_sobre_limite": float(np.mean(pca_t2.spe(modelo, x0) > lim_spe)),
        "primera_alarma": _deteccion(modelo, lim_spe, x0, modelo.limite_t2),
        "eventos_alarma": len(ev),
        "tasa_max_10min": alarmas.tasa_por_ventana(ev, 10.0),
    }
    fallas = {}
    for f in FALLAS:
        d = _deteccion(modelo, lim_spe, datos.cargar(f, prueba=True), modelo.limite_t2)
        fallas[str(f)] = {}
        for k in ("t2", "spe"):
            i = d[k]
            ok = i is not None and i >= datos.INICIO_FALLA_TEST
            fallas[str(f)][k] = {"primera_alarma": i, "detectada": bool(ok),
                                 "retraso_muestras": int(i - datos.INICIO_FALLA_TEST) if ok else None}
    return {"n_calibracion": int(normal.shape[0]), "componentes_A": modelo.componentes,
            "limite_t2": modelo.limite_t2, "limite_spe": lim_spe,
            "limite_spe_tipo": "percentil 99 empirico" if spe_empirico else "Jackson-Mudholkar",
            "normal_te": normal_te, "fallas": fallas}


def imprimir(nombre: str, r: dict) -> None:
    n = r["normal_te"]
    print(f"\n=== {nombre} (n={r['n_calibracion']}, SPE: {r['limite_spe_tipo']}) ===")
    print(f"A={r['componentes_A']}  limite T2={r['limite_t2']:.2f}  limite SPE={r['limite_spe']:.2f}")
    print(f"d00_te: T2>lim {n['frac_t2_sobre_limite']:.1%} | SPE>lim {n['frac_spe_sobre_limite']:.1%} | "
          f"primera_alarma {n['primera_alarma']} | eventos {n['eventos_alarma']} | tasa max 10 min {n['tasa_max_10min']}")
    det_t = [f for f, v in r["fallas"].items() if v["t2"]["detectada"]]
    det_s = [f for f, v in r["fallas"].items() if v["spe"]["detectada"]]
    print(f"Detectadas T2 ({len(det_t)}/21): {', '.join(det_t)}")
    print(f"Detectadas SPE ({len(det_s)}/21): {', '.join(det_s)}")
    print("falla  T2(ret)  SPE(ret)")
    for f, v in r["fallas"].items():
        fmt = lambda e: "no" if not e["detectada"] else str(e["retraso_muestras"])  # noqa: E731
        print(f"{f:>5}  {fmt(v['t2']):>7}  {fmt(v['spe']):>8}")


def main() -> None:
    sumas = _sha()
    usados = {}
    for f in range(0, 22):
        ruta = f"data/raw/braatz/d{f:02d}.dat"
        usados[ruta] = sumas.get(ruta)
    usados["data/raw/braatz/d00_te.dat"] = sumas.get("data/raw/braatz/d00_te.dat")
    for f in FALLAS:
        r = f"data/raw/braatz/d{f:02d}_te.dat"
        usados[r] = sumas.get(r)
    normal_d00, ampliado = datos.cargar(0), datos.normal_ampliado()
    res = {"d00": evaluar(normal_d00), "ampliado": evaluar(ampliado),
           "ampliado_spe_empirico_p99": evaluar(ampliado, spe_empirico=True),
           "d00_spe_empirico_p99": evaluar(normal_d00, spe_empirico=True)}
    for k, v in res.items():
        imprimir(k, v)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps({"calibraciones": res, "sha256_archivos_usados": usados},
                                 indent=2, ensure_ascii=False))
    print(f"\nGuardado: {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
