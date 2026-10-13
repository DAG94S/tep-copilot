"""Prueba de solo lectura de Evolus: GET /ai-tools (no gasta créditos).

Uso:  .venv/bin/python scripts/probar_evolus.py
Lee EVOLUS_* de .env o del entorno. No hace POST ni imprime la key.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolus.cliente import ClienteEvolus, ErrorEvolus


def main():
    try:
        herramientas = ClienteEvolus.desde_env().herramientas()
    except ErrorEvolus as e:
        print(f"Error: {e} status={e.status} codigo={e.codigo} traza={e.traza}")
        return 1
    for h in herramientas:
        opts = ", ".join(f"{o.get('key')}={o.get('defaultValue')}"
                         for o in h.get("options") or [])
        print(f"{h.get('slug')}  [{opts}]")
    print(f"Total: {len(herramientas)} herramientas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
