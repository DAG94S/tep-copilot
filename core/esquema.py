"""Contrato de salida del LLM: el JSON que Gemma debe devolver. Las claves del JSON van en inglés (alias).

El LLM solo propone: causas del catálogo y sensores de evidencia con la dirección de su desviación.
No hay ningún campo para acciones sobre el proceso.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Evidencia(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    tag: str
    direccion: Literal["up", "down"] = Field(alias="direction")


class Diagnostico(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    causas: list[str] = Field(alias="causes", min_length=1, max_length=3)  # códigos del catálogo, de más a menos probable
    evidencia: list[Evidencia] = Field(alias="evidence", min_length=1, max_length=6)
    explicacion: str = Field(alias="explanation", max_length=1500)


def esquema_json() -> dict:
    """JSON Schema con las claves en inglés, para el prompt y para la salida guiada de vLLM."""
    return Diagnostico.model_json_schema(by_alias=True)
