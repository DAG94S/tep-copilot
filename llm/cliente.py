"""Cliente para endpoints OpenAI-compatibles (vLLM en AMD, Ollama local) y un simulado para tests y replay sin GPU."""
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests


class ErrorLLM(Exception):
    def __init__(self, status: int | None, cuerpo: str):
        super().__init__(f"error del servidor LLM (status={status}): {cuerpo[:300]}")
        self.status = status
        self.cuerpo = cuerpo


@dataclass
class Respuesta:
    textos: list[str]
    modelo: str
    uso: dict = field(default_factory=dict)       # tokens prompt/completion sumados
    segundos: float = 0.0
    crudo: list[dict] = field(default_factory=list)


class ClienteLLM:
    REINTENTOS = 3
    ESPERAS_429 = (10, 20, 40, 60, 60, 60)  # s; total ~4 min antes de rendirse

    def __init__(self, base_url: str, modelo: str, api_key: str | None = None, timeout: float = 120.0,
                 extra_body: dict | None = None, esperar=time.sleep,
                 soporta_n: bool = True):
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.api_key = api_key
        self.timeout = timeout
        self.extra_body = extra_body or {}
        self.soporta_n = soporta_n  # Token Factory (Gemma) rechaza n>1: "Send n separate requests instead"
        self.esperar = esperar

    def _post(self, cuerpo: dict) -> dict:
        cabeceras = {"Content-Type": "application/json"}
        if self.api_key:
            cabeceras["Authorization"] = f"Bearer {self.api_key}"
        ultimo: ErrorLLM | None = None
        intento = n_429 = 0
        while True:
            espera_429 = None
            try:
                r = requests.post(f"{self.base_url}/chat/completions", json=cuerpo, headers=cabeceras,
                                  timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                ultimo = ErrorLLM(None, f"{type(e).__name__}: {e}")
            else:
                if r.status_code == 200:
                    return r.json()
                ultimo = ErrorLLM(r.status_code, r.text)
                if r.status_code == 429:
                    # Límites por minuto (Token Factory: 20 RPM y tokens/min, STATE 14 oct): esperas largas aparte.
                    if n_429 >= len(self.ESPERAS_429):
                        raise ultimo
                    espera_429 = self.ESPERAS_429[n_429]
                    try:
                        espera_429 = max(espera_429, float((getattr(r, "headers", None) or {}).get("Retry-After", 0)))
                    except (TypeError, ValueError):
                        pass
                    n_429 += 1
                elif r.status_code < 500:
                    raise ultimo
            if espera_429 is not None:
                self.esperar(espera_429)
                continue
            if intento >= self.REINTENTOS:
                raise ultimo
            self.esperar(2 ** intento)  # 1, 2, 4 s
            intento += 1

    def completar(self, mensajes: list[dict], n: int = 1, temperatura: float = 0.0, max_tokens: int = 800,
                  semilla: int | None = None, esquema: dict | None = None) -> Respuesta:
        t0 = time.perf_counter()
        textos, crudo, uso = [], [], {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0}
        while len(textos) < n:
            cuerpo = {"model": self.modelo, "messages": mensajes,
                      "temperature": temperatura, "max_tokens": max_tokens}
            if self.soporta_n and n - len(textos) > 1:
                cuerpo["n"] = n - len(textos)
            if semilla is not None:
                cuerpo["seed"] = semilla + len(textos)
            if esquema is not None:
                cuerpo["response_format"] = {"type": "json_schema",
                                             "json_schema": {"name": "diagnostico", "schema": esquema, "strict": True}}
            cuerpo |= self.extra_body
            datos = self._post(cuerpo)
            crudo.append(datos)
            u = datos.get("usage") or {}
            uso["prompt_tokens"] += u.get("prompt_tokens") or 0
            uso["completion_tokens"] += u.get("completion_tokens") or 0
            uso["reasoning_tokens"] += (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
            nuevos = [(c.get("message") or {}).get("content") or "" for c in datos.get("choices", [])]
            if not nuevos:
                raise ErrorLLM(200, f"respuesta sin choices: {str(datos)[:300]}")
            textos += nuevos[: n - len(textos)]
        return Respuesta(textos, self.modelo, uso, time.perf_counter() - t0, crudo)


def _leer_env(ruta: str) -> dict[str, str]:
    valores = {}
    p = Path(ruta)
    if p.exists():
        for linea in p.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip().strip("'\"")
    return valores


def desde_env(prefijo: str = "AMD_VLLM", ruta_env: str = ".env", **kwargs) -> ClienteLLM:
    """Construye el cliente desde {prefijo}_ENDPOINT/_API_KEY/_MODEL (entorno primero, luego .env).

    Opcionales: {prefijo}_EXTRA_BODY (JSON, p. ej. {"chat_template_kwargs": {"enable_thinking": false}}) y
    {prefijo}_TIMEOUT (segundos) y {prefijo}_SOPORTA_N (false si el servidor rechaza n>1). Los kwargs explícitos tienen prioridad.
    """
    archivo = _leer_env(ruta_env)

    def valor(sufijo: str) -> str | None:
        clave = f"{prefijo}_{sufijo}"
        return os.environ.get(clave) or archivo.get(clave) or None

    endpoint, modelo = valor("ENDPOINT"), valor("MODEL")
    if not endpoint or not modelo:
        raise KeyError(f"faltan {prefijo}_ENDPOINT y/o {prefijo}_MODEL en el entorno o en {ruta_env}")
    if valor("EXTRA_BODY") and "extra_body" not in kwargs:
        kwargs["extra_body"] = json.loads(valor("EXTRA_BODY"))
    if valor("SOPORTA_N") and "soporta_n" not in kwargs:
        kwargs["soporta_n"] = valor("SOPORTA_N").strip().lower() not in ("false", "0", "no")
    if valor("TIMEOUT") and "timeout" not in kwargs:
        kwargs["timeout"] = float(valor("TIMEOUT"))
    return ClienteLLM(endpoint, modelo, valor("API_KEY"), **kwargs)


class ClienteSimulado:
    """Misma interfaz que ClienteLLM; devuelve textos predefinidos en orden circular."""

    def __init__(self, textos: list[str], modelo: str = "simulado"):
        if not textos:
            raise ValueError("ClienteSimulado necesita al menos un texto")
        self.textos, self.modelo, self._i = list(textos), modelo, 0
        self.llamadas: list[list[dict]] = []

    def completar(self, mensajes: list[dict], n: int = 1, temperatura: float = 0.0, max_tokens: int = 800,
                  semilla: int | None = None, esquema: dict | None = None) -> Respuesta:
        self.llamadas.append(mensajes)
        salida = [self.textos[(self._i + k) % len(self.textos)] for k in range(n)]
        self._i = (self._i + n) % len(self.textos)
        return Respuesta(salida, self.modelo, {"prompt_tokens": 0, "completion_tokens": 0}, 0.0, [])
