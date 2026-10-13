"""Diagnóstico de la salida degenerada de Gemma-4-31B-IT en AMD Token Factory (13-oct: "```/////…" hasta max_tokens).

Prueba 5 variantes, una llamada cada una (≈0,01 pts en total), y muestra el inicio de la respuesta y finish_reason.
Solo envía datos públicos de TEP disfrazados (IDV1, gemela nivel 2).
Uso:
    .venv/bin/python scripts/diagnosticar_token_factory.py
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval import pipeline  # noqa: E402
from llm.cliente import desde_env  # noqa: E402
from llm.parseo import parsear  # noqa: E402


def llamar(cliente, mensajes, **extra) -> None:
    cuerpo = {"model": cliente.modelo, "messages": mensajes, "max_tokens": 700} | extra
    t0 = time.time()
    r = requests.post(f"{cliente.base_url.rstrip('/')}/chat/completions", json=cuerpo, timeout=600,
                      headers={"Authorization": f"Bearer {cliente.api_key}"})
    if not r.ok:
        print(f"   HTTP {r.status_code}: {r.text[:200]}")
        return
    choice = r.json()["choices"][0]
    texto = choice["message"].get("content") or ""
    diag, error = parsear(texto)
    print(f"   {time.time() - t0:.1f} s · finish={choice.get('finish_reason')} · uso={r.json().get('usage', {}).get('completion_tokens')}")
    print(f"   JSON: {'OK ' + str(diag.causas) if diag else 'inválido'}")
    print(f"   inicio: {texto[:160]!r}")


def main() -> int:
    cliente = desde_env(prefijo="AMD_TF")
    caso = pipeline.preparar_caso(1, 2)
    fusionado = pipeline.preparar_caso(1, 2, fusionar_system=True)
    variantes = [
        ("1. saludo simple, sin temperature", [{"role": "user", "content": "Say hello in one sentence."}], {}),
        ("2. nuestro caso, sin temperature (default del servidor)", caso.mensajes, {}),
        ("3. nuestro caso, temperature 0.7", caso.mensajes, {"temperature": 0.7}),
        ("4. nuestro caso, temperature 0.7 + json_object", caso.mensajes,
         {"temperature": 0.7, "response_format": {"type": "json_object"}}),
        ("5. system fusionado en user, temperature 0.7", fusionado.mensajes, {"temperature": 0.7}),
    ]
    for nombre, mensajes, extra in variantes:
        print(nombre)
        llamar(cliente, mensajes, **extra)
        time.sleep(4)  # respeta 20 RPM
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
