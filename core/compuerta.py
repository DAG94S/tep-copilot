"""Compuerta determinista: verifica lo que propone el LLM antes de que llegue al operador.

Invariante del proyecto: la estadística detecta → el LLM propone → esta compuerta verifica → el humano aprueba.

Comprobaciones:
  1. Cada causa citada existe en el catálogo que vio el LLM. Si no → BLOQUEADO.
  2. La explicación no contiene órdenes de control (abrir, cerrar, fijar, arrancar, parar…). Si las hay → BLOQUEADO.
  3. Cada sensor de evidencia existe y se desvió de verdad, en la dirección que dice el LLM:
     z mediano de la ventana ≥ umbral_z, con signo coherente. Si la mediana no llega al umbral pero la desviación
     RMS de la ventana sí (variable oscilante: válvula pegada, variaciones aleatorias), la afirmación se acepta como
     "oscila (dirección no verificable)" y cuenta como verificada. Las afirmaciones no respaldadas se retiran de la tarjeta
     y se cuentan. Si ninguna se sostiene → BLOQUEADO; si solo algunas → PARCIAL.
  4. Autoconsistencia: con k muestras del LLM, la confianza es la fracción que coincide en la causa principal.
     Por debajo de umbral_acuerdo → INCIERTO (escalar a supervisor).

Trabaja en las coordenadas de la vista (TEP o gemela): las escalas del disfraz son positivas, así que el signo de z
no cambia entre vistas. No depende de twin/ ni del LLM.
"""
import re
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from core.esquema import Diagnostico, Evidencia

UMBRAL_Z = 3.0
UMBRAL_ACUERDO = 0.6

# Verbos de control en forma de orden: al inicio de oración o de viñeta, o tras un modal/recomendación.
# Las formas descriptivas pasan ("the valve is stuck open", "temperature increased").
_VERBOS = r"(?:open|close|shut|set|start|stop|restart|trip|bypass|override|adjust|increase|decrease|raise|lower|reduce)"
_ORDEN = re.compile(
    rf"(?:^|[.;:!?\n]\s*|^\s*[-*•]\s*|\b(?:should|must|recommend(?:ed)?(?:\s+to)?|need\s+to|please|try\s+to)\s+)"
    rf"{_VERBOS}\b",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class Veredicto:
    estado: str                                   # VERIFICADO | PARCIAL | BLOQUEADO | INCIERTO
    motivos: list[str] = field(default_factory=list)
    causas: list[str] = field(default_factory=list)
    evidencia_verificada: list[Evidencia] = field(default_factory=list)
    evidencia_rechazada: list[tuple[Evidencia, str]] = field(default_factory=list)
    evidencia_oscilante: list[tuple[Evidencia, str]] = field(default_factory=list)  # aceptada sin dirección verificada
    confianza: float | None = None                # acuerdo entre muestras; None si k=1

    @property
    def afirmaciones(self) -> int:
        return len(self.evidencia_verificada) + len(self.evidencia_oscilante) + len(self.evidencia_rechazada)


def desviacion_z(ventana: np.ndarray, media: np.ndarray, desv: np.ndarray) -> np.ndarray:
    """z mediano por variable en la ventana (n, p) respecto al estado normal → (p,)."""
    desv = np.where(desv == 0, 1.0, desv)
    return np.median((ventana - media) / desv, axis=0)


def desviacion_rms(ventana: np.ndarray, media: np.ndarray, desv: np.ndarray) -> np.ndarray:
    """Desviación RMS por variable en la ventana (n, p): sqrt(mean(z²)) → (p,). Detecta oscilación que la mediana oculta."""
    desv = np.where(desv == 0, 1.0, desv)
    return np.sqrt(np.mean(((ventana - media) / desv) ** 2, axis=0))


def ordenes_de_control(texto: str) -> list[str]:
    return [m.group(0).strip() for m in _ORDEN.finditer(texto)]


def verificar(diag: Diagnostico, *, tags: list[str], codigos: set[str], z: np.ndarray,
              umbral_z: float = UMBRAL_Z, z_rms: np.ndarray | None = None) -> Veredicto:
    """Verifica una salida del LLM. `tags[j]` corresponde a `z[j]`; `codigos` es el catálogo mostrado.
    `z_rms` (opcional) permite aceptar variables oscilantes cuya mediana no llega al umbral."""
    v = Veredicto("VERIFICADO", causas=list(diag.causas))
    desconocidas = [c for c in diag.causas if c not in codigos]
    if desconocidas:
        v.motivos.append(f"causa fuera del catálogo: {', '.join(desconocidas)}")
    ordenes = ordenes_de_control(diag.explicacion)
    if ordenes:
        v.motivos.append(f"orden de control en la explicación: {'; '.join(ordenes)}")

    indice = {t: j for j, t in enumerate(tags)}
    for ev in diag.evidencia:
        j = indice.get(ev.tag)
        if j is None:
            v.evidencia_rechazada.append((ev, "tag inexistente"))
        elif abs(z[j]) < umbral_z and z_rms is not None and z_rms[j] >= umbral_z:
            v.evidencia_oscilante.append((ev, f"oscila (dirección no verificable; RMS={z_rms[j]:.1f})"))
        elif abs(z[j]) < umbral_z:
            v.evidencia_rechazada.append((ev, f"sin desviación (|z|={abs(z[j]):.1f} < {umbral_z})"))
        elif (z[j] > 0) != (ev.direccion == "up"):
            v.evidencia_rechazada.append((ev, f"dirección contraria (z={z[j]:+.1f})"))
        else:
            v.evidencia_verificada.append(ev)

    if not v.evidencia_verificada and not v.evidencia_oscilante:
        v.motivos.append("ninguna evidencia respaldada por los datos")
    if v.motivos:
        v.estado = "BLOQUEADO"
    elif v.evidencia_rechazada:
        v.estado = "PARCIAL"
    return v


def votar(diags: list[Diagnostico]) -> tuple[Diagnostico, float]:
    """Causa principal por mayoría entre k muestras → (primera muestra con esa causa, fracción de acuerdo)."""
    if not diags:
        raise ValueError("no hay muestras que votar")
    principal, votos = Counter(d.causas[0] for d in diags).most_common(1)[0]
    elegido = next(d for d in diags if d.causas[0] == principal)
    return elegido, votos / len(diags)


def verificar_muestras(diags: list[Diagnostico], *, tags: list[str], codigos: set[str], z: np.ndarray,
                       umbral_z: float = UMBRAL_Z, umbral_acuerdo: float = UMBRAL_ACUERDO,
                       z_rms: np.ndarray | None = None) -> Veredicto:
    """Vota entre k muestras y verifica la elegida. Bajo acuerdo → INCIERTO, salvo que ya esté BLOQUEADO."""
    elegido, acuerdo = votar(diags)
    v = verificar(elegido, tags=tags, codigos=codigos, z=z, umbral_z=umbral_z, z_rms=z_rms)
    if len(diags) > 1:
        v.confianza = acuerdo
        if v.estado != "BLOQUEADO" and acuerdo < umbral_acuerdo:
            v.estado = "INCIERTO"
            v.motivos.append(f"acuerdo {acuerdo:.0%} < {umbral_acuerdo:.0%} entre {len(diags)} muestras")
    return v
