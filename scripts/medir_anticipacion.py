"""Anticipación de la tarjeta frente a la inundación de alarmas (nivel 0, una simulación por falla de Braatz).

Uso:
    python3 scripts/medir_anticipacion.py

Para cada falla con caso LLM en la campaña combinada (original recompuertada + reintentos, regla INVALIDO -> reintento,
sin NO_DETECTADO), con los eventos de `core/alarmas` (límites p99,9 de `normal_ampliado`, retardo 2, solo XMEAS) sobre
x = d{falla}_te[INICIO_FALLA_TEST:] (muestra 0 = inicio de la falla, 3 min por muestra):
- tarjeta_min: (indice_alarma - INICIO_FALLA_TEST) * 3.
- primera_alarma_min: minuto del primer evento (None si no hay).
- inundacion_min: primer instante t (muestras, x3 min) con >= 10 eventos con muestra en [t, t+4). Aproximación del criterio
  EEMUA de 10 alarmas en 10 min: la ventana de 4 muestras son 12 min (la rejilla es de 3 min), es decir, ligeramente laxa.
- alarmas_2h_tras_tarjeta: eventos con muestra en (tarjeta, tarjeta + 40] (40 muestras = 2 h).
Las alarmas son las de NUESTRO sistema de límites estadísticos sobre TEP, no la configuración de alarmas de una planta real.
Determinista. Guarda data/processed/anticipacion.json (registrar en SHA256SUMS).
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
SALIDA = RAIZ / "data/processed/anticipacion.json"

UMBRAL_INUNDACION = 10   # eventos
VENTANA_MUESTRAS = 4     # 12 min
HORIZONTE_MUESTRAS = 40  # 2 h
MIN_POR_MUESTRA = alarmas.MINUTOS_POR_MUESTRA


def inundacion(muestras: list[int]) -> int | None:
    """Primer t (muestras) con >= UMBRAL eventos con muestra en [t, t+VENTANA); None si nunca."""
    if not muestras:
        return None
    for t in range(0, max(muestras) + 1):
        if sum(t <= m < t + VENTANA_MUESTRAS for m in muestras) >= UMBRAL_INUNDACION:
            return t
    return None


def medir_falla(lim: alarmas.Limites, falla: int, indice_alarma: int) -> dict:
    x = datos.cargar(falla, prueba=True)[datos.INICIO_FALLA_TEST:]
    muestras = [e.muestra for e in alarmas.eventos(lim, x)]
    tarjeta = indice_alarma - datos.INICIO_FALLA_TEST
    t_inund = inundacion(muestras)
    return {"indice_alarma": indice_alarma,
            "tarjeta_min": tarjeta * MIN_POR_MUESTRA,
            "primera_alarma_min": min(muestras) * MIN_POR_MUESTRA if muestras else None,
            "inundacion_min": None if t_inund is None else t_inund * MIN_POR_MUESTRA,
            "alarmas_2h_tras_tarjeta": sum(tarjeta < m <= tarjeta + HORIZONTE_MUESTRAS for m in muestras)}


def main() -> None:
    regs = combinar_reintentos(leer_jsonl(BASE), leer_jsonl(REINTENTOS))
    indices: dict[int, set] = {}
    for r in regs:
        if r["nivel"] == 0 and r["estado"] != "NO_DETECTADO":
            indices.setdefault(r["falla"], set()).add(r["indice_alarma"])
    for f, s in indices.items():
        if len(s) != 1:
            raise SystemExit(f"falla {f}: indice_alarma ambiguo: {sorted(s)}")
    lim = alarmas.ajustar_limites(datos.normal_ampliado())
    por_falla = {str(f): medir_falla(lim, f, next(iter(s))) for f, s in sorted(indices.items())}
    salida = {"definicion": "anticipacion de la tarjeta frente a las alarmas de proceso (limites estadisticos p99.9 sobre TEP, "
                            "retardo 2, solo XMEAS; no es la configuracion de alarmas de una planta real); nivel 0, "
                            "una simulacion por falla (Braatz); minutos desde el inicio de la falla",
              "parametros": {"umbral_inundacion_eventos": UMBRAL_INUNDACION, "ventana_inundacion_muestras": VENTANA_MUESTRAS,
                             "horizonte_muestras": HORIZONTE_MUESTRAS, "minutos_por_muestra": MIN_POR_MUESTRA,
                             "inicio_falla": datos.INICIO_FALLA_TEST, "percentil_limites": 99.9, "retardo": 2},
              "fuentes": [str(BASE.relative_to(RAIZ)), str(REINTENTOS.relative_to(RAIZ))],
              "por_falla": por_falla}
    SALIDA.write_text(json.dumps(salida, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{SALIDA.relative_to(RAIZ)}: {len(por_falla)} fallas")
    for f, v in por_falla.items():
        print(f"  falla {f:>2}: {v}")


if __name__ == "__main__":
    main()
