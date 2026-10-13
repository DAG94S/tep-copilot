"""Construcción del prompt. Solo lee los campos públicos de la vista; nada de TEP ni del mapeo privado.

Los textos que lee el LLM están en inglés y son neutros: sin vocabulario de planta concreta.
"""
from dataclasses import dataclass

SISTEMA = (
    "You are a diagnostic assistant for control room operators. You only propose; you never control anything.\n"
    "You receive a process description, a table of process variables, the variables that deviate most at the moment "
    "an anomaly was detected, and a catalog of possible root causes.\n"
    "Rules:\n"
    "1. Choose 1 to 3 causes, only by their catalog code, from most to least probable.\n"
    "2. Cite 1 to 6 evidence sensors by their exact tag, each with direction \"up\" or \"down\" relative to normal.\n"
    "3. The explanation must describe what is happening and why. Never order actions and never use control "
    "imperatives (open, close, set, start, stop, adjust, increase, decrease...).\n"
    "4. Reply ONLY with a JSON object with keys \"causes\" (list of codes), \"evidence\" (list of objects with "
    "\"tag\" and \"direction\") and \"explanation\" (string). No text outside the JSON."
)

EJEMPLO = '{"causes": ["C00"], "evidence": [{"tag": "XX-000", "direction": "up"}], "explanation": "Short description."}'


@dataclass
class Fila:
    indice: int            # columna en la vista (0..51)
    contribucion: float
    z: float
    valor: float
    media_normal: float


def _n(x: float) -> str:
    return f"{x:.4g}"


def construir_mensajes(vista, filas: list[Fila]) -> list[dict]:
    lineas = ["Process description:", vista.descripcion, "", "Process variables:", "tag | description | unit"]
    lineas += [f"{v.tag} | {v.descripcion} | {v.unidad}" for v in vista.variables]
    lineas += ["", "Top contributing variables at detection:",
               "tag | description | unit | normal value | current value | z | contribution"]
    for f in filas:
        v = vista.variables[f.indice]
        lineas.append(f"{v.tag} | {v.descripcion} | {v.unidad} | {_n(f.media_normal)} | {_n(f.valor)} | "
                      f"{f.z:+.4g} | {_n(f.contribucion)}")
    lineas += ["", "Catalog of possible causes:", "code | description | type"]
    lineas += [f"{c.codigo} | {c.descripcion} | {c.tipo}" for c in vista.catalogo]
    lineas += ["", "Output format example (fictitious code and tag):", EJEMPLO]
    return [{"role": "system", "content": SISTEMA}, {"role": "user", "content": "\n".join(lineas)}]
