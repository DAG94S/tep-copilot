"""Grabación y replay de intercambios con Evolus (demo con GPU/red apagadas)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .cliente import ErrorEvolus


def _clave(metodo, ruta, peticion):
    return (metodo, ruta, json.dumps(peticion, sort_keys=True, ensure_ascii=False))


class Grabadora:
    """Añade una línea JSONL por intercambio. Nunca guarda cabeceras."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def registrar(self, metodo, ruta, peticion, status, respuesta, segundos):
        linea = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "metodo": metodo,
                 "ruta": ruta, "peticion": peticion, "status": status,
                 "respuesta": respuesta, "segundos": round(segundos, 3)}
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")


class ClienteReplay:
    """Misma interfaz pública que ClienteEvolus, sirviendo respuestas grabadas."""

    def __init__(self, ruta):
        self._datos = {}
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                if linea.strip():
                    d = json.loads(linea)
                    self._datos[_clave(d["metodo"], d["ruta"], d["peticion"])] = d
        self.creditos_consumidos = 0.0

    def _pedir(self, metodo, ruta, json=None):
        k = _clave(metodo, ruta, json)
        if k not in self._datos:
            raise KeyError(f"Sin grabación para {metodo} {ruta} con petición {k[2]}")
        d = self._datos[k]
        resp = d["respuesta"]
        if d["status"] >= 400:
            dd = resp if isinstance(resp, dict) else {}
            raise ErrorEvolus(f"Evolus {d['status']} (replay)", status=d["status"],
                              codigo=dd.get("errorCode"), traza=dd.get("traceId"),
                              cuerpo=resp)
        if isinstance(resp, dict) and isinstance(resp.get("creditsConsumed"), (int, float)):
            self.creditos_consumidos += resp["creditsConsumed"]
        return resp

    def herramientas(self):
        return self._pedir("GET", "/ai-tools")

    def ejecutar_herramienta(self, slug, texto, opciones=None):
        cuerpo = {"text": texto}
        if opciones:
            cuerpo["options"] = opciones
        return self._pedir("POST", f"/ai-tools/{slug}/run", json=cuerpo)

    def ejecutar_workflow(self, workflow_id, entradas):
        return self._pedir("POST", f"/workflows/{workflow_id}/execute", json=entradas)

    def estado_ejecucion(self, workflow_id, ejecucion_id):
        return self._pedir("GET", f"/workflows/{workflow_id}/executions/{ejecucion_id}")

    def esperar_ejecucion(self, workflow_id, ejecucion_id, timeout=120, intervalo=2):
        """En replay devuelve el último estado grabado (Completed/Failed)."""
        return self.estado_ejecucion(workflow_id, ejecucion_id)
