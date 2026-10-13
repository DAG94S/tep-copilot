"""Pruebas de la planta gemela: sin fugas de TEP, mapeos biyectivos y detector invariante al disfraz."""
import numpy as np
import pytest

from core import datos, pca_t2, tep
from twin import gemela

NIVELES = (0, 1, 2)


@pytest.mark.parametrize("nivel", NIVELES)
def test_sin_fugas(nivel):
    assert gemela.buscar_fugas(gemela.construir(nivel)) == []


def test_el_detector_de_fugas_si_detecta():
    vista = gemela.construir(2)
    vista.variables[0] = gemela.Variable("XMEAS(9)", "Reactor temperature", "°C")
    patrones = {p for p, _ in gemela.buscar_fugas(vista)}
    assert {r"(?i)xmeas", r"°C", r"(?i)reactor"} <= patrones


def test_nivel_0_es_tep_sin_cambios():
    vista = gemela.construir(0)
    x = np.arange(2 * 52, dtype=float).reshape(2, 52)
    np.testing.assert_array_equal(vista.transformar(x), x)
    assert vista.variables[8] == gemela.Variable("XMEAS(9)", "Reactor temperature", "°C")
    assert "Tennessee Eastman" in vista.descripcion


@pytest.mark.parametrize("nivel", NIVELES)
def test_mapeos_biyectivos(nivel):
    vista = gemela.construir(nivel)
    assert sorted(vista.origen) == list(range(52))
    assert len({v.tag for v in vista.variables}) == 52
    assert sorted(vista.idv.values()) == list(range(1, 16))
    assert [c.codigo for c in vista.catalogo] == list(vista.idv)


def test_es_determinista():
    a, b = gemela.construir(2), gemela.construir(2)
    assert a.variables == b.variables and a.catalogo == b.catalogo and a.descripcion == b.descripcion


def test_niveles_1_y_2_comparten_tags_orden_y_codigos():
    n1, n2 = gemela.construir(1), gemela.construir(2)
    np.testing.assert_array_equal(n1.origen, n2.origen)
    assert [v.tag for v in n1.variables] == [v.tag for v in n2.variables]
    assert list(n1.idv.items()) == list(n2.idv.items())


def test_nivel_2_convierte_unidades():
    vista = gemela.construir(2)
    j = int(np.flatnonzero(vista.origen == 8)[0])  # XMEAS(9), temperatura del reactor
    assert vista.variables[j].unidad == "°F"
    assert vista.variables[j].descripcion == "Converter temperature"
    x = np.zeros((1, 52))
    x[0, 8] = 120.4
    assert vista.transformar(x)[0, j] == pytest.approx(120.4 * 1.8 + 32)


def test_nivel_2_renombra_igual_en_descripcion_variables_y_catalogo():
    vista = gemela.construir(2)
    letra_a = vista.descripcion.split("reactants (")[1][0]  # nombre gemelo de A
    assert letra_a in gemela.LETRAS_GEMELA
    assert any(v.descripcion == f"{letra_a} feed ({vista.descripcion.split(f'{letra_a} (')[1].split(')')[0]})"
               for v in vista.variables)
    assert any(c.descripcion.startswith(f"{letra_a} feed loss") for c in vista.catalogo)


requiere_datos = pytest.mark.skipif(
    not (datos.BRAATZ / "d00.dat").exists(), reason="faltan datos: python3 scripts/descargar_datos.py"
)


@requiere_datos
@pytest.mark.parametrize("nivel", (1, 2))
@pytest.mark.parametrize("falla", (1, 6, 14))
def test_detector_invariante_al_disfraz(nivel, falla):
    vista = gemela.construir(nivel)
    normal, prueba = datos.cargar(0), datos.cargar(falla, prueba=True)
    m_tep = pca_t2.ajustar(normal)
    m_gem = pca_t2.ajustar(vista.transformar(normal))
    assert m_gem.componentes == m_tep.componentes
    np.testing.assert_allclose(pca_t2.t2(m_gem, vista.transformar(prueba)), pca_t2.t2(m_tep, prueba), rtol=1e-6)
    assert pca_t2.primera_alarma(m_gem, vista.transformar(prueba)) == pca_t2.primera_alarma(m_tep, prueba)
    i = datos.INICIO_FALLA_TEST + 40
    c_tep = pca_t2.contribuciones(m_tep, prueba[i])
    c_gem = pca_t2.contribuciones(m_gem, vista.transformar(prueba)[i])
    np.testing.assert_allclose(c_gem, c_tep[vista.origen], rtol=1e-6, atol=1e-9)


def test_catalogo_y_variables_cubren_tep():
    assert len(tep.VARIABLES) == 52 and len(tep.FALLAS) == 15
