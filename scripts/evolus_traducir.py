"""Traduce con el AI Tool «translate» de Evolus los documentos que redactó el agente (3.er bloque de Evolus) y graba.

Toma `resultados.jsonl` de una corrida del agente, recorta el preámbulo (desde "## Work order") y envía el texto a
POST /api/v1/ai-tools/translate/run. Nada de la traducción se escribe a mano; se graba petición y respuesta.

Uso:
  .venv/bin/python scripts/evolus_traducir.py --agente data/runs/evolus/agente_2026-10-16_biblioteca_qwen_v2 --destino it
Lee EVOLUS_* de .env o del entorno.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from evolus.cliente import ClienteEvolus, ErrorEvolus
from evolus.replay import Grabadora


def documento(texto: str) -> str:
    """El documento sin el preámbulo del agente ("I'll start by searching…")."""
    i = texto.find("## Work order")
    return texto[i:] if i >= 0 else texto.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agente", required=True, help="carpeta de una corrida de scripts/evolus_agente.py")
    ap.add_argument("--destino", default="it", help="código de idioma de destino (it, es, …)")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()

    origen = RAIZ / a.agente / "resultados.jsonl"
    regs = [json.loads(l) for l in origen.read_text(encoding="utf-8").splitlines() if l.strip()]
    salida = Path(a.salida or RAIZ / "data" / "runs" / "evolus"
                  / f"traduccion_{a.destino}_{datetime.now(timezone.utc):%Y-%m-%d}")
    salida.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    manifiesto = {"argumentos": vars(a), "origen": str(origen.relative_to(RAIZ)), "commit": commit,
                  "inicio_utc": datetime.now(timezone.utc).isoformat()}

    cli = ClienteEvolus.desde_env(str(RAIZ / ".env"), grabadora=Grabadora(salida / "intercambios.jsonl"))
    rc = 0
    with open(salida / "resultados.jsonl", "a", encoding="utf-8") as out:
        for r in regs:
            doc = documento(r["texto"])
            try:
                resp = cli.ejecutar_herramienta("translate", doc, {"target": a.destino, "style": "natural"})
            except ErrorEvolus as e:
                print(f"ERROR caso {r['falla']}:{r['nivel']}: {e}")
                rc = 1
                continue
            linea = {"falla": r["falla"], "nivel": r["nivel"], "destino": a.destino,
                     "sha256_origen": hashlib.sha256(doc.encode("utf-8")).hexdigest(), "texto_origen": doc,
                     "traduccion": resp.get("output"), "truncado": resp.get("truncated"),
                     "creditos": resp.get("creditsConsumed"),
                     "ts": datetime.now(timezone.utc).isoformat()}
            out.write(json.dumps(linea, ensure_ascii=False) + "\n")
            out.flush()
            print(f"caso {r['falla']}:{r['nivel']}: {len(doc)} → {len(linea['traduccion'] or '')} caracteres, "
                  f"créditos {linea['creditos']}, truncado {linea['truncado']}")
    manifiesto["fin_utc"] = datetime.now(timezone.utc).isoformat()
    manifiesto["creditos_totales"] = cli.creditos_consumidos
    (salida / "manifiesto.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
