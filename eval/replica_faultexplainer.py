"""Brazo de RÉPLICA fiel de FaultExplainer (Khan et al. 2025, MIT), separado de nuestro pipeline.

Reproduce el protocolo de third_party/faultexplainer (commit 2fcfee9...; ver docs/REPLICA_FAULTEXPLAINER.md):
datos CSV de ellos, PCA/T² de model.py, contribuciones en UN punto, prompt de prompts.py en un solo mensaje `user`,
salida en texto libre con las causas IDV leídas del texto. Lo único que cambia es el LLM (inevitable).
Código derivado de FaultExplainer (c) 2025 Li Group, Purdue University, licencia MIT (third_party/faultexplainer/LICENSE).

CLI: python3 -m eval.replica_faultexplainer --campana NOMBRE --backend {simulado,AMD_TF,GOOGLE,...} --fallas 1-15
"""
import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from scipy.stats import f as dist_f
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from core import datos
from eval import pipeline
from eval.correr import BACKENDS, RAIZ_RUNS, _leer, _rango
from llm import cliente as cliente_llm

DATOS = datos.RAIZ / "data" / "raw" / "faultexplainer"
FE = datos.RAIZ / "third_party" / "faultexplainer"

# Tabla 1 del paper (derivación en docs/REPLICA_FAULTEXPLAINER.md sección 10; verificar con las negritas del PDF).
PCA_NO_DETECTA_PAPER = (3, 4, 9, 15)
LINEA_BASE = {"GPT-4o": (2, 6, 7, 11, 12, 13, 14), "o1-preview": (1, 2, 6, 7, 8, 11, 12, 13, 14)}

# model.py:9 (n_components=0.9, alpha=0.01); test_explain.py:43-46 y config.json:3 (6 alarmas consecutivas);
# config.json:4 y test_explain.py:59 (topkfeatures=6).
VARIANZA, ALFA, RACHA, TOP_K = 0.9, 0.01, 6, 6


