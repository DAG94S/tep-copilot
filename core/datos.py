"""Carga de las corridas TEP de Braatz (data/raw/braatz). Siempre devuelve (muestras, 52).

Columnas: XMEAS(1..41) y XMV(1..11). Muestreo cada 3 minutos.
Particularidades del espejo (verificadas el 2026-10-09):
  - d00.dat (normal, entrenamiento) viene TRANSPUESTO: 52 x 500 (500 muestras, no 480 como dice su README).
  - d01..d21.dat tienen 480 muestras; todos los *_te.dat tienen 960.
  - La falla se activa en la muestra 161 de los *_te.dat (índice 160) y en la 21 de los de entrenamiento (índice 20).
"""
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
BRAATZ = RAIZ / "data" / "raw" / "braatz"
N_VARIABLES = 52
INICIO_FALLA_TEST = 160
INICIO_FALLA_TRAIN = 20


def cargar(falla: int, prueba: bool = False) -> np.ndarray:
    """Corrida de la falla `falla` (0 = normal). `prueba=True` usa el archivo *_te (960 muestras)."""
    nombre = f"d{falla:02d}{'_te' if prueba else ''}.dat"
    datos = np.loadtxt(BRAATZ / nombre)
    if datos.shape[0] == N_VARIABLES and datos.shape[1] != N_VARIABLES:
        datos = datos.T
    if datos.shape[1] != N_VARIABLES:
        raise ValueError(f"{nombre}: forma inesperada {datos.shape}")
    return datos


def normal_ampliado() -> np.ndarray:
    """Datos normales ampliados para calibrar: d00.dat (500) + tramo previo a la falla de d01..d21.dat.

    De cada archivo de ENTRENAMIENTO dXX.dat (XX=1..21) se toman las muestras 0..INICIO_FALLA_TRAIN-1
    (20 por archivo, aún sin falla). Total: 500 + 21*20 = 920 muestras x 52 variables.
    No usa ningún *_te.dat: el conjunto de prueba queda intacto.
    """
    tramos = [cargar(0)] + [cargar(f)[:INICIO_FALLA_TRAIN] for f in range(1, 22)]
    return np.vstack(tramos)


# --- Rieth et al. (2017): 20 simulaciones independientes por falla (ENTRENAMIENTO, fallas 1..20) ---
# Mismo orden de columnas que `cargar` (Braatz): XMEAS 1-41 y XMV 1-11 (52). Derivado de data/raw/rieth
# con scripts/extraer_rieth.R + scripts/convertir_rieth.py. La falla entra en la muestra 21 (índice 20).
RIETH = RAIZ / "data" / "processed" / "rieth"
INICIO_FALLA_RIETH_TRAIN = 20


def cargar_rieth(falla: int, corrida: int) -> np.ndarray:
    """Simulación `corrida` (1..20) de la falla `falla` (0 = normal, 1..20) de Rieth: (500, 52) float32."""
    if not 1 <= corrida <= 20:
        raise ValueError(f"corrida fuera de 1..20: {corrida}")
    nombre = "faultfree_train.npz" if falla == 0 else f"faulty_train_f{falla:02d}.npz"
    with np.load(RIETH / nombre) as z:
        return z["x"][list(z["runs"]).index(corrida)]
