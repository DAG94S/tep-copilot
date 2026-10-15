"""Extracción de las causas propuestas en las respuestas en PROSA de la réplica FaultExplainer, con un LLM anotador.

Por qué: el prompt de FaultExplainer pide texto libre y ellos puntuaron a mano. `replica_faultexplainer.extraer_idv`
toma los 3 primeros IDV por orden de aparición, lo que solo funciona con respuestas breves (Gemma). Con respuestas
largas que repasan y descartan causas (Qwen) falla. Aquí un modelo distinto del evaluado (por defecto
DeepSeek-V4-Flash) lee cada muestra y devuelve las causas que el autor PROPONE y si llegó a concluir.
El mismo anotador se aplica a todas las réplicas (simetría) y se valida contra `extraer_idv` donde este no es ambiguo.

No toca `registros.jsonl`: escribe `extraccion_llm.jsonl` y `extraccion_manifiesto.json` en la carpeta de la campaña.
CLI: python3 -m eval.extraer_causas_llm --campana tf_replica_fe_k5 [--modelo DeepSeek-V4-Flash]
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone

from eval.correr import RAIZ_RUNS
from llm import cliente as cliente_llm
from llm import parseo

CATALOGO = """1. IDV(1) A/C Feed Ratio, B Composition Constant (Stream 4) & Step
2. IDV(2) B Composition, A/C Ratio Constant (Stream 4) & Step
3. IDV(3) D Feed Temperature (Stream 2) & Step
4. IDV(4) Reactor Cooling Water Inlet Temperature & Step
5. IDV(5) Condenser Cooling Water Inlet Temperature & Step
6. IDV(6) A Feed Loss (Stream 1) & Step
7. IDV(7) C Header Pressure Loss - Reduced Availability (Stream 4) & Step
8. IDV(8) A, B, C Feed Composition (Stream 4) & Random Variation
9. IDV(9) D Feed Temperature (Stream 2) & Random Variation
10. IDV(10) C Feed Temperature (Stream 4) & Random Variation
11. IDV(11) Reactor Cooling Water Inlet Temperature & Random Variation
12. IDV(12) Condenser Cooling Water Inlet Temperature & Random Variation
13. IDV(13) Reaction Kinetics & Slow Drift
14. IDV(14) Reactor Cooling Water Valve & Sticking
15. IDV(15) Condenser Cooling Water Valve & Sticking"""   # third_party/faultexplainer/backend/prompts.py, "Available Root Causes"

PROMPT = f"""You are a strict annotator. You will read a free-text answer written by an engineer who diagnosed a fault in the Tennessee Eastman Process. The engineer was asked to identify up to THREE most likely root causes from this catalog:

{CATALOGO}

Report the catalog causes that the engineer PROPOSES as candidate root causes in the answer, in the engineer's order of preference (most likely first).
- Do NOT include causes the engineer only mentions while searching and then rejects, dismisses, or says cannot explain the data.
- Map names and aliases to catalog numbers (e.g. "A Feed Loss" is 6).
- If more than three are proposed, keep the first three in the engineer's ranking.
- If the answer is cut off before the engineer makes clear which causes are proposed, set "concluded" to false and list only the causes clearly proposed so far (possibly none).

Return only JSON: {{"proposed": [catalog numbers], "concluded": true or false}}"""


def validar(obj: dict) -> tuple[list[int], bool]:
    """(propuestas, concluyó) desde la salida del anotador; ValueError si no cumple el formato."""
    if not isinstance(obj, dict) or "proposed" not in obj or "concluded" not in obj:
        raise ValueError(f"faltan claves: {obj!r}")
    vistos = []
    for x in obj["proposed"]:
        n = int(x)
        if not 1 <= n <= 15:
            raise ValueError(f"causa fuera del catálogo: {x!r}")
        if n not in vistos:
            vistos.append(n)
    return vistos[:3], bool(obj["concluded"])


def puntuar(falla: int, propuestas: list[list[int]]) -> dict:
    """Misma regla que replica_faultexplainer.puntuar: mayoría estricta de las k muestras."""
    top3 = [falla in p for p in propuestas]
    top1 = [bool(p) and p[0] == falla for p in propuestas]
    return {"aciertos_muestras": sum(top3), "acierto_top3": sum(top3) > len(propuestas) / 2,
            "acierto_top1": sum(top1) > len(propuestas) / 2}


def anotar(cliente, texto: str, max_tokens: int, intentos: int = 3) -> dict:
    """Una muestra: hasta `intentos` llamadas hasta obtener JSON válido."""
    ultimo = None
    for _ in range(intentos):
        r = cliente.completar([{"role": "system", "content": PROMPT},
                               {"role": "user", "content": f"Answer to annotate:\n<<<\n{texto}\n>>>"}],
                              n=1, temperatura=0.0, max_tokens=max_tokens)
        bruto = r.textos[0]
        try:
            prop, concl = validar(parseo.extraer_json(bruto))
            return {"propuestas": prop, "concluyo": concl, "bruto": bruto, "uso": r.uso}
        except (ValueError, TypeError) as e:
            ultimo = f"{e!r}: {bruto[:200]!r}"
    return {"propuestas": [], "concluyo": False, "bruto": None, "error": ultimo, "uso": {}}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--campana", required=True)
    p.add_argument("--modelo", default="DeepSeek-V4-Flash")
    p.add_argument("--max-tokens", type=int, default=400)
    a = p.parse_args()

    carpeta = RAIZ_RUNS / a.campana
    regs = [json.loads(l) for l in (carpeta / "registros.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    cliente = cliente_llm.desde_env(prefijo="AMD_TF", soporta_n=False,
                                    extra_body={"response_format": {"type": "json_object"}})
    cliente.modelo = a.modelo
    inicio = datetime.now(timezone.utc).isoformat()
    salida, uso = [], {"prompt_tokens": 0, "completion_tokens": 0}
    for r in regs:
        if not r.get("muestras"):
            continue
        muestras = []
        for m in r["muestras"]:
            an = anotar(cliente, m["texto"], a.max_tokens)
            for k in uso:
                uso[k] += an["uso"].get(k, 0) or 0
            muestras.append({"propuestas": an["propuestas"], "concluyo": an["concluyo"], "regex": m["extraidos"],
                             "regex_ambiguo": m["requiere_revision_alias"], "bruto": an["bruto"],
                             **({"error": an["error"]} if "error" in an else {})})
        fila = {"falla": r["falla"], **puntuar(r["falla"], [m["propuestas"] for m in muestras]),
                "sin_conclusion": sum(not m["concluyo"] for m in muestras),
                "errores": sum("error" in m for m in muestras), "muestras": muestras}
        salida.append(fila)
        print(f"IDV{r['falla']:2d} top3={fila['acierto_top3']} ({fila['aciertos_muestras']}/{len(muestras)}) "
              f"sin_conclusion={fila['sin_conclusion']} errores={fila['errores']}", flush=True)

    (carpeta / "extraccion_llm.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in salida),
                                                  encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (carpeta / "extraccion_manifiesto.json").write_text(json.dumps({
        "campana": a.campana, "anotador": a.modelo, "temperatura": 0.0, "max_tokens": a.max_tokens,
        "sha256_prompt": hashlib.sha256(PROMPT.encode()).hexdigest(), "commit": commit,
        "inicio": inicio, "fin": datetime.now(timezone.utc).isoformat(), "uso": uso}, ensure_ascii=False, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
