"""Re-aplica la compuerta vigente a una campaña grabada, sin llamar al LLM.

Relee `registros.jsonl`, reconstruye cada caso con `pipeline.preparar_caso`, re-parsea los `textos` guardados y escribe
`recompuertado.jsonl` junto al original (que no se toca). Imprime la tabla antes/después por nivel.

Uso: python3 -m eval.recompuertar --campana NOMBRE [--raiz data/runs]
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from core import compuerta, datos
from eval import pipeline
from llm.parseo import parsear

ESTADOS = ["VERIFICADO", "PARCIAL", "BLOQUEADO", "INCIERTO", "INVALIDO", "NO_DETECTADO"]


def recompuertar_registro(reg: dict, caso) -> dict:
    """Devuelve una copia de `reg` con la compuerta nueva aplicada a sus textos guardados."""
    textos = reg.get("textos")
    if not textos or not caso.detectado:
        return dict(reg)
    validos = [d for d, _ in (parsear(t) for t in textos) if d is not None]
    if not validos:
        return dict(reg)
    v = compuerta.verificar_muestras(validos, tags=caso.tags, codigos=set(caso.codigos), z=caso.z, z_rms=caso.z_rms)
    idv = [caso.vista.idv.get(c) for c in v.causas]
    return dict(reg) | {
        "estado": v.estado, "motivos": v.motivos, "confianza": v.confianza, "causas": v.causas,
        "idv_predichos": idv,
        "evidencia_verificada": [{"tag": e.tag, "direction": e.direccion} for e in v.evidencia_verificada],
        "evidencia_rechazada": [{"tag": e.tag, "direction": e.direccion, "motivo": m}
                                for e, m in v.evidencia_rechazada],
        "evidencia_oscilante": [{"tag": e.tag, "direction": e.direccion, "motivo": m}
                                for e, m in v.evidencia_oscilante],
        "acierto_top1": idv[:1] == [reg["falla"]], "acierto_top3": reg["falla"] in idv[:3],
        "afirmaciones": v.afirmaciones,
    }


def _tasa(regs: list[dict]) -> str:
    total = sum(r.get("afirmaciones", 0) for r in regs)
    rech = sum(len(r.get("evidencia_rechazada", [])) for r in regs)
    return f"{rech}/{total} ({rech / total:.0%})" if total else "n/d"


def tabla(antes: list[dict], despues: list[dict]) -> str:
    niveles = sorted({r["nivel"] for r in antes})
    lineas = []
    for etiqueta, regs in (("ANTES", antes), ("DESPUÉS", despues)):
        lineas.append(f"\n{etiqueta}")
        lineas.append("nivel | " + " | ".join(ESTADOS) + " | rechazadas")
        for n in niveles:
            sub = [r for r in regs if r["nivel"] == n]
            c = Counter(r["estado"] for r in sub)
            lineas.append(f"{n} | " + " | ".join(str(c.get(e, 0)) for e in ESTADOS) + f" | {_tasa(sub)}")
        lineas.append("todos | " + " | ".join(str(Counter(r["estado"] for r in regs).get(e, 0)) for e in ESTADOS)
                      + f" | {_tasa(regs)}")
    osc = sum(len(r.get("evidencia_oscilante", [])) for r in despues)
    lineas.append(f"\nafirmaciones aceptadas como oscilantes: {osc}")
    return "\n".join(lineas)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campana", required=True)
    ap.add_argument("--raiz", default="data/runs")
    a = ap.parse_args(argv)
    raiz = Path(a.raiz)
    if not raiz.is_absolute():
        raiz = datos.RAIZ / raiz
    carpeta = raiz / a.campana
    antes = [json.loads(l) for l in (carpeta / "registros.jsonl").read_text().splitlines() if l.strip()]
    man_path = carpeta / "manifiesto.json"
    fusionar = False
    if man_path.exists():
        fusionar = bool(json.loads(man_path.read_text()).get("argumentos", {}).get("fusionar_system", False))
    despues = []
    for reg in antes:
        if reg.get("textos") and reg.get("estado") != "NO_DETECTADO":
            caso = pipeline.preparar_caso(reg["falla"], reg["nivel"], reg.get("calibracion", "d00"),
                                          reg.get("estadistico", "t2"), fusionar_system=fusionar)
            despues.append(recompuertar_registro(reg, caso))
        else:
            despues.append(dict(reg))
    salida = carpeta / "recompuertado.jsonl"
    salida.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in despues))
    print(tabla(antes, despues))
    print(f"\nEscrito: {salida}")


if __name__ == "__main__":
    main()
