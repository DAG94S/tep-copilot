"""Cliente para endpoints OpenAI-compatibles (vLLM en AMD, Ollama local) y un simulado para tests y replay sin GPU."""
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

    def __init__(self, base_url: str, modelo: str, api_key: str | None = None, timeout: float = 120.0,
                 extra_body: dict | None = None, esperar=time.sleep):
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.api_key = api_key
        self.timeout = timeout
        self.extra_body = extra_body or {}
        self.esperar = esperar

    def _post(self, cuerpo: dict) -> dict:
        cabeceras = {"Content-Type": "application/json"}
        if self.api_key:
            cabeceras["Authorization"] = f"Bearer {self.api_key}"
        ultimo: ErrorLLM | None = None
        for intento in range(self.REINTENTOS + 1):
            try:
                r = requests.post(f"{self.base_url}/chat/completions", json=cuerpo, headers=cabeceras,
                                  timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                ultimo = ErrorLLM(None, f"{type(e).__name__}: {e}")
            else:
                if r.status_code == 200:
                    return r.json()
                ultimo = ErrorLLM(r.status_code, r.text)
                if r.status_code != 429 and r.status_code < 500:
                    raise ultimo
            if intento < self.REINTENTOS:
                self.esperar(2 ** intento)  # 1, 2, 4 s
        raise ultimo

    def completar(self, mensajes: list[dict], n: int = 1, temperatura: float = 0.0, max_tokens: int = 800,
                  semilla: int | None = None, esquema: dict | None = None) -> Respuesta:
        t0 = time.perf_counter()
        textos, crudo, uso = [], [], {"prompt_tokens": 0, "completion_tokens": 0}
        while len(textos) < n:
            cuerpo = {"model": self.modelo, "messages": mensajes, "n": n - len(textos),
                      "temperature": temperatura, "max_tokens": max_tokens}
            if semilla is not None:
                cuerpo["seed"] = semilla + len(textos)
            if esquema is not None:
                cuerpo["response_format"] = {"type": "json_schema",
                                             "json_schema": {"name": "diagnostico", "schema": esquema, "strict": True}}
            cuerpo |= self.extra_body
            datos = self._post(cuerpo)
            crudo.append(datos)
            for k in uso:
                uso[k] += (datos.get("usage") or {}).get(k, 0)
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
    """Construye el cliente desde {prefijo}_ENDPOINT/_API_KEY/_MODEL (entorno primero, luego .env)."""
    archivo = _leer_env(ruta_env)

    def valor(sufijo: str) -> str | None:
        clave = f"{prefijo}_{sufijo}"
        return os.environ.get(clave) or archivo.get(clave) or None

    endpoint, modelo = valor("ENDPOINT"), valor("MODEL")
    if not endpoint or not modelo:
        raise KeyError(f"faltan {prefijo}_ENDPOINT y/o {prefijo}_MODEL en el entorno o en {ruta_env}")
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
