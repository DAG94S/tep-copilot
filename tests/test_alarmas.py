"""Pruebas del sistema de alarmas: sintéticas (sin datos) y con datos reales de Braatz."""
import numpy as np
import pytest

from core import alarmas, datos
from core.alarmas import Evento, Limites

hay_datos = (datos.BRAATZ / "d00.dat").exists()


def _lim(p=2):
    return Limites(np.full(p, -1.0), np.full(p, 1.0))


def test_retardo_desactivacion_reactivacion_y_direccion():
    x = np.zeros((12, 2))
    x[1:4, 0] = 2      # alta: se activa en muestra 2 (retardo 2), sigue activa en 3
    x[4, 0] = 0        # desactiva
    x[5, 0] = 2        # una sola muestra: no activa
    x[7:9, 0] = 2      # reactiva en 8
    x[2:4, 1] = -2     # baja en variable 1, activa en 3
    ev = alarmas.eventos(_lim(), x, retardo=2)
    assert [(e.muestra, e.variable, e.direccion) for e in ev] == [
        (2, 0, "alta"), (3, 1, "baja"), (8, 0, "alta")]
    assert ev[0].minuto == 2 * alarmas.MINUTOS_POR_MUESTRA


def test_t0_desplaza_el_minuto():
    x = np.zeros((6, 1))
    x[3:5, 0] = 2
    ev = alarmas.eventos(_lim(1), x, retardo=2, t0=3)
    assert ev[0].muestra == 4 and ev[0].minuto == 3.0


def _evs(minutos):
    return [Evento(int(m / 3), float(m), 0, "alta") for m in minutos]


def test_tasa_e_inundacion_en_el_borde():
    diez = _evs([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    once = _evs([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9.5])
    assert alarmas.tasa_por_ventana(diez) == 10 and not alarmas.inundacion(diez)
    assert alarmas.tasa_por_ventana(once) == 11 and alarmas.inundacion(once)
    assert alarmas.tasa_por_ventana(_evs([0, 10, 20])) == 1
    assert alarmas.tasa_por_ventana([]) == 0


def test_primeras_salidas():
    ev = [Evento(1, 3, 5, "alta"), Evento(2, 6, 5, "baja"), Evento(3, 9, 2, "alta")]
    assert [e.variable for e in alarmas.primeras_salidas(ev)] == [5, 2]
    assert len(alarmas.primeras_salidas(ev, n=1)) == 1


def test_xmv_sin_limites():
    lim = alarmas.ajustar_limites(np.random.default_rng(0).normal(size=(500, 52)))
    assert np.isinf(lim.bajo[41:]).all() and np.isfinite(lim.alto[:41]).all()


@pytest.mark.skipif(not hay_datos, reason="faltan datos: python3 scripts/descargar_datos.py")
def test_con_datos_reales():
    lim = alarmas.ajustar_limites(datos.cargar(0))
    ev0 = alarmas.eventos(lim, datos.cargar(0, prueba=True))
    print("eventos d00_te:", len(ev0))
    assert not alarmas.inundacion(ev0)
    ev1 = alarmas.eventos(lim, datos.cargar(1, prueba=True))
    print("eventos d01_te:", len(ev1), "tasa:", alarmas.tasa_por_ventana(ev1))
    tras = [e for e in ev1 if e.muestra > datos.INICIO_FALLA_TEST]
    assert tras
    primeras = alarmas.primeras_salidas(tras, 5)
    print("primeras:", [(e.variable, e.direccion) for e in primeras])
    assert len({e.variable for e in primeras}) == len(primeras) > 1
