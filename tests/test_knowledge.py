"""Los documentos de la Knowledge Library no deben contener órdenes de control."""
from pathlib import Path

import pytest

from core.compuerta import ordenes_de_control

DOCS = ["tep_process_description.md", "alarm_response_procedure.md", "inspection_guide_by_disturbance.md"]
RAIZ = Path(__file__).resolve().parents[1] / "knowledge"


@pytest.mark.parametrize("nombre", DOCS)
def test_sin_ordenes_de_control(nombre):
    texto = (RAIZ / nombre).read_text(encoding="utf-8")
    assert ordenes_de_control(texto) == []
    assert "## Sources" in texto


def test_guia_cubre_idv_1_a_15():
    texto = (RAIZ / "inspection_guide_by_disturbance.md").read_text(encoding="utf-8")
    for i in range(1, 16):
        assert f"IDV({i})" in texto
