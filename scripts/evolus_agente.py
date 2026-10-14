"""Envía diagnósticos aprobados de una campaña al agente de Evolus y graba el resultado.

Uso:
  .venv/bin/python scripts/evolus_agente.py --campana tf_gemma31b_k5_v2 --casos 6:0,6:2 --dry-run
  .venv/bin/python scripts/evolus_agente.py --campana tf_gemma31b_k5_v2 --casos 6:0,6:2
Solo casos con estado VERIFICADO o PARCIAL. Lee EVOLUS_* de .env o del entorno.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from core.compuerta import ordenes_de_control
from evolus.agente import ClienteAgente
from evolus.cliente import ErrorEvolus
from evolus.mensaje import mensaje_aprobado
from evolus.replay import Grabadora

ESTADOS_OK = ("VERIFICADO", "PARCIAL")


def sha(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def cargar(campana):
    d = RAIZ / "data" / "runs" / campana
    f = d / "recompuertado.jsonl"
    if not f.exists():
        f = d / "registros.jsonl"
    regs = {}
    with open(f, encoding="utf-8") as fh:
        for linea in fh:
            if linea.strip():
                r = json.loads(linea)
                regs[(r["falla"], r["nivel"])] = r  # el último gana
    return f, regs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campana", required=True)
    ap.add_argument("--casos", required=True, help="falla:nivel separados por coma, ej. 6:0,6:2")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    archivo, regs = cargar(a.campana)
    casos = [tuple(int(x) for x in c.split(":")) for c in a.casos.split(",")]
    elegidos = []
    for c in casos:
        r = regs.get(c)
        if r is None:
            print(f"AVISO: caso {c[0]}:{c[1]} no está en {archivo.name}; se salta")
        elif r["estado"] not in ESTADOS_OK:
            print(f"AVISO: caso {c[0]}:{c[1]} tiene estado {r['estado']} (solo {'/'.join(ESTADOS_OK)}); se salta")
        else:
            elegidos.append(r)

    if a.dry_run:
        for r in elegidos:
            print(f"=== caso {r['falla']}:{r['nivel']} ===\n{mensaje_aprobado(r)}\n")
        return 0

    salida = Path(a.salida or RAIZ / "data" / "runs" / "evolus"
                  / f"agente_{datetime.now(timezone.utc):%Y-%m-%d}")
    salida.mkdir(parents=True, exist_ok=True)
    inicio = datetime.now(timezone.utc).isoformat()
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                                text=True, check=True).stdout.strip()
    except Exception:
        commit = None
    instr = RAIZ / "evolus" / "agente_instrucciones.md"
    manifiesto = {"argumentos": vars(a), "archivo_campana": str(archivo.relative_to(RAIZ)),
                  "commit": commit, "inicio_utc": inicio,
                  "sha256_instrucciones": hashlib.sha256(instr.read_bytes()).hexdigest()}

    cli = ClienteAgente.desde_env(str(RAIZ / ".env"), grabadora=Grabadora(salida / "intercambios.jsonl"))
    rc = 0
    with open(salida / "resultados.jsonl", "a", encoding="utf-8") as out:
        for r in elegidos:
            msg = mensaje_aprobado(r)
            try:
                resp = cli.chat(msg)
            except ErrorEvolus as e:
                print(f"ERROR caso {r['falla']}:{r['nivel']}: {e}")
                rc = 1
                continue
            linea = {"falla": r["falla"], "nivel": r["nivel"], "sha256_mensaje": sha(msg),
                     "mensaje": msg, "texto": resp["texto"],
                     "ordenes_de_control": ordenes_de_control(resp["texto"]),
                     "conversacion": resp["conversacion"], "segundos": resp["segundos"],
                     "modelo": resp["modelo"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            out.write(json.dumps(linea, ensure_ascii=False) + "\n")
            out.flush()
            print(f"caso {r['falla']}:{r['nivel']}: {len(resp['texto'])} caracteres, "
                  f"{len(linea['ordenes_de_control'])} órdenes de control, {resp['segundos']} s")
    manifiesto["fin_utc"] = datetime.now(timezone.utc).isoformat()
    (salida / "manifiesto.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False) + "\n",
                                            encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
