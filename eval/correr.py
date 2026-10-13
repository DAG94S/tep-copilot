"""CLI de campañas: python3 -m eval.correr --campana NOMBRE --backend {simulado,AMD_VLLM,OLLAMA,GOOGLE} ..."""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from core import datos
from eval import pipeline
from llm import cliente as cliente_llm

RAIZ_RUNS = datos.RAIZ / "data" / "runs"
BACKENDS = ("simulado", "AMD_VLLM", "OLLAMA", "GOOGLE")


def _rango(texto: str) -> list[int]:
    if "-" in texto:
        a, b = texto.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(p) for p in texto.split(",")]


def _leer(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def correr(campana: str, backend: str, fallas: list[int], niveles: list[int], k: int = 1, temperatura: float = 0.0,
           semilla: int | None = 0, calibracion: str = "d00", estadistico: str = "t2", usar_esquema: bool = True,
           fusionar_system: bool = False, continuar: bool = False, raiz_runs: Path = RAIZ_RUNS,
           argumentos: dict | None = None, cliente=None) -> list[dict]:
    """Corre la campaña y devuelve todos los registros de la carpeta."""
    carpeta = raiz_runs / campana
    ruta_reg, ruta_man = carpeta / "registros.jsonl", carpeta / "manifiesto.json"
    if ruta_man.exists() and not continuar:
        raise SystemExit(f"la campaña {campana!r} ya existe en {carpeta}; usa --continuar o cambia el nombre")
    carpeta.mkdir(parents=True, exist_ok=True)
    hechos = {(r["falla"], r["nivel"]) for r in _leer(ruta_reg)}
    if backend != "simulado" and cliente is None:
        cliente = cliente_llm.desde_env(prefijo=backend)
    endpoint = urlparse(cliente.base_url).netloc if cliente is not None and hasattr(cliente, "base_url") else None
    manifiesto = {"campana": campana, "argumentos": argumentos or {}, "commit": pipeline.commit_git(),
                  "inicio": datetime.now(timezone.utc).isoformat(), "backend": backend,
                  "modelo": getattr(cliente, "modelo", "eco"), "host_endpoint": endpoint}
    if ruta_man.exists():
        previo = json.loads(ruta_man.read_text(encoding="utf-8"))
        manifiesto["inicio_original"] = previo.get("inicio_original", previo.get("inicio"))
    ruta_man.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")

    with ruta_reg.open("a", encoding="utf-8") as f:
        for falla in fallas:
            for nivel in niveles:
                if (falla, nivel) in hechos:
                    continue
                caso = pipeline.preparar_caso(falla, nivel, calibracion, estadistico, fusionar_system=fusionar_system)
                if not caso.detectado:
                    reg = pipeline.registro_no_detectado(caso)
                else:
                    c = pipeline.ClienteEco(caso) if backend == "simulado" else cliente
                    reg = pipeline.diagnosticar(caso, c, k, temperatura, semilla, usar_esquema)
                f.write(json.dumps(reg, ensure_ascii=False) + "\n")
                f.flush()
    manifiesto["fin"] = datetime.now(timezone.utc).isoformat()
    ruta_man.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    return _leer(ruta_reg)


def tabla(registros: list[dict]) -> str:
    estados = ("VERIFICADO", "PARCIAL", "BLOQUEADO", "INCIERTO", "INVALIDO", "ERROR_LLM")
    cab = ["nivel", "casos", "detect.", "top-1", "top-3"] + [e[:5] for e in estados] + ["rechaz."]
    filas = [cab]
    for nivel in sorted({r["nivel"] for r in registros}):
        rs = [r for r in registros if r["nivel"] == nivel]
        det = [r for r in rs if r["estado"] != "NO_DETECTADO"]
        cuenta = Counter(r["estado"] for r in det)
        afirm = sum(r.get("afirmaciones", 0) for r in det)
        rech = sum(len(r.get("evidencia_rechazada", [])) for r in det)
        filas.append([str(nivel), str(len(rs)), str(len(det)),
                      str(sum(bool(r.get("acierto_top1")) for r in det)),
                      str(sum(bool(r.get("acierto_top3")) for r in det))]
                     + [str(cuenta[e]) for e in estados] + [f"{rech / afirm:.0%}" if afirm else "-"])
    anchos = [max(len(f[i]) for f in filas) for i in range(len(cab))]
    return "\n".join("  ".join(c.rjust(a) for c, a in zip(f, anchos)) for f in filas)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="eval.correr", description=__doc__)
    p.add_argument("--campana", required=True)
    p.add_argument("--backend", required=True, choices=BACKENDS)
    p.add_argument("--fallas", default="1-15")
    p.add_argument("--niveles", default="0,1,2")
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--temperatura", type=float, default=0.0)
    p.add_argument("--semilla", type=int, default=0)
    p.add_argument("--calibracion", default="d00", choices=("d00", "ampliado"))
    p.add_argument("--estadistico", default="t2", choices=("t2", "spe", "cualquiera"))
    p.add_argument("--sin-esquema", action="store_true")
    p.add_argument("--fusionar-system", action="store_true")
    p.add_argument("--continuar", action="store_true")
    a = p.parse_args(argv)
    registros = correr(a.campana, a.backend, _rango(a.fallas), _rango(a.niveles), a.k, a.temperatura, a.semilla,
                       a.calibracion, a.estadistico, not a.sin_esquema, a.fusionar_system, a.continuar,
                       argumentos=vars(a))
    print(tabla(registros))


if __name__ == "__main__":
    main(sys.argv[1:])
