"""Extracción y validación del JSON que devuelve el LLM."""
import json
import re

from pydantic import ValidationError

from core.esquema import Diagnostico

_CERCO = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


# Bloques de razonamiento que algunos endpoints no permiten apagar (Gemma 4 en la API de Gemini). Si el bloque no
# se cierra (se cortó por max_tokens), todo lo que sigue es razonamiento y no hay respuesta.
_PENSAMIENTO = re.compile(r"<(thought|think)>.*?(?:</\1>|$)", re.DOTALL)


def quitar_pensamiento(texto: str) -> str:
    return _PENSAMIENTO.sub("", texto)


def extraer_json(texto: str) -> dict:
    """Primer objeto {...} balanceado de la respuesta, sin razonamiento ni cercos de código. ValueError si no hay JSON."""
    texto = quitar_pensamiento(texto)
    m = _CERCO.search(texto)
    if m and "{" in m.group(1):
        texto = m.group(1)
    inicio = texto.find("{")
    while inicio != -1:
        profundidad, en_cadena, escapado = 0, False, False
        for i in range(inicio, len(texto)):
            c = texto[i]
            if en_cadena:
                if escapado:
                    escapado = False
                elif c == "\\":
                    escapado = True
                elif c == '"':
                    en_cadena = False
            elif c == '"':
                en_cadena = True
            elif c == "{":
                profundidad += 1
            elif c == "}":
                profundidad -= 1
                if profundidad == 0:
                    try:
                        obj = json.loads(texto[inicio:i + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(obj, dict):
                        return obj
                    break
        inicio = texto.find("{", inicio + 1)
    raise ValueError("no hay un objeto JSON en el texto")


def parsear(texto: str) -> tuple[Diagnostico | None, str | None]:
    """(diagnóstico, None) o (None, mensaje de error); nunca lanza."""
    try:
        return Diagnostico.model_validate(extraer_json(texto)), None
    except ValueError as e:  # incluye ValidationError
        if isinstance(e, ValidationError):
            return None, "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
        return None, str(e)
