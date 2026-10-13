"""Planta gemela disfrazada: la misma planta TEP presentada con otro nombre, para medir si el LLM razona o recita.

Niveles de disfraz (anidados: cada nivel incluye al anterior):
  0  TEP original: nombre del proceso, tags XMEAS/XMV, catálogo IDV, letras, corrientes, equipos y unidades originales.
  1  Sin etiquetas memorizables: proceso anónimo, tags ISA aleatorios, variables reordenadas, catálogo con códigos
     aleatorios y orden barajado. Se mantienen letras, corrientes, equipos y unidades.
  2  Disfraz completo: además, componentes, números de corriente, nombres de equipos y unidades cambian.

Garantías por construcción:
  - Los datos de la gemela son una transformación afín por columna más una permutación de columnas. Tras estandarizar,
    el PCA/T² da exactamente el mismo resultado (ver tests/test_gemela.py). Solo cambia lo que lee el LLM.
  - Todos los niveles se renderizan desde las mismas plantillas de core/tep.py: el contenido físico es idéntico.
  - El mapeo a TEP (columna original, IDV) vive en campos separados que el constructor de prompts no debe leer.
"""
import re
from dataclasses import dataclass, field

import numpy as np

from core import tep

SEMILLA = 20261012

# Componentes de la gemela: letras ajenas a A–H para que no se confundan con las originales.
LETRAS_GEMELA = "KLMNPRSU"

# Lo que no puede aparecer en ningún texto visible al LLM a partir de cada nivel.
_FUGAS_N1 = [r"(?i)tennessee", r"(?i)eastman", r"\bTEP\b", r"(?i)xmeas", r"(?i)xmv", r"\bIDV", r"Downs", r"Vogel"]
_FUGAS_N2 = _FUGAS_N1 + [
    r"(?<![°\w])[A-H](?!\w)",  # letra de componente original suelta (excluye °F)
    r"\bstream (?:1[01]|[1-9])\b",
    r"kPa", r"°C", r"kscmh", r"kg/h", r"m3/h", r"\bkW\b", r"mol%",
    r"(?i)reactor", r"(?i)stripper", r"(?i)separator", r"(?i)compressor", r"(?i)condenser", r"(?i)purge",
    r"(?i)cooling water",
]
FUGAS = {0: [], 1: _FUGAS_N1, 2: _FUGAS_N2}


@dataclass(frozen=True)
class Variable:
    tag: str
    descripcion: str
    unidad: str


@dataclass(frozen=True)
class Causa:
    codigo: str
    descripcion: str
    tipo: str


@dataclass
class Vista:
    """Lo que ve el LLM (variables, catalogo, descripcion) y, aparte, el mapeo para puntuar (origen, idv)."""
    nivel: int
    semilla: int
    variables: list[Variable]
    catalogo: list[Causa]
    descripcion: str
    # --- mapeo privado: no va al prompt ---
    origen: np.ndarray = field(repr=False)           # columna TEP de cada variable presentada
    escala: np.ndarray = field(repr=False)
    desplazamiento: np.ndarray = field(repr=False)
    idv: dict[str, int] = field(repr=False)          # código de causa → IDV

    def transformar(self, x: np.ndarray) -> np.ndarray:
        """Datos TEP (m, 52) → datos tal como los ve esta vista (m, 52)."""
        return x[:, self.origen] * self.escala + self.desplazamiento

    def textos_visibles(self) -> list[str]:
        """Todo lo que puede llegar al LLM."""
        textos = [self.descripcion]
        textos += [f"{v.tag} {v.descripcion} [{v.unidad}]" for v in self.variables]
        textos += [f"{c.codigo} {c.descripcion} ({c.tipo})" for c in self.catalogo]
        return textos


def _renderizar(plantilla: str, nombres: dict) -> str:
    texto = plantilla.format(**nombres)
    return texto[:1].upper() + texto[1:]


def construir(nivel: int, semilla: int = SEMILLA) -> Vista:
    if nivel not in (0, 1, 2):
        raise ValueError(f"nivel de disfraz desconocido: {nivel}")
    rng = np.random.default_rng(semilla)
    # Todos los sorteos se hacen siempre y en el mismo orden: los niveles 1 y 2 comparten tags, orden y códigos.
    perm = rng.permutation(52)
    numeros_tag = rng.choice(np.arange(100, 1000), size=52, replace=False)
    codigos = rng.choice(np.arange(10, 100), size=len(tep.FALLAS), replace=False)
    orden_catalogo = rng.permutation(len(tep.FALLAS))
    letras = rng.permutation(list(LETRAS_GEMELA))
    corrientes = rng.choice(np.arange(100, 1000), size=tep.N_CORRIENTES, replace=False)

    disfraz = nivel == 2
    nombres = {c: (letras[i] if disfraz else c) for i, c in enumerate(tep.COMPONENTES)}
    nombres |= {f"s{i + 1}": f"stream {corrientes[i] if disfraz else i + 1}" for i in range(tep.N_CORRIENTES)}
    nombres |= {k: v[1 if disfraz else 0] for k, v in tep.EQUIPOS.items()}
    nombres["intro"] = tep.INTRO_TEP if nivel == 0 else tep.INTRO_ANONIMA

    origen = np.arange(52) if nivel == 0 else perm
    variables, escala, desplazamiento = [], np.ones(52), np.zeros(52)
    for j, col in enumerate(origen):
        tag_tep, plantilla, tipo, letra = tep.VARIABLES[col]
        if nivel == 0:
            tag = tag_tep
        else:
            sufijo = "I" if tag_tep.startswith("XMEAS") else "V"
            tag = f"{letra}{sufijo}-{numeros_tag[col]}"
        etiqueta_tep, (etiqueta_gemela, a, b) = tep.UNIDADES[tipo]
        if disfraz:
            unidad, escala[j], desplazamiento[j] = etiqueta_gemela, a, b
        else:
            unidad = etiqueta_tep
        variables.append(Variable(tag, _renderizar(plantilla, nombres), unidad))

    orden = range(len(tep.FALLAS)) if nivel == 0 else orden_catalogo
    catalogo, idv = [], {}
    for k in orden:
        numero, plantilla, tipo = tep.FALLAS[k]
        codigo = f"IDV({numero})" if nivel == 0 else f"C{codigos[k]}"
        catalogo.append(Causa(codigo, _renderizar(plantilla, nombres), tipo))
        idv[codigo] = numero

    vista = Vista(nivel, semilla, variables, catalogo, tep.DESCRIPCION_PROCESO.format(**nombres),
                  origen, escala, desplazamiento, idv)
    fugas = buscar_fugas(vista)
    if fugas:
        raise AssertionError(f"la vista de nivel {nivel} deja ver TEP: {fugas[:5]}")
    return vista


def buscar_fugas(vista: Vista) -> list[tuple[str, str]]:
    """Pares (patrón, texto) de los textos visibles que delatan TEP para el nivel de la vista."""
    return [(p, t) for t in vista.textos_visibles() for p in FUGAS[vista.nivel] if re.search(p, t)]
