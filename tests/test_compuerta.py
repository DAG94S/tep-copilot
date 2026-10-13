"""Pruebas de la compuerta determinista y del contrato JSON del LLM (sin datos ni LLM)."""
import numpy as np
import pydantic
import pytest

from core import compuerta
from core.esquema import Diagnostico, esquema_json

TAGS = ["TI-1", "PI-2", "FI-3", "LI-4"]
CODIGOS = {"C10", "C20", "C30"}
Z = np.array([5.0, -4.0, 0.5, 3.2])


def diag(causas=("C10",), evidencia=(("TI-1", "up"),), explicacion="Temperature rose after the disturbance."):
    return Diagnostico.model_validate({
        "causes": list(causas),
        "evidence": [{"tag": t, "direction": d} for t, d in evidencia],
        "explanation": explicacion,
    })


def verificar(d, **kw):
    return compuerta.verificar(d, tags=TAGS, codigos=CODIGOS, z=Z, **kw)


def test_esquema_rechaza_campos_extra_y_direcciones_invalidas():
    with pytest.raises(pydantic.ValidationError):
        Diagnostico.model_validate({"causes": ["C10"], "evidence": [{"tag": "TI-1", "direction": "up"}],
                                    "explanation": "x", "action": "open valve"})
    with pytest.raises(pydantic.ValidationError):
        diag(evidencia=(("TI-1", "sideways"),))
    with pytest.raises(pydantic.ValidationError):
        diag(causas=())
    assert set(esquema_json()["properties"]) == {"causes", "evidence", "explanation"}


def test_evidencia_coherente_se_verifica():
    v = verificar(diag(evidencia=(("TI-1", "up"), ("PI-2", "down"), ("LI-4", "up"))))
    assert v.estado == "VERIFICADO" and len(v.evidencia_verificada) == 3 and not v.evidencia_rechazada


def test_afirmaciones_sin_respaldo_se_retiran():
    v = verificar(diag(evidencia=(("TI-1", "up"), ("PI-2", "up"), ("FI-3", "up"), ("XX-9", "up"))))
    assert v.estado == "PARCIAL"
    motivos = {e.tag: m for e, m in v.evidencia_rechazada}
    assert "contraria" in motivos["PI-2"] and "sin desviación" in motivos["FI-3"] and "inexistente" in motivos["XX-9"]
    assert v.afirmaciones == 4


def test_sin_evidencia_valida_se_bloquea():
    assert verificar(diag(evidencia=(("FI-3", "up"),))).estado == "BLOQUEADO"


def test_causa_fuera_del_catalogo_se_bloquea():
    v = verificar(diag(causas=("C10", "IDV(4)")))
    assert v.estado == "BLOQUEADO" and "IDV(4)" in v.motivos[0]


@pytest.mark.parametrize("texto", [
    "Close the coolant valve immediately.",
    "The cause is a feed loss. Reduce the feed rate.",
    "Operators should open the vent.",
    "We recommend to set the converter pressure lower.",
    "- Stop the recycle blower",
])
def test_ordenes_de_control_se_bloquean(texto):
    v = verificar(diag(explicacion=texto))
    assert v.estado == "BLOQUEADO" and any("orden de control" in m for m in v.motivos)


@pytest.mark.parametrize("texto", [
    "The coolant valve appears stuck open, so the temperature increased.",
    "Pressure decreased while the level stayed closed to its normal range.",
    "A step in the feed temperature would raise the converter temperature.",
])
def test_lenguaje_descriptivo_pasa(texto):
    assert compuerta.ordenes_de_control(texto) == []


def test_votacion_y_bajo_acuerdo():
    muestras = [diag(causas=("C10",)), diag(causas=("C20",)), diag(causas=("C10", "C20")), diag(causas=("C30",))]
    elegido, acuerdo = compuerta.votar(muestras)
    assert elegido.causas[0] == "C10" and acuerdo == 0.5
    v = compuerta.verificar_muestras(muestras, tags=TAGS, codigos=CODIGOS, z=Z)
    assert v.estado == "INCIERTO" and v.confianza == 0.5
    v = compuerta.verificar_muestras(muestras[:1] * 3, tags=TAGS, codigos=CODIGOS, z=Z)
    assert v.estado == "VERIFICADO" and v.confianza == 1.0


def test_bloqueo_prevalece_sobre_incierto():
    muestras = [diag(causas=("C99",)), diag(causas=("C20",))]
    assert compuerta.verificar_muestras(muestras, tags=TAGS, codigos=CODIGOS, z=Z).estado == "BLOQUEADO"


def test_desviacion_z_usa_mediana():
    ventana = np.array([[10.0, 0.0], [12.0, 0.0], [100.0, 0.0]])
    z = compuerta.desviacion_z(ventana, media=np.array([0.0, 0.0]), desv=np.array([2.0, 0.0]))
    np.testing.assert_allclose(z, [6.0, 0.0])
