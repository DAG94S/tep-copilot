"""Pruebas del cargador y del detector PCA T² con datos reales pineados (requieren data/raw/braatz)."""
import numpy as np
import pytest

from core import datos, pca_t2

pytestmark = pytest.mark.skipif(
    not (datos.BRAATZ / "d00.dat").exists(), reason="faltan datos: python3 scripts/descargar_datos.py"
)


@pytest.fixture(scope="module")
def modelo():
    return pca_t2.ajustar(datos.cargar(0))


def test_d00_se_normaliza_a_muestras_por_variables():
    assert datos.cargar(0).shape == (500, 52)
    assert datos.cargar(0, prueba=True).shape == (960, 52)
    assert datos.cargar(1).shape == (480, 52)


def test_sin_falsa_alarma_en_operacion_normal(modelo):
    assert pca_t2.primera_alarma(modelo, datos.cargar(0, prueba=True)) is None


def test_detecta_idv1_despues_de_la_falla(modelo):
    i = pca_t2.primera_alarma(modelo, datos.cargar(1, prueba=True))
    assert i is not None and i >= datos.INICIO_FALLA_TEST


def test_contribuciones_no_negativas(modelo):
    x = datos.cargar(1, prueba=True)
    c = pca_t2.contribuciones(modelo, x[datos.INICIO_FALLA_TEST + 20])
    assert c.shape == (52,) and (c >= 0).all() and c.sum() > 0
