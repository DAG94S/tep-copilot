"""Metadatos del Tennessee Eastman Process como plantillas, para renderizarlos en TEP original o en la planta gemela.

Fuente de nombres, unidades y fallas: Downs & Vogel (1993), Comput. Chem. Eng. 17(3):245–255, tablas de
variables medidas (XMEAS 1–41), manipuladas (XMV 1–11; XMV 12, agitador, no viene en los datos de Braatz) y
perturbaciones (IDV 1–15). El catálogo de 15 causas es el que usa FaultExplainer (Khan et al. 2025).

Cada texto es una plantilla con marcadores:
  {A}..{H}   componentes químicos
  {s1}..{s11} corrientes ("stream N")
  {reactor} {condenser} {separator} {compressor} {stripper} {purge} {cw}  equipos y servicios
Los textos que lee el LLM están en inglés; el código y los comentarios, en español.
"""

# Orden de columnas de los datos: XMEAS(1..41) y luego XMV(1..11) → 52 variables.
# Cada entrada: (tag original, plantilla de descripción, tipo de unidad, letra ISA)
VARIABLES = [
    ("XMEAS(1)", "{A} feed ({s1})", "kscmh", "F"),
    ("XMEAS(2)", "{D} feed ({s2})", "kg_h", "F"),
    ("XMEAS(3)", "{E} feed ({s3})", "kg_h", "F"),
    ("XMEAS(4)", "{A} and {C} feed ({s4})", "kscmh", "F"),
    ("XMEAS(5)", "recycle flow ({s8})", "kscmh", "F"),
    ("XMEAS(6)", "{reactor} feed rate ({s6})", "kscmh", "F"),
    ("XMEAS(7)", "{reactor} pressure", "kpa", "P"),
    ("XMEAS(8)", "{reactor} level", "pct_nivel", "L"),
    ("XMEAS(9)", "{reactor} temperature", "degc", "T"),
    ("XMEAS(10)", "{purge} rate ({s9})", "kscmh", "F"),
    ("XMEAS(11)", "{separator} temperature", "degc", "T"),
    ("XMEAS(12)", "{separator} level", "pct_nivel", "L"),
    ("XMEAS(13)", "{separator} pressure", "kpa", "P"),
    ("XMEAS(14)", "{separator} underflow ({s10})", "m3_h", "F"),
    ("XMEAS(15)", "{stripper} level", "pct_nivel", "L"),
    ("XMEAS(16)", "{stripper} pressure", "kpa", "P"),
    ("XMEAS(17)", "{stripper} underflow ({s11})", "m3_h", "F"),
    ("XMEAS(18)", "{stripper} temperature", "degc", "T"),
    ("XMEAS(19)", "{stripper} steam flow", "kg_h", "F"),
    ("XMEAS(20)", "{compressor} work", "kw", "J"),
    ("XMEAS(21)", "{reactor} {cw} outlet temperature", "degc", "T"),
    ("XMEAS(22)", "{separator} {cw} outlet temperature", "degc", "T"),
]
VARIABLES += [(f"XMEAS({23 + i})", f"{{{c}}} in {{reactor}} feed ({{s6}})", "molpct", "A") for i, c in enumerate("ABCDEF")]
VARIABLES += [(f"XMEAS({29 + i})", f"{{{c}}} in {{purge}} gas ({{s9}})", "molpct", "A") for i, c in enumerate("ABCDEFGH")]
VARIABLES += [(f"XMEAS({37 + i})", f"{{{c}}} in product ({{s11}})", "molpct", "A") for i, c in enumerate("DEFGH")]
VARIABLES += [
    ("XMV(1)", "{D} feed flow ({s2})", "pct_valv", "F"),
    ("XMV(2)", "{E} feed flow ({s3})", "pct_valv", "F"),
    ("XMV(3)", "{A} feed flow ({s1})", "pct_valv", "F"),
    ("XMV(4)", "{A} and {C} feed flow ({s4})", "pct_valv", "F"),
    ("XMV(5)", "{compressor} recycle valve", "pct_valv", "P"),
    ("XMV(6)", "{purge} valve ({s9})", "pct_valv", "F"),
    ("XMV(7)", "{separator} pot liquid flow ({s10})", "pct_valv", "F"),
    ("XMV(8)", "{stripper} liquid product flow ({s11})", "pct_valv", "F"),
    ("XMV(9)", "{stripper} steam valve", "pct_valv", "F"),
    ("XMV(10)", "{reactor} {cw} flow", "pct_valv", "F"),
    ("XMV(11)", "{condenser} {cw} flow", "pct_valv", "F"),
]
assert len(VARIABLES) == 52

