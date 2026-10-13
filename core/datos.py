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
