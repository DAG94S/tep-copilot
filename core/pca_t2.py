"""Detección de fallas con PCA y estadístico T² (protocolo de FaultExplainer, Khan et al. 2025).

Protocolo replicado: PCA con 90% de varianza acumulada sobre datos normales estandarizados,
límite T² con α=0,01 (distribución F) y alarma tras 6 observaciones consecutivas sobre el límite.
La contribución por variable es la de Kourti & MacGregor (1996) para T².

Extensión nuestra (no parte del protocolo de FaultExplainer): estadístico SPE (Q) sobre el
subespacio residual, con límite de Jackson & Mudholkar (1979) y el mismo α. `primera_alarma`
usa T² por defecto, que es el protocolo replicado.

Este módulo es determinista: no usa ningún LLM.
"""
from dataclasses import dataclass

import numpy as np
from scipy import stats

VARIANZA = 0.90
ALFA = 0.01
CONSECUTIVAS = 6


@dataclass
class ModeloPCA:
    media: np.ndarray
    desv: np.ndarray
    cargas: np.ndarray       # (p, A)
    autovalores: np.ndarray  # (A,)
    limite_t2: float
    n_entrenamiento: int
    autovalores_residuales: np.ndarray  # autovalores de las componentes NO retenidas
    limite_spe: float

    @property
    def componentes(self) -> int:
        return self.cargas.shape[1]


def ajustar(normal: np.ndarray, varianza: float = VARIANZA, alfa: float = ALFA) -> ModeloPCA:
    """Ajusta el PCA con datos de operación normal (n, p)."""
    n = normal.shape[0]
    media = normal.mean(axis=0)
    desv = normal.std(axis=0, ddof=1)
    desv[desv == 0] = 1.0
    z = (normal - media) / desv
    u, s, vt = np.linalg.svd(z, full_matrices=False)
    autoval = s**2 / (n - 1)
    acumulada = np.cumsum(autoval) / autoval.sum()
    a = int(np.searchsorted(acumulada, varianza) + 1)
    limite = a * (n**2 - 1) / (n * (n - a)) * stats.f.ppf(1 - alfa, a, n - a)
    residuales = autoval[a:]
    return ModeloPCA(media, desv, vt[:a].T, autoval[:a], float(limite), n,
                     residuales, _limite_spe(residuales, alfa))


def _limite_spe(residuales: np.ndarray, alfa: float) -> float:
    """Límite Q de Jackson & Mudholkar (1979) a partir de los autovalores residuales."""
    if residuales.size == 0:
        return 0.0
    th1, th2, th3 = (np.sum(residuales**i) for i in (1, 2, 3))
    h0 = 1 - 2 * th1 * th3 / (3 * th2**2)
    c = stats.norm.ppf(1 - alfa)
    base = c * np.sqrt(2 * th2 * h0**2) / th1 + 1 + th2 * h0 * (h0 - 1) / th1**2
    return float(th1 * base ** (1 / h0))


def t2(modelo: ModeloPCA, x: np.ndarray) -> np.ndarray:
    """T² de cada observación (m, p) → (m,)."""
    z = (x - modelo.media) / modelo.desv
    scores = z @ modelo.cargas
    return np.sum(scores**2 / modelo.autovalores, axis=1)


def spe(modelo: ModeloPCA, x: np.ndarray) -> np.ndarray:
    """SPE (Q) de cada observación (m, p) → (m,): ‖z − z·P·Pᵀ‖²."""
    z = (x - modelo.media) / modelo.desv
    resid = z - z @ modelo.cargas @ modelo.cargas.T
    return np.sum(resid**2, axis=1)


def primera_alarma(modelo: ModeloPCA, x: np.ndarray, consecutivas: int = CONSECUTIVAS,
                   estadistico: str = "t2"):
    """Índice de la observación que cumple `consecutivas` alarmas seguidas (None si no hay).

    `estadistico`: "t2" (protocolo FaultExplainer), "spe" o "cualquiera" (T² o SPE sobre su límite).
    """
    if estadistico == "t2":
        sobre = t2(modelo, x) > modelo.limite_t2
    elif estadistico == "spe":
        sobre = spe(modelo, x) > modelo.limite_spe
    elif estadistico == "cualquiera":
        sobre = (t2(modelo, x) > modelo.limite_t2) | (spe(modelo, x) > modelo.limite_spe)
    else:
        raise ValueError(f"estadistico desconocido: {estadistico!r}")
    racha = 0
    for i, flag in enumerate(sobre):
        racha = racha + 1 if flag else 0
        if racha >= consecutivas:
            return i
    return None


def contribuciones(modelo: ModeloPCA, observacion: np.ndarray) -> np.ndarray:
    """Contribución de cada variable al T² de una observación (p,). Valores negativos se truncan a 0."""
    z = (observacion - modelo.media) / modelo.desv
    scores = z @ modelo.cargas
    c = (scores / modelo.autovalores) * modelo.cargas * z[:, None]
    return np.clip(c.sum(axis=1), 0.0, None)


def contribuciones_spe(modelo: ModeloPCA, observacion: np.ndarray) -> np.ndarray:
    """Contribución de cada variable al SPE de una observación (p,): residuo al cuadrado."""
    z = (observacion - modelo.media) / modelo.desv
    return (z - z @ modelo.cargas @ modelo.cargas.T) ** 2