# Unidades: tipo → ((etiqueta TEP), (etiqueta gemela, escala, desplazamiento)) con valor_gemela = escala·x + desplazamiento.
# Conversiones afines: estandarizar las columnas las anula, así que el detector PCA/T² no cambia.
# kscmh→kSCFH ignora la diferencia de condiciones estándar (0 °C vs 60 °F): es un disfraz, no un balance.
UNIDADES = {
    "kscmh": ("kscmh", ("kSCFH", 35.3147, 0.0)),
    "kg_h": ("kg/h", ("lb/h", 2.204623, 0.0)),
    "kpa": ("kPa gauge", ("psig", 0.1450377, 0.0)),
    "pct_nivel": ("%", ("fraction of span", 0.01, 0.0)),
    "degc": ("°C", ("°F", 1.8, 32.0)),
    "m3_h": ("m3/h", ("US gpm", 4.402868, 0.0)),
    "kw": ("kW", ("hp", 1.341022, 0.0)),
    "molpct": ("mol%", ("mole fraction", 0.01, 0.0)),
    "pct_valv": ("% open", ("fraction open", 0.01, 0.0)),
}

# Catálogo de 15 causas candidatas: (IDV, plantilla, tipo de perturbación)
FALLAS = [
    (1, "{A}/{C} feed ratio, {B} composition constant ({s4})", "step"),
    (2, "{B} composition, {A}/{C} ratio constant ({s4})", "step"),
    (3, "{D} feed temperature ({s2})", "step"),
    (4, "{reactor} {cw} inlet temperature", "step"),
    (5, "{condenser} {cw} inlet temperature", "step"),
    (6, "{A} feed loss ({s1})", "step"),
    (7, "{C} header pressure loss, reduced availability ({s4})", "step"),
    (8, "{A}, {B}, {C} feed composition ({s4})", "random variation"),
    (9, "{D} feed temperature ({s2})", "random variation"),
    (10, "{C} feed temperature ({s4})", "random variation"),
    (11, "{reactor} {cw} inlet temperature", "random variation"),
    (12, "{condenser} {cw} inlet temperature", "random variation"),
    (13, "reaction kinetics", "slow drift"),
    (14, "{reactor} {cw} valve", "sticking"),
    (15, "{condenser} {cw} valve", "sticking"),
]

# Nombres de equipos y servicios: (TEP, gemela)
EQUIPOS = {
    "reactor": ("reactor", "converter"),
    "condenser": ("condenser", "overhead cooler"),
    "separator": ("separator", "flash drum"),
    "compressor": ("compressor", "blower"),
    "stripper": ("stripper", "recovery column"),
    "purge": ("purge", "vent"),
    "cw": ("cooling water", "coolant"),
}

COMPONENTES = "ABCDEFGH"
N_CORRIENTES = 11

DESCRIPCION_PROCESO = """\
{intro}
The plant converts four gaseous reactants ({A}, {C}, {D}, {E}) into two liquid products ({G}, {H}). \
The feeds also carry an inert component ({B}), and side reactions form a byproduct ({F}).

Reactions (all irreversible and exothermic; rates increase with temperature):
  {A}(g) + {C}(g) + {D}(g) -> {G}(liq)
  {A}(g) + {C}(g) + {E}(g) -> {H}(liq)
  {A}(g) + {E}(g) -> {F}(liq)
  3 {D}(g) -> 2 {F}(liq)

Flow sheet:
- Gaseous feeds enter the {reactor}: {A} ({s1}), {D} ({s2}) and {E} ({s3}). The combined {reactor} feed is {s6}.
- An internal {cw} bundle removes the heat of reaction from the {reactor}.
- The {reactor} effluent ({s7}) passes through the {condenser} into the {separator}.
- Vapor from the {separator} returns to the {reactor} feed through the recycle {compressor} ({s8}). \
Part of it leaves as {purge} ({s9}) to remove the inert and the byproduct.
- Condensed liquid from the {separator} ({s10}) goes to the {stripper}. Feed {s4}, which carries {A} and {C}, \
strips the remaining reactants from it; the stripped vapor joins the {reactor} feed through {s5}.
- Products {G} and {H} leave the {stripper} base as {s11}. Steam heats the {stripper}.
"""

INTRO_TEP = "This is the Tennessee Eastman process (Downs & Vogel, 1993)."
INTRO_ANONIMA = "This is a continuous chemical plant."
