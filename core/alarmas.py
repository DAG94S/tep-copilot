"""Simulación determinista del sistema de alarmas de proceso (sin LLM).

TEP no trae límites de alarma oficiales, así que se calculan desde datos normales
(percentiles bajo/alto por variable). Solo se alarman las 41 mediciones (XMEAS); las 11
válvulas (XMV) no. Una alarma se activa tras `retardo` muestras consecutivas fuera del mismo
límite (anti-chattering). El criterio de inundación es el de EEMUA 191: más de 10 alarmas
en 10 minutos.
"""
from dataclasses import dataclass

import numpy as np

N_MEDICIONES = 41
MINUTOS_POR_MUESTRA = 3.0


@dataclass
class Limites:
    bajo: np.ndarray  # (p,)
    alto: np.ndarray  # (p,)


@dataclass
class Evento:
    muestra: int
    minuto: float
    variable: int     # índice de columna
    direccion: str    # "alta" | "baja"


def ajustar_limites(normal: np.ndarray, percentil: float = 99.9) -> Limites:
    """Límites bajo/alto por variable desde datos normales (n, p); XMV sin límites."""
    p = normal.shape[1]
    bajo = np.full(p, -np.inf)
    alto = np.full(p, np.inf)
    m = min(N_MEDICIONES, p)
    bajo[:m] = np.percentile(normal[:, :m], 100 - percentil, axis=0)
    alto[:m] = np.percentile(normal[:, :m], percentil, axis=0)
    return Limites(bajo, alto)


def eventos(limites: Limites, x: np.ndarray, retardo: int = 2, t0: int = 0) -> list[Evento]:
    """Eventos de activación de alarma en x (m, p), ordenados por muestra y variable."""
    salida = []
    estado = np.zeros(x.shape[1], dtype=int)  # +1 alta, -1 baja, 0 normal
    racha = np.zeros(x.shape[1], dtype=int)
    activa = np.zeros(x.shape[1], dtype=int)
    for i, fila in enumerate(x):
        actual = np.where(fila > limites.alto, 1, np.where(fila < limites.bajo, -1, 0))
        racha = np.where((actual != 0) & (actual == estado), racha + 1, (actual != 0).astype(int))
        estado = actual
        activa = np.where(actual == 0, 0, activa)
        nuevas = (actual != 0) & (racha >= retardo) & (activa != actual)
        for v in np.flatnonzero(nuevas):
            salida.append(Evento(i, (i - t0) * MINUTOS_POR_MUESTRA, int(v),
                                 "alta" if actual[v] > 0 else "baja"))
        activa = np.where(nuevas, actual, activa)
    return salida


def tasa_por_ventana(eventos: list[Evento], minutos: float = 10.0) -> int:
    """Máximo número de eventos en cualquier ventana deslizante de `minutos`."""
    t = sorted(e.minuto for e in eventos)
    mejor, j = 0, 0
    for i in range(len(t)):
        while t[i] - t[j] >= minutos:
            j += 1
        mejor = max(mejor, i - j + 1)
    return mejor


def inundacion(eventos: list[Evento], umbral: int = 10, minutos: float = 10.0) -> bool:
    """True si hay más de `umbral` eventos en alguna ventana de `minutos` (EEMUA 191)."""
    return tasa_por_ventana(eventos, minutos) > umbral


def primeras_salidas(eventos: list[Evento], n: int | None = None) -> list[Evento]:
    """First-out: primer evento de cada variable, en orden de aparición."""
    vistas, salida = set(), []
    for e in eventos:
        if e.variable not in vistas:
            vistas.add(e.variable)
            salida.append(e)
    return salida[:n] if n is not None else salida
