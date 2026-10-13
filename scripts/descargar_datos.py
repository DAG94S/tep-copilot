"""Descarga el espejo de datos TEP de Braatz (d00–d21) con commit fijado y registra/verifica SHA-256.

Fuente: https://github.com/jkitchin/tennessee-eastman-profbraatz (licencia tipo NCSA/UIUC, ver data/raw/braatz/LICENSE).
Datos originales: Russell, Chiang & Braatz (2000), simulación Fortran de Downs & Vogel (1993).

Uso:
    python3 scripts/descargar_datos.py            # descarga lo que falte y verifica contra SHA256SUMS
    python3 scripts/descargar_datos.py --registrar  # añade a SHA256SUMS los archivos que aún no estén
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "raw" / "braatz"
SUMS = RAIZ / "SHA256SUMS"
COMMIT = "9a6c8e5fcef4a2850778704e7793c87b0a187005"
BASE = f"https://raw.githubusercontent.com/jkitchin/tennessee-eastman-profbraatz/{COMMIT}"
ARCHIVOS = (
    ["LICENSE", "data/README.md"]
    + [f"data/d{i:02d}.dat" for i in range(22)]
    + [f"data/d{i:02d}_te.dat" for i in range(22)]
)


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_sumas() -> dict:
    if not SUMS.exists():
        return {}
    sumas = {}
    for linea in SUMS.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            digest, _, nombre = linea.partition("  ")
            sumas[nombre] = digest
    return sumas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registrar", action="store_true", help="añade a SHA256SUMS los archivos nuevos")
    args = ap.parse_args()

    DESTINO.mkdir(parents=True, exist_ok=True)
    sumas = leer_sumas()
    nuevas, errores = [], []

    for rel in ARCHIVOS:
        destino = DESTINO / Path(rel).name
        clave = str(destino.relative_to(RAIZ))
        if not destino.exists():
            with urllib.request.urlopen(f"{BASE}/{rel}", timeout=60) as r:
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
