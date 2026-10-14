"""Mensaje (en inglés) para el agente de Evolus a partir de un registro de campaña.

Solo usa lo que el operador aprobó: nunca la etiqueta verdadera de la falla ni los
campos de acierto, ni el número de falla ni el nivel de disfraz
(en la planta real no existen y en la gemela destaparían el disfraz). Determinista: mismo registro, mismo texto.
"""
from __future__ import annotations


_ESTADO = {"VERIFICADO": "VERIFIED", "PARCIAL": "PARTIAL", "RECHAZADO": "REJECTED",
           "INVALIDO": "INVALID"}


def _ev(lista):
    return [f"- {e['tag']} ({e['direction']})" for e in lista or []]


def mensaje_aprobado(registro: dict) -> str:
    conf = registro.get("confianza")
    acuerdo = "not provided" if conf is None else f"{conf:.2f}"
    lineas = [
        "Approved diagnosis for documentation.",
        f"Alarm sample index: {registro['indice_alarma']}",
        f"Gate status: {_ESTADO.get(registro['estado'], registro['estado'])}",
        f"Agreement between samples: {acuerdo}",
        "Approved causes (in order): " + ", ".join(registro.get("causas") or ["none"]),
        "Verified evidence:",
        *(_ev(registro.get("evidencia_verificada")) or ["- none"]),
    ]
    rech = _ev(registro.get("evidencia_rechazada"))
    if rech:
        lineas += ["Rejected evidence (did NOT pass the gate):", *[f"{r} [rejected]" for r in rech]]
    osc = _ev(registro.get("evidencia_oscilante"))
    if osc:
        lineas += ["Oscillating evidence (direction not verifiable):", *[f"{o} [oscillating]" for o in osc]]
    return "\n".join(lineas)
