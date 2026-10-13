"""Detección de fallas con PCA y estadístico T² (protocolo de FaultExplainer, Khan et al. 2025).

Protocolo replicado: PCA con 90% de varianza acumulada sobre datos normales estandarizados,
límite T² con α=0,01 (distribución F) y alarma tras 6 observaciones consecutivas sobre el límite.
La contribución por variable es la de Kourti & MacGregor (1996) para T².

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
    return ModeloPCA(media, desv, vt[:a].T, autoval[:a], float(limite), n)


def t2(modelo: ModeloPCA, x: np.ndarray) -> np.ndarray:
    """T² de cada observación (m, p) → (m,)."""
    z = (x - modelo.media) / modelo.desv
    scores = z @ modelo.cargas
    return np.sum(scores**2 / modelo.autovalores, axis=1)


def primera_alarma(modelo: ModeloPCA, x: np.ndarray, consecutivas: int = CONSECUTIVAS):
    """Índice de la observación que cumple `consecutivas` alarmas seguidas (None si no hay)."""
    sobre = t2(modelo, x) > modelo.limite_t2
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
