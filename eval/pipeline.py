"""Tubería de evaluación: preparar un caso (detección + prompt) y diagnosticarlo con un cliente LLM.

Orden del invariante: la estadística detecta → el LLM propone → la compuerta verifica. Aquí no hay control del proceso.
Las columnas TEP (`columnas_tep_top`) y el mapeo IDV solo se usan para auditar y puntuar; nunca van al prompt.
"""
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from core import compuerta, datos, pca_t2
from core.esquema import esquema_json
from llm.cliente import ErrorLLM, Respuesta
from llm.parseo import parsear
from llm.prompt import Fila, construir_mensajes
from twin import gemela

VENTANA = 6


@dataclass
class Caso:
    falla: int
    nivel: int
    calibracion: str
    estadistico: str
    detectado: bool
    indice_alarma: int | None
    vista: object = field(repr=False)
    mensajes: list[dict] = field(default_factory=list, repr=False)
    z: np.ndarray | None = field(default=None, repr=False)
    tags: list[str] = field(default_factory=list)
    codigos: list[str] = field(default_factory=list)    # orden del catálogo mostrado
    top: list[int] = field(default_factory=list)        # índices en la vista
    columnas_tep_top: list[int] = field(default_factory=list)  # auditoría; NO va al prompt
    falsa_alarma_previa: bool = False


def preparar_caso(falla: int, nivel: int, calibracion: str = "d00", estadistico: str = "t2",
                  n_top: int = 6, fusionar_system: bool = False) -> Caso:
    """Detecta la falla en d{falla}_te y construye el prompt con la vista del nivel dado."""
    if calibracion not in ("d00", "ampliado"):
        raise ValueError(f"calibracion desconocida: {calibracion!r}")
    vista = gemela.construir(nivel)
    normal = datos.cargar(0) if calibracion == "d00" else datos.normal_ampliado()
    n_mat = vista.transformar(normal)
    x = vista.transformar(datos.cargar(falla, prueba=True))
    modelo = pca_t2.ajustar(n_mat)
    i = pca_t2.primera_alarma(modelo, x, estadistico=estadistico)
    tags = [v.tag for v in vista.variables]
    codigos = [c.codigo for c in vista.catalogo]
    base = dict(falla=falla, nivel=nivel, calibracion=calibracion, estadistico=estadistico,
                vista=vista, tags=tags, codigos=codigos)
    if i is None or i < datos.INICIO_FALLA_TEST:
        return Caso(detectado=False, indice_alarma=i, falsa_alarma_previa=i is not None, **base)

    ventana = x[i - VENTANA + 1: i + 1]
    contrib = np.mean([pca_t2.contribuciones(modelo, fila) for fila in ventana], axis=0)
    top = [int(j) for j in np.argsort(-contrib)[:n_top]]
    media, desv = n_mat.mean(0), n_mat.std(0, ddof=1)
    z = compuerta.desviacion_z(ventana, media, desv)
    filas = [Fila(indice=j, contribucion=float(contrib[j]), z=float(z[j]),
                  valor=float(ventana[:, j].mean()), media_normal=float(media[j])) for j in top]
    mensajes = construir_mensajes(vista, filas)
    if fusionar_system:
        sistema = [m for m in mensajes if m["role"] == "system"]
        resto = [dict(m) for m in mensajes if m["role"] != "system"]
        if sistema and resto:
            resto[0]["content"] = "\n\n".join([m["content"] for m in sistema] + [resto[0]["content"]])
        mensajes = resto
    return Caso(detectado=True, indice_alarma=int(i), mensajes=mensajes, z=z, top=top,
                columnas_tep_top=[int(c) for c in vista.origen[top]], **base)


class ClienteEco:
    """Cliente simulado determinista: primer código del catálogo y variable top-1 en la dirección de su z."""

    modelo = "eco"

    def __init__(self, caso: Caso):
        j = caso.top[0]
        self.texto = json.dumps({
            "causes": [caso.codigos[0]],
            "evidence": [{"tag": caso.tags[j], "direction": "up" if caso.z[j] > 0 else "down"}],
            "explanation": "Simulated deterministic answer: the top contributing variable deviates.",
        })

    def completar(self, mensajes, n=1, temperatura=0.0, max_tokens=800, semilla=None, esquema=None) -> Respuesta:
        return Respuesta([self.texto] * n, self.modelo, {"prompt_tokens": 0, "completion_tokens": 0}, 0.0, [])


def _base_registro(caso: Caso) -> dict:
    return {"ts": datetime.now(timezone.utc).isoformat(), "falla": caso.falla, "nivel": caso.nivel,
            "calibracion": caso.calibracion, "estadistico": caso.estadistico,
            "indice_alarma": caso.indice_alarma, "columnas_tep_top": caso.columnas_tep_top}


def registro_no_detectado(caso: Caso) -> dict:
    return {**_base_registro(caso), "estado": "NO_DETECTADO", "falsa_alarma_previa": caso.falsa_alarma_previa}


def diagnosticar(caso: Caso, cliente, k: int = 1, temperatura: float = 0.0, semilla: int | None = None,
                 usar_esquema: bool = True) -> dict:
    """Pide k diagnósticos al LLM, los pasa por la compuerta y puntúa con el mapeo privado. Devuelve un registro JSON."""
    reg = _base_registro(caso)
    reg |= {"parametros": {"k": k, "temperatura": temperatura, "semilla": semilla, "usar_esquema": usar_esquema},
            "sha256_mensajes": hashlib.sha256(json.dumps(caso.mensajes, sort_keys=True).encode()).hexdigest()}
    try:
        resp = cliente.completar(caso.mensajes, n=k, temperatura=temperatura, semilla=semilla,
                                 esquema=esquema_json() if usar_esquema else None)
    except ErrorLLM as e:
        return reg | {"estado": "ERROR_LLM", "error": str(e)}
    parseos = [parsear(t) for t in resp.textos]
    validos = [d for d, _ in parseos if d is not None]
    reg |= {"modelo": resp.modelo, "textos": resp.textos, "errores_parseo": [e for _, e in parseos if e],
            "uso": resp.uso, "segundos": resp.segundos}
    if not validos:
        return reg | {"estado": "INVALIDO", "motivos": ["ninguna muestra con JSON válido"], "causas": [],
                      "idv_predichos": [], "acierto_top1": False, "acierto_top3": False, "afirmaciones": 0,
                      "evidencia_verificada": [], "evidencia_rechazada": []}
    v = compuerta.verificar_muestras(validos, tags=caso.tags, codigos=set(caso.codigos), z=caso.z)
    idv = [caso.vista.idv.get(c) for c in v.causas]
    return reg | {
        "estado": v.estado, "motivos": v.motivos, "confianza": v.confianza, "causas": v.causas,
        "idv_predichos": idv,
        "evidencia_verificada": [{"tag": e.tag, "direction": e.direccion} for e in v.evidencia_verificada],
        "evidencia_rechazada": [{"tag": e.tag, "direction": e.direccion, "motivo": m}
                                for e, m in v.evidencia_rechazada],
        "acierto_top1": idv[:1] == [caso.falla], "acierto_top3": caso.falla in idv[:3],
        "afirmaciones": v.afirmaciones,
    }


def commit_git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=datos.RAIZ).stdout.strip() or "desconocido"
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"
