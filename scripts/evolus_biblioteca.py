"""Sube documentos a una Knowledge Library de Evolus y/o lista su estado de indexación.

Uso:
  .venv/bin/python scripts/evolus_biblioteca.py --library-id <id> --subir knowledge/*.md --dry-run
  .venv/bin/python scripts/evolus_biblioteca.py --library-id <id> --subir knowledge/tep_*.md
  .venv/bin/python scripts/evolus_biblioteca.py --library-id <id> --listar
Graba data/runs/evolus/biblioteca_<fecha>/intercambios.jsonl (sin cabeceras) y manifiesto.json con sha256.
Nunca imprime ni guarda las keys. Los READMEs no se suben: pasa solo los documentos.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from evolus.biblioteca import (formatos_documento, listar_documentos, sha256_archivo,
                               subir_documento)
from evolus.cliente import ClienteEvolus, ErrorEvolus
from evolus.replay import Grabadora


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library-id", required=True)
    ap.add_argument("--subir", nargs="*", default=[], help="archivos a subir")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--formatos", action="store_true")
    ap.add_argument("--idioma", default="en")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--dry-run", action="store_true", help="sin red: muestra qué se subiría")
    a = ap.parse_args(argv)

    archivos = [Path(x) for x in a.subir]
    for f in archivos:
        if not f.is_file():
            print(f"ERROR: no existe {f}")
            return 2
    manifiesto = [{"archivo": f.name, "bytes": f.stat().st_size, "sha256": sha256_archivo(f)}
                  for f in archivos]

    if a.dry_run:
        for m in manifiesto:
            print(f"[dry-run] POST /memories/{a.library_id}/documents?language={a.idioma}  "
                  f"{m['archivo']} ({m['bytes']} B) sha256={m['sha256'][:12]}")
        if a.listar:
            print(f"[dry-run] GET /memories/{a.library_id}/documents")
        return 0

    fecha = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    carpeta = Path(a.salida) if a.salida else RAIZ / "data" / "runs" / "evolus" / f"biblioteca_{fecha}"
    cliente = ClienteEvolus.desde_env(str(RAIZ / ".env"), grabadora=Grabadora(carpeta / "intercambios.jsonl"))
    resultados = []
    try:
        for f, m in zip(archivos, manifiesto):
            r = subir_documento(cliente, a.library_id, f, a.idioma)
            resultados.append({**m, "respuesta": r})
            print(f"subido {f.name}")
        if a.formatos:
            print(json.dumps(formatos_documento(cliente), indent=2, ensure_ascii=False))
        if a.listar:
            print(json.dumps(listar_documentos(cliente, a.library_id), indent=2, ensure_ascii=False))
    except ErrorEvolus as e:
        print(f"ERROR Evolus: {e} (status={e.status}, codigo={e.codigo})")
        return 1
    finally:
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "manifiesto.json").write_text(json.dumps(
            {"library_id": a.library_id, "fecha": fecha, "documentos": resultados or manifiesto},
            indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