def _cargar_prompts():
    """Importa third_party/faultexplainer/backend/prompts.py tal cual (no importa `openai`; solo define cadenas)."""
    spec = importlib.util.spec_from_file_location("fe_prompts", FE / "backend" / "prompts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROMPTS = _cargar_prompts()


def disponibles() -> bool:
    return (DATOS / "backend_data" / "fault0.csv").exists() and (DATOS / "backend_data" / "fault15.csv").exists()


def cargar_falla(i: int) -> pd.DataFrame:
    """CSV crudo de la falla i (backend/data/fault{i}.csv): columna `time` + 52 variables."""
    return pd.read_csv(DATOS / "backend_data" / f"fault{i}.csv")


class ModeloFE:
    """Réplica de FaultDetectionModel (backend/model.py) entrenada con fault0 (model.py:250)."""

    def __init__(self):
        ent = cargar_falla(0).drop(columns=["time"])
        self.nombres = ent.columns.to_list()
        self.scaler = StandardScaler()                       # model.py:11, :24 (media y std poblacional, ddof=0)
        Z = self.scaler.fit_transform(ent)
        self.pca = PCA(n_components=VARIANZA).fit(Z)         # model.py:12, :27
        self.a, self.n = int(self.pca.n_components_), self.pca.n_samples_        # model.py:28-30
        self.P, self.lam = self.pca.components_.T, self.pca.explained_variance_  # model.py:31-32
        escala = self.a * (self.n - 1) * (self.n + 1) / (self.n * (self.n - self.a))   # model.py:45-54
        self.umbral = escala * dist_f.ppf(1 - ALFA, self.a, self.n - self.a)
        # tabla de medias normales (equivale a backend/stats/features_mean_std.csv, model.py:36-43)
        self.normal = pd.DataFrame({"feature": self.nombres, "mean": self.scaler.mean_, "std": self.scaler.scale_})

    def t2(self, df: pd.DataFrame) -> np.ndarray:
        Z = self.scaler.transform(df[self.nombres])
        return np.einsum("ij,jk,ik->i", Z @ self.P, np.diag(1 / self.lam), Z @ self.P)  # model.py:65

    def contribuciones(self, fila: pd.DataFrame) -> np.ndarray:
        """model.py:154-165: c_ji = (t_i/λ_i)·p_ji·z_j, truncado a 0 POR COMPONENTE antes de sumar sobre i."""
        z = self.scaler.transform(fila[self.nombres])[0]
        t = z.T @ self.P
        return np.array([np.maximum((t / self.lam) * self.P[j, :] * z[j], 0).sum() for j in range(len(z))])


def indice_alarma(anomalia: np.ndarray) -> int | None:
    """test_explain.py:44-46: índice de la 6.ª alarma de la primera racha de 6 (rolling(6).sum()==6 → idxmax)."""
    racha = pd.Series(anomalia.astype(bool)).rolling(window=RACHA).sum() == RACHA
    return int(racha.idxmax()) if racha.any() else None


def analizar(modelo: ModeloFE, falla: int) -> dict:
    """Detección y top-6 de contribuciones de la falla; `idx=None` si su PCA no la detecta."""
    df = cargar_falla(falla)
    t2 = modelo.t2(df)
    idx = indice_alarma(t2 > modelo.umbral)
    res = {"falla": falla, "indice_alarma": idx, "detectada": idx is not None, "df": df}
    if idx is None:
        return res
    c = pd.Series(modelo.contribuciones(df.iloc[[idx]]), index=modelo.nombres)
    top = c.sort_values(ascending=False).head(TOP_K).index.to_list()   # test_explain.py:56-60
    res |= {"top": top, "contribuciones": {k: float(c[k]) for k in top}, "tiempo_h": float(df["time"].iloc[idx])}
    return res


def comparacion(modelo: ModeloFE, df: pd.DataFrame, idx: int, top: list[str]) -> str:
    """Copia literal de generate_feature_comparison (backend/app.py:170-213), con la tabla de medias de `modelo`."""
    comparison_results = []
    for feature in top:
        faulty_val = df[feature].iloc[: idx + 1].tolist()[-1]      # test_explain.py:62-65 + app.py:188 (solo el último)
        match = modelo.normal[modelo.normal["feature"].str.contains(feature, case=False, na=False)]  # app.py:191 (regex)
        if not match.empty:
            normal_mean = match["mean"].values[0]
            mean_change_percent = ((faulty_val - normal_mean) / normal_mean) * 100
            result = (
                f"Feature: {feature}\n"
                f"  - Faulty Data: Value = {faulty_val:.3f},"
                f"  - Normal Conditions: Mean = {normal_mean:.3f},"
                f"  - Percentage Changes: Value Change = {mean_change_percent:.2f}%, "
            )
            comparison_results.append(result)
        else:
            comparison_results.append(f"Feature: {feature} not found in normal conditions dataset.\n")
    return "The top feature changes are\n" + "\n".join(comparison_results)


def construir_mensajes(comparacion_txt: str) -> list[dict]:
    """app.py:221-229 / test_explain.py:83-90: UN solo mensaje `user` = SYSTEM_MESSAGE + EXPLAIN_ROOT + "\\n" + comparación.
    No se añade el sufijo LaTeX de test_explain.py:78-81 (formato de salida de su script, no parte del prompt de la app)."""
    return [{"role": "user", "content": PROMPTS.SYSTEM_MESSAGE + f"{PROMPTS.EXPLAIN_ROOT}\n{comparacion_txt}"}]


_IDV = re.compile(r"IDV\s*[\(\[]?\s*(\d{1,2})\b", re.IGNORECASE)


def extraer_idv(texto: str) -> dict:
    """Extrae las causas propuestas (números IDV) por orden de primera aparición.

    Ambigua si no hay exactamente 3 IDV distintos del catálogo (1-15) o si aparece alguno fuera del catálogo:
    entonces el humano debe revisar el texto crudo (alias de la Tabla 1 del paper, p. 14)."""
    vistos: list[int] = []
    for m in _IDV.finditer(texto):
        n = int(m.group(1))
        if n not in vistos:
            vistos.append(n)
    validos = [n for n in vistos if 1 <= n <= 15]
    return {"extraidos": validos[:3], "todos_mencionados": vistos,
            "requiere_revision_alias": len(validos) != 3 or len(vistos) != len(validos)}


def puntuar(falla: int, textos: list[str]) -> dict:
    muestras = []
    for t in textos:
        e = extraer_idv(t)
        muestras.append({"texto": t, **e, "acierto_top3": falla in e["extraidos"],
                         "acierto_top1": bool(e["extraidos"]) and e["extraidos"][0] == falla})
    n_top3 = sum(m["acierto_top3"] for m in muestras)
    return {"muestras": muestras, "aciertos_muestras": n_top3,
            "acierto_top3": n_top3 > len(muestras) / 2,       # mayoría estricta; con k=1 es la única muestra
            "acierto_top1": sum(m["acierto_top1"] for m in muestras) > len(muestras) / 2,
            "requiere_revision_alias": any(m["requiere_revision_alias"] for m in muestras)}


class _ClienteEco:
    """Backend `simulado`: responde con la causa verdadera y dos más (no usa LLM; solo para humo/replay)."""
    modelo = "simulado"

    def __init__(self, falla: int):
        self.falla = falla

    def completar(self, mensajes, n=1, temperatura=0.0, max_tokens=800, semilla=None, esquema=None):
        otros = [c for c in (1, 2, 3, 4) if c != self.falla][:2]
        t = f"The three most likely causes are IDV({self.falla}), IDV({otros[0]}) and IDV({otros[1]})."
        return cliente_llm.Respuesta([t] * n, "simulado", {"prompt_tokens": 0, "completion_tokens": 0}, 0.0, [])


def correr(campana: str, backend: str, fallas: list[int], k: int = 1, temperatura: float = 0.7, max_tokens: int = 1500,
           razonamiento: str | None = None, continuar: bool = False, raiz_runs: Path = RAIZ_RUNS,
           argumentos: dict | None = None, cliente=None) -> list[dict]:
    carpeta = raiz_runs / campana
    ruta_reg, ruta_man = carpeta / "registros.jsonl", carpeta / "manifiesto.json"
    if ruta_man.exists() and not continuar:
        raise SystemExit(f"la campaña {campana!r} ya existe en {carpeta}; usa --continuar o cambia el nombre")
    if not disponibles():
        raise SystemExit("faltan los CSV de FaultExplainer: python3 scripts/descargar_faultexplainer.py --registrar")
    carpeta.mkdir(parents=True, exist_ok=True)
    hechos = {r["falla"] for r in _leer(ruta_reg)}
    if backend != "simulado" and cliente is None:
        cliente = cliente_llm.desde_env(prefijo=backend)
        if razonamiento:
            cliente.extra_body = cliente.extra_body | {"reasoning_effort": razonamiento}
    endpoint = urlparse(cliente.base_url).netloc if cliente is not None and hasattr(cliente, "base_url") else None
    manifiesto = {"campana": campana, "tipo": "replica_faultexplainer", "argumentos": argumentos or {},
                  "commit": pipeline.commit_git(), "inicio": datetime.now(timezone.utc).isoformat(),
                  "backend": backend, "modelo": getattr(cliente, "modelo", "simulado"), "host_endpoint": endpoint,
                  "faultexplainer_commit": "2fcfee975a687c350f10909eeccd1ecdd60340be"}
    if ruta_man.exists():
        previo = json.loads(ruta_man.read_text(encoding="utf-8"))
        manifiesto["inicio_original"] = previo.get("inicio_original", previo.get("inicio"))
    ruta_man.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")

    modelo = ModeloFE()
    manifiesto["pca"] = {"componentes": modelo.a, "umbral_t2": float(modelo.umbral), "n": int(modelo.n)}
    with ruta_reg.open("a", encoding="utf-8") as f:
        for falla in fallas:
            if falla in hechos:
                continue
            an = analizar(modelo, falla)
            reg = {"falla": falla, "nivel": 0, "detectada": an["detectada"], "indice_alarma": an["indice_alarma"]}
            if not an["detectada"]:
                reg["estado"] = "NO_DETECTADO"
            else:
                texto_cmp = comparacion(modelo, an["df"], an["indice_alarma"], an["top"])
                mensajes = construir_mensajes(texto_cmp)
                c = _ClienteEco(falla) if backend == "simulado" else cliente
                reg |= {"tiempo_h": an["tiempo_h"], "top6": an["top"], "contribuciones": an["contribuciones"],
                        "comparacion": texto_cmp, "mensajes": mensajes}
                try:
                    resp = c.completar(mensajes, n=k, temperatura=temperatura, max_tokens=max_tokens)
                except cliente_llm.ErrorLLM as e:
                    reg |= {"estado": "ERROR_LLM", "error": str(e)}
                else:
                    reg |= {"estado": "RESPONDIDO", "uso": resp.uso, "segundos": resp.segundos,
                            **puntuar(falla, resp.textos)}
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
            f.flush()
    manifiesto["fin"] = datetime.now(timezone.utc).isoformat()
    ruta_man.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    return _leer(ruta_reg)


def resumen(registros: list[dict]) -> str:
    registros = sorted(registros, key=lambda r: r["falla"])
    det = [r["falla"] for r in registros if r["detectada"]]
    nodet = [r["falla"] for r in registros if not r["detectada"]]
    ac = [r["falla"] for r in registros if r.get("acierto_top3")]
    rev = [r["falla"] for r in registros if r.get("requiere_revision_alias")]
    err = [r["falla"] for r in registros if r["estado"] == "ERROR_LLM"]
    ev = {r["falla"] for r in registros}
    L = [f"Fallas detectadas por su PCA ({len(det)}): {det}",
         f"No detectadas ({len(nodet)}): {nodet}  (paper: {list(PCA_NO_DETECTA_PAPER)})",
         f"Aciertos top-3 sin alias: {len(ac)}/{len(det)} -> {ac}",
         f"Requieren revisión manual de alias: {rev}"]
    if err:
        L.append(f"Errores del LLM: {err}")
    for nombre, base in LINEA_BASE.items():
        b = [x for x in base if x in ev]
        L.append(f"Línea base {nombre} (Tabla 1, con alias, derivado): {len(b)} aciertos en las fallas evaluadas -> {b}")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="eval.replica_faultexplainer", description=__doc__.splitlines()[0])
    p.add_argument("--campana", required=True)
    p.add_argument("--backend", required=True, choices=BACKENDS)
    p.add_argument("--fallas", default="1-15")
    p.add_argument("--k", type=int, default=1)
    p.add_argument("--temperatura", type=float, default=0.7)
    p.add_argument("--max-tokens", type=int, default=1500)
    p.add_argument("--razonamiento", default=None, help="valor de reasoning_effort (si el backend lo admite)")
    p.add_argument("--continuar", action="store_true")
    p.add_argument("--dev", action="store_true", help="guarda en data/dev (no versionado)")
    a = p.parse_args(argv)
    regs = correr(a.campana, a.backend, _rango(a.fallas), a.k, a.temperatura, a.max_tokens, a.razonamiento, a.continuar,
                  raiz_runs=RAIZ_RUNS.parent / "dev" if a.dev else RAIZ_RUNS, argumentos=vars(a))
    print(resumen(regs))


if __name__ == "__main__":
    main(sys.argv[1:])
