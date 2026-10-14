"""Cuenta los eventos de alarma de proceso entre el inicio de la falla y la tarjeta (primera alarma estadística).

Uso:
    python3 scripts/medir_alarmas.py

Para cada falla con caso LLM en la campaña combinada (original recompuertada + reintentos, estado != NO_DETECTADO),
cuenta los eventos de `core/alarmas` (límites p99,9 de `normal_ampliado`, retardo 2, solo XMEAS) con muestra en
[INICIO_FALLA_TEST, indice_alarma] sobre d{falla}_te: lo que vería el operador hasta que el copiloto emite UNA tarjeta.
Los eventos son invariantes a la vista (el disfraz solo reetiqueta), por eso se cuentan una vez por falla.
Determinista. Guarda data/processed/alarmas_por_falla.json (registrar en SHA256SUMS).
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from core import alarmas, datos  # noqa: E402
from verify_claims import combinar_reintentos, leer_jsonl  # noqa: E402

BASE = RAIZ / "data/runs/tf_gemma31b_k5_v2/recompuertado.jsonl"
REINTENTOS = RAIZ / "data/runs/tf_gemma31b_k5_v2_reintentos/registros.jsonl"
SALIDA = RAIZ / "data/processed/alarmas_por_falla.json"


def contar(lim: alarmas.Limites, falla: int, indice_alarma: int) -> int:
    x = datos.cargar(falla, prueba=True)[datos.INICIO_FALLA_TEST: indice_alarma + 1]
    return len(alarmas.eventos(lim, x))


def main() -> None:
    regs = combinar_reintentos(leer_jsonl(BASE), leer_jsonl(REINTENTOS))
    indices: dict[int, set] = {}
    for r in regs:
        if r["estado"] != "NO_DETECTADO":
            indices.setdefault(r["falla"], set()).add(r["indice_alarma"])
    for f, s in indices.items():
        if len(s) != 1:
            raise SystemExit(f"falla {f}: indice_alarma distinto entre niveles: {sorted(s)}")
    lim = alarmas.ajustar_limites(datos.normal_ampliado())
    por_falla = {str(f): {"indice_alarma": next(iter(s)), "eventos": contar(lim, f, next(iter(s)))}
                 for f, s in sorted(indices.items())}
    salida = {"definicion": "eventos de alarma de proceso con muestra en [160, indice_alarma] de d{falla}_te "
                            "(limites p99.9 de normal_ampliado, retardo 2, solo XMEAS)",
              "fuentes": [str(BASE.relative_to(RAIZ)), str(REINTENTOS.relative_to(RAIZ))],
              "por_falla": por_falla}
    SALIDA.write_text(json.dumps(salida, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{SALIDA.relative_to(RAIZ)}: {len(por_falla)} fallas")
    for f, v in por_falla.items():
        print(f"  falla {f:>2}: alarma {v['indice_alarma']}, {v['eventos']} eventos")


if __name__ == "__main__":
    main()
