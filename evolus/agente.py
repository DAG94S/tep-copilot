"""Cliente del agente de Evolus (API OpenAI-compatible; solo requests + stdlib).

SIN VERIFICAR (documentado en evolus.ai/developers, no probado): GET /models y
POST /chat/completions con model="<applicationId>:<agentId>". La temperatura y demás
parámetros los fija el agente, no se envían. La cabecera de respuesta X-Conversation-Id
se guarda en la grabación (dentro de la respuesta, clave `_conversation_id`);
la cabecera Authorization nunca se guarda.
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

from .cliente import BACKOFF, INTERVALO_MIN, ErrorEvolus, _leer_env
from .replay import _clave

BASE_AGENTE = "https://api.evolus.ai/v1"
TIMEOUT = 180  # s por petición (el agente puede tardar)


class ClienteAgente:
    def __init__(self, base, api_key, modelo=None, grabadora=None, sesion=None,
                 esperar=time.sleep):
        self.base = base.rstrip("/")
        self._api_key = api_key
        self.modelo = modelo or None
        self.grabadora = grabadora
        self.sesion = sesion or requests.Session()
        self.esperar = esperar
        self._ultimo = None

    @classmethod
    def desde_env(cls, ruta_env=".env", **kw):
        """Construye el cliente desde .env; las variables de entorno tienen prioridad."""
        env = _leer_env(ruta_env)
        def val(k, defecto=""):
            return os.environ.get(k) or env.get(k) or defecto
        key = val("EVOLUS_API_KEY")
        if not key:
            raise ErrorEvolus("Falta EVOLUS_API_KEY")
        return cls(val("EVOLUS_AGENT_BASE", BASE_AGENTE), key,
                   modelo=val("EVOLUS_AGENT_MODEL") or None, **kw)

    def _cabeceras(self):
        return {"Authorization": f"Bearer {self._api_key}",
                "Accept": "application/json", "Content-Type": "application/json"}

    def _throttle(self):
        if self._ultimo is not None:
            falta = INTERVALO_MIN - (time.monotonic() - self._ultimo)
            if falta > 0:
                self.esperar(falta)
        self._ultimo = time.monotonic()

    def _pedir(self, metodo, ruta, json=None):
        """Devuelve (cuerpo, id_conversacion, segundos). Reintenta 429/5xx con BACKOFF."""
        url = self.base + ruta
        for intento in range(len(BACKOFF) + 1):
            self._throttle()
            t0 = time.monotonic()
            resp = self.sesion.request(metodo, url, headers=self._cabeceras(),
                                       json=json, timeout=TIMEOUT)
            seg = time.monotonic() - t0
            status = resp.status_code
            if (status == 429 or status >= 500) and intento < len(BACKOFF):
                self.esperar(BACKOFF[intento])
                continue
            break
        try:
            cuerpo = resp.json()
        except Exception:
            cuerpo = {"texto": resp.text} if getattr(resp, "text", "") else None
        cabs = resp.headers or {}
        conv = cabs.get("X-Conversation-Id")
        grabado = cuerpo
        if conv and isinstance(cuerpo, dict):
            grabado = {**cuerpo, "_conversation_id": conv}
        if self.grabadora is not None:
            self.grabadora.registrar(metodo, ruta, json, status, grabado, seg)
        if status >= 400:
            d = cuerpo if isinstance(cuerpo, dict) else {}
            e = d.get("error")
            msg = e.get("message") if isinstance(e, dict) else (e or d.get("title"))
            raise ErrorEvolus(f"Evolus agente {status}: {msg or 'error'}",
                              status=status, codigo=d.get("errorCode"),
                              traza=d.get("traceId"), cuerpo=cuerpo)
        return cuerpo, conv, seg

    def modelos(self):
        cuerpo, _, _ = self._pedir("GET", "/models")
        return (cuerpo or {}).get("data", []) if isinstance(cuerpo, dict) else []

    def modelo_por_defecto(self):
        """EVOLUS_AGENT_MODEL si está fijado; si no, el único modelo de /models."""
        if self.modelo:
            return self.modelo
        ids = [m.get("id") for m in self.modelos()]
        if not ids:
            raise ErrorEvolus("/models no devolvió ningún agente; fija EVOLUS_AGENT_MODEL")
        if len(ids) > 1:
            raise ErrorEvolus("/models devolvió varios agentes (" + ", ".join(map(str, ids))
                              + "); fija EVOLUS_AGENT_MODEL=<applicationId>:<agentId>")
        self.modelo = ids[0]
        return self.modelo

    def chat(self, texto):
        """Envía un mensaje de usuario. Devuelve {texto, modelo, conversacion, segundos, uso}."""
        modelo = self.modelo_por_defecto()
        peticion = {"model": modelo, "messages": [{"role": "user", "content": str(texto)}]}
        cuerpo, conv, seg = self._pedir("POST", "/chat/completions", json=peticion)
        return _respuesta(cuerpo, modelo, conv, seg)


def _respuesta(cuerpo, modelo, conv, seg):
    try:
        contenido = cuerpo["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ErrorEvolus("Respuesta de /chat/completions sin choices[0].message.content",
                          cuerpo=cuerpo)
    # Evolus devuelve 200 con el fallo del modelo propio como texto del asistente (STATE.md, 14 oct).
    if re.match(r"Your model '[^']*' could not answer", contenido or ""):
        raise ErrorEvolus(f"El modelo del agente no respondió: {contenido}", status=200, cuerpo=cuerpo)
    return {"texto": contenido, "modelo": cuerpo.get("model") or modelo,
            "conversacion": conv, "segundos": round(seg, 3), "uso": cuerpo.get("usage")}


class AgenteReplay:
    """Misma interfaz (`modelos`, `modelo_por_defecto`, `chat`) sirviendo lo grabado."""

    def __init__(self, ruta, modelo=None):
        self._datos = {}
        self.modelo = modelo
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                if linea.strip():
                    d = json.loads(linea)
                    self._datos[_clave(d["metodo"], d["ruta"], d["peticion"])] = d

    def _get(self, metodo, ruta, peticion=None):
        k = _clave(metodo, ruta, peticion)
        if k not in self._datos:
            raise KeyError(f"Sin grabación para {metodo} {ruta} con petición {k[2]}")
        d = self._datos[k]
        if d["status"] >= 400:
            raise ErrorEvolus(f"Evolus agente {d['status']} (replay)", status=d["status"],
                              cuerpo=d["respuesta"])
        return d

    def modelos(self):
        return (self._get("GET", "/models")["respuesta"] or {}).get("data", [])

    def modelo_por_defecto(self):
        if self.modelo:
            return self.modelo
        ids = [m.get("id") for m in self.modelos()]
        if len(ids) != 1:
            raise ErrorEvolus("Replay: no hay un único modelo; indica `modelo`")
        self.modelo = ids[0]
        return self.modelo

    def chat(self, texto):
        modelo = self.modelo_por_defecto()
        d = self._get("POST", "/chat/completions",
                      {"model": modelo, "messages": [{"role": "user", "content": str(texto)}]})
        cuerpo = d["respuesta"]
        return _respuesta(cuerpo, modelo, cuerpo.get("_conversation_id"), d.get("segundos", 0.0))
