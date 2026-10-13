"""Cliente REST mínimo de Evolus (solo requests + stdlib).

Verificado: GET /ai-tools y POST /ai-tools/{slug}/run.
SIN VERIFICAR (documentados, no probados): POST /workflows/{id}/execute y
GET /workflows/{id}/executions/{executionId} (estados Pending|Running|Completed|Failed).
Límite de la API: 60 peticiones/min.
"""
from __future__ import annotations

import json
import os
import time

import requests

BASE_POR_DEFECTO = "https://api.evolus.ai/api/v1"
INTERVALO_MIN = 1.0  # s entre peticiones (60/min)
BACKOFF = (1, 2, 4)


class ErrorEvolus(Exception):
    """Error devuelto por la API (o agotamiento de espera)."""

    def __init__(self, mensaje, status=None, codigo=None, traza=None, cuerpo=None):
        super().__init__(mensaje)
        self.status = status
        self.codigo = codigo
        self.traza = traza
        self.cuerpo = cuerpo


def _leer_env(ruta):
    """Parser mínimo de .env: KEY=VALOR, ignora comentarios y comillas."""
    datos = {}
    try:
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                datos[k.strip()] = v
    except FileNotFoundError:
        pass
    return datos


class ClienteEvolus:
    def __init__(self, base, api_key, app_id, grabadora=None, sesion=None,
                 esperar=time.sleep):
        self.base = base.rstrip("/")
        self._api_key = api_key
        self._app_id = app_id
        self.grabadora = grabadora
        self.sesion = sesion or requests.Session()
        self.esperar = esperar
        self.creditos_consumidos = 0.0
        self._ultimo = None

    @classmethod
    def desde_env(cls, ruta_env=".env", **kw):
        """Construye el cliente desde .env; las variables de entorno tienen prioridad."""
        env = _leer_env(ruta_env)
        def val(k, defecto=""):
            return os.environ.get(k) or env.get(k) or defecto
        key, app = val("EVOLUS_API_KEY"), val("EVOLUS_APPLICATION_ID")
        if not key or not app:
            raise ErrorEvolus("Faltan EVOLUS_API_KEY o EVOLUS_APPLICATION_ID")
        return cls(val("EVOLUS_API_BASE", BASE_POR_DEFECTO), key, app, **kw)

    def _cabeceras(self):
        return {"X-ApiKey": self._api_key, "X-Application-Id": self._app_id,
                "Accept": "application/json"}

    def _throttle(self):
        if self._ultimo is not None:
            falta = INTERVALO_MIN - (time.monotonic() - self._ultimo)
            if falta > 0:
                self.esperar(falta)
        self._ultimo = time.monotonic()

    def _pedir(self, metodo, ruta, json=None):
        """Petición central: throttle, reintentos en 429/5xx, errores problem+json."""
        url = self.base + ruta
        for intento in range(len(BACKOFF) + 1):
            self._throttle()
            t0 = time.monotonic()
            resp = self.sesion.request(metodo, url, headers=self._cabeceras(),
                                       json=json, timeout=60)
            seg = time.monotonic() - t0
            status = resp.status_code
            if status == 429 or status >= 500:
                if intento < len(BACKOFF):
                    self.esperar(BACKOFF[intento])
                    continue
            break
        ctype = resp.headers.get("Content-Type", "") if resp.headers else ""
        try:
            cuerpo = resp.json()
        except Exception:
            cuerpo = {"texto": resp.text} if getattr(resp, "text", "") else None
        if self.grabadora is not None:
            self.grabadora.registrar(metodo, ruta, json, status, cuerpo, seg)
        if status >= 400:
            d = cuerpo if isinstance(cuerpo, dict) else {}
            if "problem+json" not in ctype and not d:
                d = {}
            raise ErrorEvolus(
                f"Evolus {status}: {d.get('errorCode') or d.get('title') or 'error'}",
                status=status, codigo=d.get("errorCode"),
                traza=d.get("traceId"), cuerpo=cuerpo)
        if isinstance(cuerpo, dict):
            c = cuerpo.get("creditsConsumed")
            if isinstance(c, (int, float)):
                self.creditos_consumidos += c
        return cuerpo

    def herramientas(self):
        return self._pedir("GET", "/ai-tools")

    def ejecutar_herramienta(self, slug, texto, opciones=None):
        cuerpo = {"text": texto}
        if opciones:
            cuerpo["options"] = opciones
        return self._pedir("POST", f"/ai-tools/{slug}/run", json=cuerpo)

    def ejecutar_workflow(self, workflow_id, entradas):
        """Esquema del body SIN VERIFICAR: se pasa `entradas` tal cual."""
        return self._pedir("POST", f"/workflows/{workflow_id}/execute", json=entradas)

    def estado_ejecucion(self, workflow_id, ejecucion_id):
        """Esquema de respuesta SIN VERIFICAR (estado Pending|Running|Completed|Failed)."""
        return self._pedir("GET", f"/workflows/{workflow_id}/executions/{ejecucion_id}")

    def esperar_ejecucion(self, workflow_id, ejecucion_id, timeout=120, intervalo=2):
        """Sondea hasta Completed/Failed; si vence el timeout lanza ErrorEvolus."""
        t0 = time.monotonic()
        transcurrido = 0.0
        while True:
            r = self.estado_ejecucion(workflow_id, ejecucion_id)
            estado = r.get("status") or r.get("state") if isinstance(r, dict) else None
            if estado in ("Completed", "Failed"):
                return r
            if time.monotonic() - t0 >= timeout or transcurrido >= timeout:
                raise ErrorEvolus(f"Timeout esperando la ejecución {ejecucion_id}")
            self.esperar(intervalo)
            transcurrido += intervalo
