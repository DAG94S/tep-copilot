"""Prueba mínima de AMD Token Factory: UNA llamada con Gemma-4-31B-IT (IDV1, gemela nivel 2) y lectura del consumo.

Envía solo datos públicos de TEP (Braatz) disfrazados; no envía ningún secreto aparte de la key en la cabecera.
Uso:
    .venv/bin/python scripts/probar_token_factory.py
Requiere en .env: AMD_TF_ENDPOINT, AMD_TF_API_KEY, AMD_TF_MODEL (y opcional AMD_TF_TIMEOUT).
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval import pipeline  # noqa: E402
from llm.cliente import desde_env  # noqa: E402
from llm.parseo import parsear  # noqa: E402


def main() -> int:
    cliente = desde_env(prefijo="AMD_TF")
    caso = pipeline.preparar_caso(1, 2)
    t0 = time.time()
    resp = cliente.completar(caso.mensajes, max_tokens=1500)
    diag, error = parsear(resp.textos[0])
    print(f"{time.time() - t0:.1f} s · modelo {resp.modelo} · uso {resp.uso}")
    print("causas:", diag.causas if diag else f"JSON inválido: {error}")
    print("respuesta (inicio):", resp.textos[0][:300])
    base = cliente.base_url.rstrip("/")
    uso = requests.get(f"{base}/usage", headers={"Authorization": f"Bearer {cliente.api_key}"}, timeout=30)
    print("usage:", uso.status_code, uso.text[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
