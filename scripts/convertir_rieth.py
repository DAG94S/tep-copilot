"""Convierte los binarios extraídos de Rieth et al. (2017) a .npz float32 (20 simulaciones por falla).

Paso previo (R, base): /usr/bin/time -v Rscript scripts/extraer_rieth.R  → data/raw/rieth/extraido/*.bin
(pyreadr necesita >5,5 GB de RAM con Faulty_Training; R pica en ~3,1 GB). Cada .bin son
20*500*52 doubles little-endian: simulaciones 1..20, muestras 1..500, columnas xmeas_1..41, xmv_1..11.
Salida en data/processed/rieth/: faulty_train_f{01..20}.npz y faultfree_train.npz, cada uno con
  x    (20, 500, 52) float32 (mismo orden de columnas que core.datos.cargar)
  runs (20,) ids de simulationRun (1..20)
Rieth trae las fallas 1..20 (no la 21). Registra los SHA-256 en SHA256SUMS.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "raw" / "rieth" / "extraido"
SALIDA = RAIZ / "data" / "processed" / "rieth"
SUMS = RAIZ / "SHA256SUMS"
FORMA = (20, 500, 52)


def leer_bin(ruta: Path) -> np.ndarray:
    x = np.fromfile(ruta, dtype="<f8")
    if x.size != np.prod(FORMA) or not np.isfinite(x).all():
        raise ValueError(f"{ruta.name}: tamaño {x.size} o valores no finitos")
    return x.reshape(FORMA).astype(np.float32)


def registrar(rutas: list[Path]) -> None:
    previas = {l.partition("  ")[2] for l in SUMS.read_text(encoding="utf-8").splitlines() if l.strip()}
    with SUMS.open("a", encoding="utf-8") as f:
        for r in rutas:
            clave = str(r.relative_to(RAIZ))
            if clave not in previas:
                f.write(f"{hashlib.sha256(r.read_bytes()).hexdigest()}  {clave}\n")


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    pares = [("faultfree_train.bin", "faultfree_train.npz")] + [
        (f"faulty_train_f{f:02d}.bin", f"faulty_train_f{f:02d}.npz") for f in range(1, 21)]
    salidas = []
    for entrada, salida in pares:
        destino = SALIDA / salida
        np.savez_compressed(destino, x=leer_bin(ENTRADA / entrada), runs=np.arange(1, 21))
        salidas.append(destino)
    registrar(salidas + [RAIZ / "data" / "raw" / "rieth" / "dataverse_metadata.json"])
    print(f"OK: {len(salidas)} archivos en {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
