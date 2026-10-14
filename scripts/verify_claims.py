"""Verifica la integridad de los datos (SHA256SUMS) y las afirmaciones cuantitativas (claims.json).

Cada afirmación de `claims.json` ({id, valor, fuente, descripcion[, reintentos]}) se RECALCULA con código desde su `fuente`
(JSONL pineado) y se compara con `valor`. Si trae `reintentos` (JSONL), cada INVALIDO de la fuente se sustituye por el reintento de su (falla, nivel). Nada se copia: si el dato cambia, la afirmación falla.

Uso:
    python3 scripts/verify_claims.py
Código de salida: 0 si todo cuadra; 1 si un hash difiere, falta un archivo versionado o una afirmación no coincide.
"""
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NO_VERSIONADO = "data/raw/"          # AGENTS.md regla 2: no se versiona; puede faltar en un clon


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_sumas(ruta: Path) -> dict:
    sumas = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.strip():
            digest, _, nombre = linea.partition("  ")
            sumas[nombre.strip()] = digest.strip()
    return sumas


def verificar_sumas(raiz: Path) -> list[tuple[str, str, str]]:
    """[(archivo, estado, detalle)] con estado OK | AUSENTE | FALLA. AUSENTE solo es tolerable bajo data/raw/."""
    sumas_path = raiz / "SHA256SUMS"
    if not sumas_path.exists():
        return [("SHA256SUMS", "FALLA", "no existe")]
    res = []
    for nombre, esperado in leer_sumas(sumas_path).items():
        ruta = raiz / nombre
        if not ruta.exists():
            if nombre.startswith(NO_VERSIONADO):
                res.append((nombre, "AUSENTE", "ausente (no versionado)"))
            else:
                res.append((nombre, "FALLA", "archivo versionado ausente"))
        elif sha256(ruta) != esperado:
            res.append((nombre, "FALLA", "hash distinto"))
        else:
            res.append((nombre, "OK", ""))
    return res


# ---------- métricas recalculadas desde registros ----------

def _fraccion(a: int, b: int) -> str:
    return f"{a}/{b}"


def _evaluables(regs: list[dict], nivel: int) -> list[dict]:
    return [r for r in regs if r["nivel"] == nivel and r["estado"] not in ("INVALIDO", "NO_DETECTADO")]


def _top(regs: list[dict], nivel: int, clave: str) -> str:
    ev = _evaluables(regs, nivel)
    return _fraccion(sum(bool(r[clave]) for r in ev), len(ev))


def _tasa_rechazo(regs: list[dict]) -> str:
    total = sum(r.get("afirmaciones", 0) for r in regs)
    rech = sum(len(r.get("evidencia_rechazada", [])) for r in regs)
    return f"{rech / total:.0%}" if total else "n/d"


def _lista(xs) -> str:
    return ",".join(str(x) for x in sorted(xs))


def _replica_top3(regs):
    det = [r for r in regs if r["detectada"]]
    return _fraccion(sum(bool(r.get("acierto_top3")) for r in det), len(det))


def combinar_reintentos(regs: list[dict], reintentos: list[dict]) -> list[dict]:
    """Sustituye cada registro INVALIDO por el reintento con la misma (falla, nivel); el resto no se toca."""
    por_caso = {(r["falla"], r["nivel"]): r for r in reintentos}
    return [por_caso.get((r["falla"], r["nivel"]), r) if r["estado"] == "INVALIDO" else r for r in regs]


METRICAS = {
    "replica_gemma_top3": _replica_top3,
    "replica_gemma_fallas": lambda regs: _lista(r["falla"] for r in regs if r["detectada"] and not r.get("acierto_top3")),
    "replica_gemma_no_detectadas": lambda regs: _lista(r["falla"] for r in regs if not r["detectada"]),
    **{f"campana_v2_n{n}_top1": (lambda regs, n=n: _top(regs, n, "acierto_top1")) for n in range(3)},
    **{f"campana_v2_n{n}_top3": (lambda regs, n=n: _top(regs, n, "acierto_top3")) for n in range(3)},
    **{f"combinado_n{n}_top1": (lambda regs, n=n: _top(regs, n, "acierto_top1")) for n in range(3)},
    **{f"combinado_n{n}_top3": (lambda regs, n=n: _top(regs, n, "acierto_top3")) for n in range(3)},
    "combinado_rechazo": _tasa_rechazo,
    "campana_v2_rechazo_antes": _tasa_rechazo,
    "campana_v2_rechazo_despues": _tasa_rechazo,
}


def leer_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def verificar_afirmaciones(raiz: Path, claims_path: Path) -> list[tuple[str, str, str, str]]:
    """[(id, estado, esperado, calculado)] con estado OK | FALLA."""
    res = []
    for c in json.loads(claims_path.read_text(encoding="utf-8")):
        esperado = str(c["valor"])
        f = METRICAS.get(c["id"])
        if f is None:
            res.append((c["id"], "FALLA", esperado, "id sin métrica definida"))
            continue
        fuente = raiz / c["fuente"]
        if not fuente.exists():
            res.append((c["id"], "FALLA", esperado, f"fuente ausente: {c['fuente']}"))
            continue
        try:
            regs = leer_jsonl(fuente)
            if c.get("reintentos"):
                rei = raiz / c["reintentos"]
                if not rei.exists():
                    res.append((c["id"], "FALLA", esperado, f"reintentos ausentes: {c['reintentos']}"))
                    continue
                regs = combinar_reintentos(regs, leer_jsonl(rei))
            calculado = f(regs)
        except (KeyError, ValueError, TypeError) as e:
            res.append((c["id"], "FALLA", esperado, f"error al calcular: {e!r}"))
            continue
        res.append((c["id"], "OK" if calculado == esperado else "FALLA", esperado, calculado))
    return res


def main(raiz: Path = RAIZ) -> int:
    fallos = 0
    print("== SHA256SUMS ==")
    sumas = verificar_sumas(raiz)
    for est in ("OK", "AUSENTE", "FALLA"):
        print(f"{est}: {sum(1 for s in sumas if s[1] == est)}")
    for nombre, est, det in sumas:
        if est != "OK":
            print(f"  {est:8} {nombre} {det}")
    fallos += sum(1 for s in sumas if s[1] == "FALLA")

    print("\n== Afirmaciones (claims.json) ==")
    claims = raiz / "claims.json"
    if not claims.exists():
        print("FALLA claims.json no existe")
        return 1
    print(f"{'id':32} {'estado':6} {'esperado':10} calculado")
    for id_, est, esp, calc in verificar_afirmaciones(raiz, claims):
        print(f"{id_:32} {est:6} {esp:10} {calc}")
        fallos += est == "FALLA"
    print("\nRESULTADO:", "TODO OK" if not fallos else f"{fallos} FALLA(S)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
