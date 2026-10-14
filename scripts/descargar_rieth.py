"""Descarga los archivos de ENTRENAMIENTO del dataset TEP de Rieth et al. (2017) desde Harvard Dataverse.

Fuente: Rieth, Amsel, Tran & Cook (2017), doi:10.7910/DVN/6C3JR1 (dominio público, CC0).
Solo baja TEP_FaultFree_Training.RData y TEP_Faulty_Training.RData (los *_Testing pesan ~4 GB en RAM
y no caben en WSL). Verifica el checksum que publica Dataverse (MD5) y registra el SHA-256 en SHA256SUMS.

Uso:
    python3 scripts/descargar_rieth.py
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "raw" / "rieth"
SUMS = RAIZ / "SHA256SUMS"
DOI = "doi:10.7910/DVN/6C3JR1"
API = f"https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId={DOI}"
ACCESO = "https://dataverse.harvard.edu/api/access/datafile/{id}"
CABECERAS = {"User-Agent": "tep-copilot/0.1 (descarga de datos publicos)"}  # Dataverse devuelve 403 sin User-Agent
ARCHIVOS = ["TEP_FaultFree_Training.RData", "TEP_Faulty_Training.RData"]


def abrir(url: str, timeout: int):
    return urllib.request.urlopen(urllib.request.Request(url, headers=CABECERAS), timeout=timeout)


def resumen(ruta: Path, algoritmo: str) -> str:
    h = hashlib.new(algoritmo)
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_sumas() -> dict:
    sumas = {}
    if SUMS.exists():
        for linea in SUMS.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                digest, _, nombre = linea.partition("  ")
                sumas[nombre] = digest
    return sumas


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    meta_ruta = DESTINO / "dataverse_metadata.json"
    if not meta_ruta.exists():
        with abrir(API, 60) as r:
            meta_ruta.write_bytes(r.read())
        print(f"descargado {meta_ruta.relative_to(RAIZ)}")
    meta = json.loads(meta_ruta.read_text(encoding="utf-8"))
    por_nombre = {f["dataFile"]["filename"]: f["dataFile"] for f in meta["data"]["latestVersion"]["files"]}

    sumas, nuevas, errores = leer_sumas(), [], []
    for nombre in ARCHIVOS:
        info = por_nombre[nombre]
        destino = DESTINO / nombre
        if not destino.exists():
            tmp = destino.with_suffix(".part")
            with abrir(ACCESO.format(id=info["id"]), 120) as r, tmp.open("wb") as f:
                while bloque := r.read(1 << 20):
                    f.write(bloque)
            tmp.rename(destino)
            print(f"descargado {destino.relative_to(RAIZ)}")
        if destino.stat().st_size != info["filesize"]:
            errores.append(f"{nombre}: tamaño {destino.stat().st_size} != {info['filesize']}")
        cs = info["checksum"]
        if resumen(destino, cs["type"].lower()) != cs["value"]:
            errores.append(f"{nombre}: {cs['type']} distinto del publicado por Dataverse")
        else:
            print(f"{cs['type']} verificado: {nombre}")
        clave = str(destino.relative_to(RAIZ))
        digest = resumen(destino, "sha256")
        if clave in sumas:
            if sumas[clave] != digest:
                errores.append(f"{clave}: SHA-256 distinto al registrado")
        else:
            nuevas.append((clave, digest))
    if errores:
        print("ERROR:", *errores, sep="\n  ")
        return 1
    if nuevas:
        with SUMS.open("a", encoding="utf-8") as f:
            for clave, digest in nuevas:
                f.write(f"{digest}  {clave}\n")
        print(f"registrados {len(nuevas)} archivos en SHA256SUMS")
    print(f"OK: {len(ARCHIVOS)} archivos en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
