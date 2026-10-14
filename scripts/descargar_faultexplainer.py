"""Descarga los CSV fault0..fault20 de li-group/FaultExplainer (MIT) con commit fijado y registra/verifica SHA-256.

Dos copias en el repo original (ver docs/REPLICA_FAULTEXPLAINER.md, sección 1):
  backend/data/fault{i}.csv     ~190 KB: variables crudas (entrenamiento: model.py:250)
  frontend/public/fault{i}.csv  ~690 KB: variables + columnas t2_*, t2_stat y anomaly (evaluación: test_explain.py:35)

Uso:
    python3 scripts/descargar_faultexplainer.py             # descarga lo que falte y verifica
    python3 scripts/descargar_faultexplainer.py --registrar # añade a SHA256SUMS lo que aún no esté
"""
import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from descargar_datos import RAIZ, SUMS, leer_sumas, sha256  # noqa: E402

DESTINO = RAIZ / "data" / "raw" / "faultexplainer"
COMMIT = "2fcfee975a687c350f10909eeccd1ecdd60340be"
BASE = f"https://raw.githubusercontent.com/li-group/FaultExplainer/{COMMIT}"
# (ruta en el repo origen, subcarpeta local)
ORIGENES = (("backend/data", "backend_data"), ("frontend/public", "frontend_public"))
ARCHIVOS = [(f"{o}/fault{i}.csv", f"{d}/fault{i}.csv") for o, d in ORIGENES for i in range(21)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registrar", action="store_true", help="añade a SHA256SUMS los archivos nuevos")
    args = ap.parse_args()
    sumas = leer_sumas()
    nuevas, errores = [], []
    for origen, local in ARCHIVOS:
        destino = DESTINO / local
        destino.parent.mkdir(parents=True, exist_ok=True)
        clave = str(destino.relative_to(RAIZ))
        if not destino.exists():
            with urllib.request.urlopen(f"{BASE}/{origen}", timeout=60) as r:
                destino.write_bytes(r.read())
            print(f"descargado {clave}")
        digest = sha256(destino)
        if clave in sumas:
            if sumas[clave] != digest:
                errores.append(clave)
        else:
            nuevas.append((clave, digest))
    if errores:
        print("ERROR: SHA-256 distinto al registrado:", *errores, sep="\n  ")
        return 1
    if nuevas and args.registrar:
        with SUMS.open("a", encoding="utf-8") as f:
            for clave, digest in nuevas:
                f.write(f"{digest}  {clave}\n")
        print(f"registrados {len(nuevas)} archivos en SHA256SUMS")
    elif nuevas:
        print(f"{len(nuevas)} archivos sin registrar; usa --registrar")
    print(f"OK: {len(ARCHIVOS)} archivos en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
