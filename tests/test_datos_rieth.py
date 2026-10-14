"""Pruebas de la carga de Rieth et al. (2017); se omiten si los .npz no existen (CI sin datos)."""
import numpy as np
import pytest

from core import datos

pytestmark = pytest.mark.skipif(not (datos.RIETH / "faulty_train_f01.npz").exists(),
                                reason="faltan los .npz de data/processed/rieth")


def test_forma_y_dtype():
    x = datos.cargar_rieth(1, 1)
    assert x.shape == (500, 52) and x.dtype == np.float32
    assert datos.cargar_rieth(0, 1).shape == (500, 52)


def test_corridas_independientes():
    assert not np.allclose(datos.cargar_rieth(1, 1), datos.cargar_rieth(1, 2))


def test_corrida_fuera_de_rango():
    with pytest.raises(ValueError):
        datos.cargar_rieth(1, 21)


def test_antes_de_la_falla_se_parece_a_la_normal():
    normal = datos.cargar_rieth(0, 1).astype(float)
    sd = normal.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    for falla in (1, 4, 6):
        previo = datos.cargar_rieth(falla, 1)[:datos.INICIO_FALLA_RIETH_TRAIN].astype(float)
        z = np.abs(previo.mean(axis=0) - normal.mean(axis=0)) / sd
        assert np.median(z) < 1.0


def test_orden_de_columnas_como_braatz():
    # Los medias de la corrida normal de Rieth y de Braatz (d00) coinciden en orden de magnitud por columna.
    r = datos.cargar_rieth(0, 1).astype(float).mean(axis=0)
    b = datos.cargar(0).mean(axis=0)
    assert np.all(np.abs(r - b) <= 0.5 * np.abs(b) + 1.0)
