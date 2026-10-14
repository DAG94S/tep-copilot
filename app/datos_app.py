"""Funciones puras de la demo (sin Streamlit): leen las corridas grabadas y agregan métricas.

Nada de lo que muestra la UI se escribe a mano: todo sale de `data/runs/` (JSONL/manifiesto), de `SHA256SUMS`
o de un cálculo determinista de `core/` sobre los datos locales.
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
RUNS = RAIZ / "data" / "runs"
CAMPANA_PRINCIPAL = "tf_gemma31b_k5_v2"
CAMPANA_REPLICA = "tf_replica_fe_k5"
ESTADOS = ["VERIFICADO", "PARCIAL", "BLOQUEADO", "INCIERTO", "INVALIDO", "NO_DETECTADO"]
VISTAS = {"Original TEP": 0, "Disguised twin (level 1: anonymous tags)": 1, "Disguised twin (level 2: full disguise)": 2}


# ---------- lectura ----------
def leer_jsonl(ruta: Path) -> list[dict]:
    """Registros de un JSONL; lista vacía si el archivo no existe."""
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def leer_json(ruta: Path) -> dict:
    ruta = Path(ruta)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def archivo_efectivo(carpeta: Path) -> Path:
    """`recompuertado.jsonl` si existe (compuerta vigente); si no, `registros.jsonl`."""
    rec = Path(carpeta) / "recompuertado.jsonl"
    return rec if rec.exists() else Path(carpeta) / "registros.jsonl"


def sha256_registrado(ruta: Path, raiz: Path = RAIZ) -> str | None:
    """SHA-256 de `ruta` leído de SHA256SUMS (no recalculado); None si no está registrado."""
    sums = Path(raiz) / "SHA256SUMS"
    if not sums.exists():
        return None
    rel = Path(ruta).resolve().relative_to(Path(raiz).resolve()).as_posix()
    for linea in sums.read_text(encoding="utf-8").splitlines():
        partes = linea.split(None, 1)
        if len(partes) == 2 and partes[1].strip().lstrip("*") == rel:
            return partes[0]
    return None


# ---------- agregación: campaña principal ----------
def resumen_por_nivel(registros: list[dict]) -> list[dict]:
    """Una fila por nivel (0/1/2). Evaluable = detectada y con JSON válido (no INVALIDO ni NO_DETECTADO)."""
    filas = []
    for nivel in sorted({r["nivel"] for r in registros}):
        rs = [r for r in registros if r["nivel"] == nivel]
        estados = Counter(r["estado"] for r in rs)
        evaluables = [r for r in rs if r["estado"] not in ("NO_DETECTADO", "INVALIDO", "ERROR_LLM")]
        afirm = sum(r.get("afirmaciones", 0) for r in evaluables)
        rech = sum(len(r.get("evidencia_rechazada", [])) for r in evaluables)
        filas.append({
            "nivel": nivel, "casos": len(rs),
            "detectadas": len(rs) - estados.get("NO_DETECTADO", 0),
            "evaluables": len(evaluables),
            "top1": sum(bool(r.get("acierto_top1")) for r in evaluables),
            "top3": sum(bool(r.get("acierto_top3")) for r in evaluables),
            "estados": {e: estados.get(e, 0) for e in ESTADOS},
            "afirmaciones": afirm, "rechazadas": rech,
            "tasa_rechazo": (rech / afirm) if afirm else None,
        })
    return filas


def buscar_registro(registros: list[dict], falla: int, nivel: int) -> dict | None:
    return next((r for r in registros if r["falla"] == falla and r["nivel"] == nivel), None)


# ---------- agregación: réplica FaultExplainer ----------
def tabla_replica(registros: list[dict], linea_base: dict[str, tuple[int, ...]]) -> list[dict]:
    """Una fila por falla: detectada por su PCA, acierto de Gemma (top-3 por mayoría) y de cada línea base."""
    filas = []
    for r in sorted(registros, key=lambda r: r["falla"]):
        det = bool(r.get("detectada"))
        fila = {"falla": r["falla"], "detectada": det,
                "gemma": r.get("acierto_top3") if det and r.get("estado") == "RESPONDIDO" else None,
                "muestras_ok": r.get("aciertos_muestras"), "revision_alias": bool(r.get("requiere_revision_alias"))}
        for nombre, aciertos in linea_base.items():
            fila[nombre] = (r["falla"] in aciertos) if det else None
        filas.append(fila)
    return filas


def totales_replica(filas: list[dict], linea_base: dict[str, tuple[int, ...]]) -> dict:
    evaluadas = [f for f in filas if f["detectada"]]
    tot = {"detectadas": len(evaluadas), "Gemma": sum(bool(f["gemma"]) for f in evaluadas)}
    for nombre in linea_base:
        tot[nombre] = sum(bool(f[nombre]) for f in evaluadas)
    return tot


# ---------- cálculo determinista en vivo (core/) ----------
def serie_t2(falla: int, nivel: int) -> dict:
    """T² de d{falla}_te en las coordenadas de la vista, con el protocolo de la campaña (calibración ampliada)."""
    from core import datos, pca_t2
    from twin import gemela
    vista = gemela.construir(nivel)
    modelo = pca_t2.ajustar(vista.transformar(datos.normal_ampliado()))
    x = vista.transformar(datos.cargar(falla, prueba=True))
    return {"t2": pca_t2.t2(modelo, x), "limite": float(modelo.limite_t2),
            "primera_alarma": pca_t2.primera_alarma(modelo, x), "inicio_falla": datos.INICIO_FALLA_TEST}


def alarmas_proceso(falla: int) -> dict:
    """Alarmas de proceso (core/alarmas) desde el inicio de la falla. Se calculan en coordenadas TEP: son invariantes
    a la vista (el disfraz solo reetiqueta y reescala)."""
    from core import alarmas, datos
    lim = alarmas.ajustar_limites(datos.normal_ampliado())
    x = datos.cargar(falla, prueba=True)[datos.INICIO_FALLA_TEST:]
    ev = alarmas.eventos(lim, x)
    return {"total": len(ev), "tasa_10min": alarmas.tasa_por_ventana(ev),
            "inundacion": alarmas.inundacion(ev), "variables": len({e.variable for e in ev})}


def variable_en_vistas(columna_tep: int = 6) -> list[dict]:
    """La misma columna física tal como la ve cada vista (tag, descripción, unidad)."""
    from twin import gemela
    filas = []
    for nivel in (0, 1, 2):
        v = gemela.construir(nivel)
        j = int(np.flatnonzero(v.origen == columna_tep)[0])
        var = v.variables[j]
        filas.append({"vista": nivel, "tag": var.tag, "descripcion": var.descripcion, "unidad": var.unidad})
    return filas
