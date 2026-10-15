"""Pruebas del anotador de causas de la réplica (eval/extraer_causas_llm.py), sin red."""
import pytest

from eval import extraer_causas_llm as ex
from llm.cliente import ClienteSimulado


def test_validar_filtra_duplicados_y_trunca_a_tres():
    assert ex.validar({"proposed": [6, "7", 6, 1, 2], "concluded": True}) == ([6, 7, 1], True)


@pytest.mark.parametrize("obj", [{"proposed": [16], "concluded": True}, {"proposed": [1]}, [1, 2]])
def test_validar_rechaza_formato_invalido(obj):
    with pytest.raises((ValueError, TypeError)):
        ex.validar(obj)


def test_puntuar_mayoria_estricta():
    assert ex.puntuar(6, [[6, 7], [7, 6], [1, 2], [6], []]) == {"aciertos_muestras": 3, "acierto_top3": True,
                                                                 "acierto_top1": False}


def test_anotar_reintenta_hasta_json_valido():
    c = ClienteSimulado(["no json", '{"proposed": [99], "concluded": true}', '{"proposed": [4, 11], "concluded": false}'])
    r = ex.anotar(c, "texto", max_tokens=50)
    assert r["propuestas"] == [4, 11] and r["concluyo"] is False


def test_anotar_marca_error_si_nunca_valida():
    r = ex.anotar(ClienteSimulado(["nada"]), "texto", max_tokens=50, intentos=2)
    assert r["propuestas"] == [] and "error" in r
