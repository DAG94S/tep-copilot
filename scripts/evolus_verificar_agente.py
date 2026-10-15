"""Verifica (solo GET) que el agente «TEP Shift Copilot» de Evolus tiene el prompt de evolus/agente_instrucciones.md.

Uso: .venv/bin/python scripts/evolus_verificar_agente.py
No imprime keys. Sale con 0 si coincide, 1 si no coincide, 2 si no se encuentra o falla la API.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from evolus.cliente import ClienteEvolus, ErrorEvolus

NOMBRE = "TEP Shift Copilot"


def prompt_esperado(texto):
    """Bloque bajo la primera línea `---`."""
    return normalizar(texto.split("\n---\n", 1)[1])


def normalizar(t):
    return "\n".join(l.rstrip() for l in t.strip().splitlines())


def _lista(cuerpo):
    if isinstance(cuerpo, list):
        return cuerpo
    if isinstance(cuerpo, dict):
        for k in ("items", "data", "agents", "results"):
            if isinstance(cuerpo.get(k), list):
                return cuerpo[k]
    return []


def _buscar(d, claves):
    """Primer valor de alguna de `claves` en el dict, buscando también un nivel anidado."""
    for k in claves:
        if d.get(k) not in (None, ""):
            return d[k]
    for v in d.values():
        if isinstance(v, dict):
            for k in claves:
                if v.get(k) not in (None, ""):
                    return v[k]
    return None


def comparar(agentes, esperado):
    """Devuelve (veredicto, agente, modelo, prompt_agente)."""
    ag = next((a for a in agentes if isinstance(a, dict)
               and str(a.get("name") or a.get("title") or "").strip() == NOMBRE), None)
    if ag is None:
        return "no encontrado", None, None, None
    prompt = _buscar(ag, ("prompt", "instructions", "systemPrompt"))
    modelo = _buscar(ag, ("modelDisplayName", "modelKey", "model", "modelName"))
    if prompt is None:
        return "sin prompt en la respuesta", ag, modelo, None
    return ("coincide" if normalizar(str(prompt)) == esperado else "no coincide"), ag, modelo, str(prompt)


def main(cliente=None):
    esperado = prompt_esperado((RAIZ / "evolus" / "agente_instrucciones.md").read_text(encoding="utf-8"))
    try:
        cliente = cliente or ClienteEvolus.desde_env(str(RAIZ / ".env"))
        agentes = _lista(cliente._pedir("GET", "/agents"))
    except ErrorEvolus as e:
        print(f"ERROR Evolus: {e} (status={e.status}, codigo={e.codigo})")
        return 2
    veredicto, ag, modelo, prompt = comparar(agentes, esperado)
    print(f"agentes listados: {len(agentes)}")
    if ag is None:
        print(f"'{NOMBRE}': no encontrado")
        return 2
    print(f"'{NOMBRE}': {veredicto}")
    print(f"modelo configurado: {json.dumps(modelo, ensure_ascii=False) if modelo is not None else 'no viene en la respuesta'}")
    for k in ("modelKey", "modelState", "modelParameters", "vectorStoreId"):
        print(f"{k}: {json.dumps(ag.get(k), ensure_ascii=False)}")
    if prompt is not None:
        print(f"longitud prompt agente={len(normalizar(prompt))} esperado={len(esperado)}")
    return {"coincide": 0, "no coincide": 1}.get(veredicto, 2)


if __name__ == "__main__":
    sys.exit(main())
