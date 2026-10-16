"""Verifica la integridad de los datos (SHA256SUMS) y las afirmaciones cuantitativas (claims.json).

Cada afirmación de `claims.json` ({id, valor, fuente, descripcion[, reintentos][, auxiliar]}) se RECALCULA con código desde su `fuente`
(JSONL pineado, o lista de JSONL que se concatenan) y se compara con `valor`. Si trae `reintentos` (JSONL), cada INVALIDO de la fuente se sustituye por el reintento de su (falla, nivel). Si trae `auxiliar` (JSON o JSONL), la métrica lo recibe como segundo argumento (FALLA si falta). Nada se copia: si el dato cambia, la afirmación falla.

Uso:
    python3 scripts/verify_claims.py
Código de salida: 0 si todo cuadra; 1 si un hash difiere, falta un archivo versionado o una afirmación no coincide.
"""
import hashlib
import json
import re
import statistics
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


def _mediana(xs) -> float:
    return float(statistics.median(xs))


def _percentil(xs, q: float) -> float:
    """Percentil q (0-100) por interpolación lineal (como numpy.percentile por defecto)."""
    v = sorted(xs)
    pos = (len(v) - 1) * q / 100
    i = int(pos)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (pos - i)


def _con_llm(regs: list[dict]) -> list[dict]:
    """Casos en que se llamó al LLM (estado distinto de NO_DETECTADO)."""
    return [r for r in regs if r["estado"] != "NO_DETECTADO"]


def _latencia(q: float):
    # cada caso = k=5 llamadas secuenciales; `segundos` es el total del caso
    return lambda regs: f"{_percentil([r['segundos'] for r in _con_llm(regs)], q):.0f} s"


def _tokens_caso(r: dict) -> int:
    return r["uso"]["prompt_tokens"] + r["uso"]["completion_tokens"]


def _tokens_por_caso_mediana(regs: list[dict]) -> str:
    return f"{_mediana([_tokens_caso(r) for r in _con_llm(regs)]):.0f}"


def _coste_por_incidente(regs: list[dict], uso_tf: dict) -> str:
    """Coste medio por caso (USD estimados): tasas de entrada y salida de Gemma-4-31B-IT del registro de uso de Token Factory
    (entrada = (input_cost + cached_input_cost) / prompt_tokens, tasa mezclada con su acierto de caché; salida = output_cost / completion_tokens)."""
    m = next(x for x in uso_tf["by_model"] if x["model"] == "Gemma-4-31B-IT")
    t_in = (m["input_cost"] + m["cached_input_cost"]) / m["prompt_tokens"]
    t_out = m["output_cost"] / m["completion_tokens"]
    casos = _con_llm(regs)
    coste = sum(r["uso"]["prompt_tokens"] * t_in + r["uso"]["completion_tokens"] * t_out for r in casos) / len(casos)
    return f"${coste:.5f}"


def _alarmas_por_tarjeta_mediana(regs: list[dict], aux: dict) -> str:
    """Mediana, sobre las fallas con caso LLM, de los eventos de alarma de proceso entre el inicio de la falla y la tarjeta
    (scripts/medir_alarmas.py). Falla si falta una falla en el auxiliar o su indice_alarma no coincide."""
    por_falla = {}
    for r in _con_llm(regs):
        a = aux["por_falla"][str(r["falla"])]
        if a["indice_alarma"] != r["indice_alarma"]:
            raise ValueError(f"falla {r['falla']}: indice_alarma {r['indice_alarma']} != auxiliar {a['indice_alarma']}")
        por_falla[r["falla"]] = a["eventos"]
    return f"{_mediana(por_falla.values()):g}"


def _filas_anticipacion(regs: list[dict], aux: dict) -> list[tuple[int, dict]]:
    """Filas (falla, fila) de anticipacion.json para las fallas con caso LLM de nivel 0, ordenadas por falla.
    Falla si falta una falla en el auxiliar o su indice_alarma no coincide con la campaña (scripts/medir_anticipacion.py)."""
    filas = {}
    for r in _con_llm(regs):
        if r["nivel"] != 0:
            continue
        a = aux["por_falla"][str(r["falla"])]
        if a["indice_alarma"] != r["indice_alarma"]:
            raise ValueError(f"falla {r['falla']}: indice_alarma {r['indice_alarma']} != auxiliar {a['indice_alarma']}")
        filas[r["falla"]] = a
    return sorted(filas.items())


def _con_inundacion(regs: list[dict], aux: dict) -> list[tuple[int, dict]]:
    return [(f, a) for f, a in _filas_anticipacion(regs, aux) if a["inundacion_min"] is not None]


def _anticipacion_inundaciones(regs: list[dict], aux: dict) -> str:
    """Fallas con inundación de alarmas en las que la tarjeta llega antes / fallas con inundación."""
    con = _con_inundacion(regs, aux)
    return f"{sum(a['tarjeta_min'] < a['inundacion_min'] for _, a in con)}/{len(con)}"


def _anticipacion_minutos(regs: list[dict], aux: dict) -> str:
    """(inundación - tarjeta) en minutos para las fallas con inundación, ordenadas por falla."""
    return ", ".join(f"{a['inundacion_min'] - a['tarjeta_min']:g}" for _, a in _con_inundacion(regs, aux))


def _tarjeta_antes_primera_alarma(regs: list[dict], aux: dict) -> str:
    """Número de fallas en que la tarjeta llega estrictamente antes de la primera alarma de proceso."""
    return str(sum(a["primera_alarma_min"] is not None and a["tarjeta_min"] < a["primera_alarma_min"]
                   for _, a in _filas_anticipacion(regs, aux)))


def _alarmas_2h_tras_tarjeta_max(regs: list[dict], aux: dict) -> str:
    """Máximo, entre fallas, de eventos de alarma en las 2 h posteriores a la tarjeta."""
    return str(max(a["alarmas_2h_tras_tarjeta"] for _, a in _filas_anticipacion(regs, aux)))


def combinar_reintentos(regs: list[dict], reintentos: list[dict]) -> list[dict]:
    """Sustituye cada registro INVALIDO por el reintento con la misma (falla, nivel); el resto no se toca."""
    por_caso = {(r["falla"], r["nivel"]): r for r in reintentos}
    return [por_caso.get((r["falla"], r["nivel"]), r) if r["estado"] == "INVALIDO" else r for r in regs]


# ---------- campañas Rieth (10 corridas por falla) y Braatz con razonamiento ----------

EXCLUIDOS = ("NO_DETECTADO", "INVALIDO", "ERROR_LLM")


def _ev(regs: list[dict], nivel: int) -> list[dict]:
    return [r for r in regs if r["nivel"] == nivel and r["estado"] not in EXCLUIDOS]


def _top_ev(regs: list[dict], nivel: int, clave: str) -> str:
    ev = _ev(regs, nivel)
    return _fraccion(sum(bool(r[clave]) for r in ev), len(ev))


def _pareado(regs: list[dict], a: int, b: int, clave: str = "acierto_top3"):
    """Casos emparejados por (falla, corrida), evaluables en ambos niveles: [(falla, acierto_a, acierto_b)]."""
    pa = {(r["falla"], r["corrida"]): bool(r[clave]) for r in _ev(regs, a)}
    pb = {(r["falla"], r["corrida"]): bool(r[clave]) for r in _ev(regs, b)}
    return [(k[0], pa[k], pb[k]) for k in sorted(pa.keys() & pb.keys())]


def _discordantes(par) -> tuple[int, int]:
    """(solo acierta el primer nivel, solo acierta el segundo)."""
    return sum(x and not y for _, x, y in par), sum(y and not x for _, x, y in par)


def _pareado_txt(a: int, b: int):
    def f(regs):
        d1, d2 = _discordantes(_pareado(regs, a, b))
        return f"{d1} vs {d2}"
    return f


def _mcnemar_p(a: int, b: int):
    def f(regs):
        from scipy.stats import binomtest  # perezoso
        d1, d2 = _discordantes(_pareado(regs, a, b))
        return f"{binomtest(d1, d1 + d2, 0.5).pvalue:.2f}" if d1 + d2 else "1.00"
    return f


def caida_bootstrap(par, replicas: int = 5000, semilla: int = 0) -> tuple[float, float, float]:
    """Caída media (primer nivel menos segundo, en puntos porcentuales) con IC95 bootstrap por clusters de falla:
    se remuestrean las fallas con reemplazo y se promedia sobre todos los casos de las fallas elegidas.
    Devuelve (caída, p2.5, p97.5). Determinista (default_rng(semilla))."""
    import numpy as np  # perezoso: solo las métricas Rieth lo necesitan
    fallas = sorted({f for f, _, _ in par})
    dif = np.array([[int(x) - int(y) for g, x, y in par if g == f] for f in fallas], dtype=object)
    sumas = np.array([sum(d) for d in dif], dtype=float)
    cuentas = np.array([len(d) for d in dif], dtype=float)
    rng = np.random.default_rng(semilla)
    idx = rng.integers(0, len(fallas), size=(replicas, len(fallas)))
    est = sumas[idx].sum(axis=1) / cuentas[idx].sum(axis=1) * 100
    return float(sumas.sum() / cuentas.sum() * 100), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def _caida_txt(a: int, b: int):
    def f(regs):
        c, lo, hi = caida_bootstrap(_pareado(regs, a, b))
        return f"{c:.0f} pp [{lo:.0f}, {hi:.0f}]"
    return f


def _idv8_top3(regs: list[dict]) -> str:
    return "/".join(str(sum(bool(r["acierto_top3"]) for r in _ev(regs, n) if r["falla"] == 8)) for n in range(3))


# ---------- evidencia rechazada: sin razonamiento (fuente) vs con razonamiento (auxiliar), mismos casos ----------

def _rechazo_por_caso(rs: list[dict]) -> dict:
    """{(falla, nivel): registro} de los casos evaluables con al menos una afirmación."""
    return {(r["falla"], r["nivel"]): r for r in rs if r["estado"] not in EXCLUIDOS and r.get("afirmaciones")}


def _pares_rechazo(regs: list[dict], aux: list[dict]) -> list[tuple[int, float, float]]:
    """Casos (falla, nivel) evaluables en ambas campañas: [(falla, rechazo_sin, rechazo_con)],
    rechazo = afirmaciones rechazadas por la compuerta / afirmaciones del caso."""
    a, b = _rechazo_por_caso(regs), _rechazo_por_caso(aux)
    tasa = lambda r: len(r.get("evidencia_rechazada", [])) / r["afirmaciones"]
    return [(k[0], tasa(a[k]), tasa(b[k])) for k in sorted(a.keys() & b.keys())]


def _por_falla(par) -> list[tuple[int, float, float]]:
    """Media por falla de sus niveles emparejados (los niveles de una falla se parecen: clusters, no casos)."""
    return [(f, statistics.fmean(x for g, x, _ in par if g == f), statistics.fmean(y for g, _, y in par if g == f))
            for f in sorted({f for f, _, _ in par})]


def _peor_mejor_igual(par) -> str:
    """Pares en que el rechazo con razonamiento es mayor / menor / igual."""
    return f"{sum(y > x for _, x, y in par)} / {sum(y < x for _, x, y in par)} / {sum(y == x for _, x, y in par)}"


def _wilcoxon_p(par) -> str:
    from scipy.stats import wilcoxon  # perezoso
    return f"{wilcoxon([y for _, _, y in par], [x for _, x, _ in par]).pvalue:.2g}"


def _think_rechazo_medias(regs: list[dict], aux: list[dict]) -> str:
    par = _pares_rechazo(regs, aux)
    return f"{statistics.fmean(x for _, x, _ in par):.0%} / {statistics.fmean(y for _, _, y in par):.0%}"


def _think_afirmaciones(regs: list[dict], aux: list[dict]) -> str:
    """Rechazadas/afirmaciones sin y con razonamiento, sumadas sobre los mismos casos emparejados."""
    a, b = _rechazo_por_caso(regs), _rechazo_por_caso(aux)
    ks = a.keys() & b.keys()
    tot = lambda d: f"{sum(len(d[k].get('evidencia_rechazada', [])) for k in ks)}/{sum(d[k]['afirmaciones'] for k in ks)}"
    return f"{tot(a)} / {tot(b)}"


def _think_top1_pares(regs: list[dict], aux: list[dict]) -> str:
    a, b = _rechazo_por_caso(regs), _rechazo_por_caso(aux)
    ks = sorted(a.keys() & b.keys())
    return f"{sum(bool(a[k]['acierto_top1']) for k in ks)} / {sum(bool(b[k]['acierto_top1']) for k in ks)} of {len(ks)}"


def _por_nivel_mediana(valor, redondeo=lambda x: f"{x:.0f}"):
    def f(regs):
        return " / ".join(redondeo(_mediana([valor(r) for r in _ev(regs, n)])) for n in range(3))
    return f


METRICAS = {
    "replica_gemma_top3": _replica_top3,
    "replica_gemma_fallas": lambda regs: _lista(r["falla"] for r in regs if r["detectada"] and not r.get("acierto_top3")),
    "replica_gemma_no_detectadas": lambda regs: _lista(r["falla"] for r in regs if not r["detectada"]),
    **{f"campana_v2_n{n}_top1": (lambda regs, n=n: _top(regs, n, "acierto_top1")) for n in range(3)},
    **{f"campana_v2_n{n}_top3": (lambda regs, n=n: _top(regs, n, "acierto_top3")) for n in range(3)},
    **{f"combinado_n{n}_top1": (lambda regs, n=n: _top(regs, n, "acierto_top1")) for n in range(3)},
    **{f"combinado_n{n}_top3": (lambda regs, n=n: _top(regs, n, "acierto_top3")) for n in range(3)},
    "evolus_llamadas": lambda regs: str(len(regs)),
    "evolus_ordenes_control": lambda regs: str(sum(len(r.get("ordenes_de_control", [])) for r in regs)),
    "evolus_biblioteca_llamadas": lambda regs: str(len(regs)),
    "evolus_biblioteca_ordenes_control": lambda regs: str(sum(len(r.get("ordenes_de_control", [])) for r in regs)),
    "evolus_traducciones": lambda regs: f"{sum(bool(r.get('traduccion')) and not r.get('truncado') for r in regs)}/{len(regs)}",
    "combinado_rechazo": _tasa_rechazo,
    "campana_v2_rechazo_antes": _tasa_rechazo,
    "campana_v2_rechazo_despues": _tasa_rechazo,
    "latencia_p50_s": _latencia(50),
    "latencia_p95_s": _latencia(95),
    "tokens_por_caso_mediana": _tokens_por_caso_mediana,
    **{f"rieth_n{n}_top1": (lambda regs, n=n: _top_ev(regs, n, "acierto_top1")) for n in range(3)},
    **{f"rieth_n{n}_top3": (lambda regs, n=n: _top_ev(regs, n, "acierto_top3")) for n in range(3)},
    "rieth_top3_pareado_n0_n2": _pareado_txt(0, 2),
    "rieth_top3_mcnemar_p_n0_n2": _mcnemar_p(0, 2),
    "rieth_top3_caida_ic95_n0_n2": _caida_txt(0, 2),
    "rieth_top3_pareado_n0_n1": _pareado_txt(0, 1),
    "rieth_top3_mcnemar_p_n0_n1": _mcnemar_p(0, 1),
    "rieth_top3_caida_ic95_n0_n1": _caida_txt(0, 1),
    "rieth_idv8_top3": _idv8_top3,
    **{f"think_n{n}_top1": (lambda regs, n=n: _top_ev(regs, n, "acierto_top1")) for n in range(3)},
    **{f"think_n{n}_top3": (lambda regs, n=n: _top_ev(regs, n, "acierto_top3")) for n in range(3)},
    # mediana por caso; las medianas con .5 se truncan (16750.5 -> 16750) para no depender del redondeo bancario
    "think_razonamiento_mediana": _por_nivel_mediana(lambda r: r["uso"]["reasoning_tokens"], lambda x: f"{int(x)}"),
    "think_segundos_mediana": _por_nivel_mediana(lambda r: r["segundos"]),
    "evolus_latencia_max_s": lambda regs: f"{max(r['segundos'] for r in regs):.0f} s",
    # réplica puntuada por el anotador LLM (eval/extraer_causas_llm.py): una fila por falla detectada
    "replica_anotador_gemma_top3": lambda regs: _fraccion(sum(bool(r["acierto_top3"]) for r in regs), len(regs)),
    "replica_anotador_qwen_top3": lambda regs: _fraccion(sum(bool(r["acierto_top3"]) for r in regs), len(regs)),
    "replica_anotador_qwen_fallas": lambda regs: _lista(r["falla"] for r in regs if r["acierto_top3"]),
    **{f"qwen_n{n}_top1": (lambda regs, n=n: _top_ev(regs, n, "acierto_top1")) for n in range(3)},
    **{f"qwen_n{n}_top3": (lambda regs, n=n: _top_ev(regs, n, "acierto_top3")) for n in range(3)},
    **{f"qwen_think_n{n}_top1": (lambda regs, n=n: _top_ev(regs, n, "acierto_top1")) for n in range(3)},
    **{f"qwen_think_n{n}_top3": (lambda regs, n=n: _top_ev(regs, n, "acierto_top3")) for n in range(3)},
}
# métricas que además reciben el archivo `auxiliar` del claim
METRICAS_AUX = {
    "coste_por_incidente": _coste_por_incidente,
    "alarmas_por_tarjeta_mediana": _alarmas_por_tarjeta_mediana,
    "anticipacion_inundaciones": _anticipacion_inundaciones,
    "anticipacion_minutos": _anticipacion_minutos,
    "tarjeta_antes_primera_alarma": _tarjeta_antes_primera_alarma,
    "alarmas_2h_tras_tarjeta_max": _alarmas_2h_tras_tarjeta_max,
    "think_rechazo_medias": _think_rechazo_medias,
    "think_rechazo_pares": lambda regs, aux: _peor_mejor_igual(_pares_rechazo(regs, aux)),
    "think_rechazo_wilcoxon_p": lambda regs, aux: _wilcoxon_p(_pares_rechazo(regs, aux)),
    "think_rechazo_fallas": lambda regs, aux: _peor_mejor_igual(_por_falla(_pares_rechazo(regs, aux))),
    "think_rechazo_fallas_wilcoxon_p": lambda regs, aux: _wilcoxon_p(_por_falla(_pares_rechazo(regs, aux))),
    "think_afirmaciones": _think_afirmaciones,
    "think_top1_pares": _think_top1_pares,
    # segundo modelo: mismas métricas con otras fuentes (fuente = referencia, auxiliar = comparada)
    "qwen_vs_gemma_rechazo_medias": _think_rechazo_medias,
    "qwen_vs_gemma_rechazo_fallas": lambda regs, aux: _peor_mejor_igual(_por_falla(_pares_rechazo(regs, aux))),
    "qwen_vs_gemma_rechazo_fallas_wilcoxon_p": lambda regs, aux: _wilcoxon_p(_por_falla(_pares_rechazo(regs, aux))),
    "qwen_think_rechazo_medias": _think_rechazo_medias,
    "qwen_think_rechazo_fallas": lambda regs, aux: _peor_mejor_igual(_por_falla(_pares_rechazo(regs, aux))),
    "qwen_think_rechazo_fallas_wilcoxon_p": lambda regs, aux: _wilcoxon_p(_por_falla(_pares_rechazo(regs, aux))),
    "qwen_think_top1_pares": _think_top1_pares,
}


def leer_jsonl(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def leer_auxiliar(ruta: Path):
    """JSON completo, o lista de registros si es .jsonl."""
    return leer_jsonl(ruta) if ruta.suffix == ".jsonl" else json.loads(ruta.read_text(encoding="utf-8"))


def _rutas_auxiliar(c: dict) -> list[str]:
    return c["auxiliar"] if isinstance(c["auxiliar"], list) else [c["auxiliar"]]


def verificar_afirmaciones(raiz: Path, claims_path: Path) -> list[tuple[str, str, str, str]]:
    """[(id, estado, esperado, calculado)] con estado OK | FALLA."""
    res = []
    for c in json.loads(claims_path.read_text(encoding="utf-8")):
        esperado = str(c["valor"])
        f = METRICAS.get(c["id"]) or METRICAS_AUX.get(c["id"])
        if f is None:
            res.append((c["id"], "FALLA", esperado, "id sin métrica definida"))
            continue
        fuentes = c["fuente"] if isinstance(c["fuente"], list) else [c["fuente"]]
        ausente = next((x for x in fuentes if not (raiz / x).exists()), None)
        if ausente is not None:
            res.append((c["id"], "FALLA", esperado, f"fuente ausente: {ausente}"))
            continue
        try:
            regs = [r for x in fuentes for r in leer_jsonl(raiz / x)]
            if c.get("reintentos"):
                rei = raiz / c["reintentos"]
                if not rei.exists():
                    res.append((c["id"], "FALLA", esperado, f"reintentos ausentes: {c['reintentos']}"))
                    continue
                regs = combinar_reintentos(regs, leer_jsonl(rei))
            if c["id"] in METRICAS_AUX:
                if not c.get("auxiliar"):
                    res.append((c["id"], "FALLA", esperado, "la métrica requiere `auxiliar`"))
                    continue
                rutas = _rutas_auxiliar(c)
                falta = next((x for x in rutas if not (raiz / x).exists()), None)
                if falta is not None:
                    res.append((c["id"], "FALLA", esperado, f"auxiliar ausente: {falta}"))
                    continue
                # una sola ruta: JSON o JSONL tal cual; lista: JSONL concatenados
                aux = (leer_auxiliar(raiz / rutas[0]) if len(rutas) == 1
                       else [r for x in rutas for r in leer_jsonl(raiz / x)])
                calculado = f(regs, aux)
            else:
                calculado = f(regs)
        except (KeyError, ValueError, TypeError, StopIteration, ZeroDivisionError) as e:
            res.append((c["id"], "FALLA", esperado, f"error al calcular: {e!r}"))
            continue
        res.append((c["id"], "OK" if calculado == esperado else "FALLA", esperado, calculado))
    return res


MARCADOR = re.compile(r"<!--claim:([A-Za-z0-9_]+)-->(.*?)<!--/claim-->", re.S)


def verificar_readme(readme: Path, claims_path: Path) -> list[tuple[str, str, str, str]]:
    """[(id, estado, en_readme, en_claims)] por cada marcador `<!--claim:ID-->VALOR<!--/claim-->` del README."""
    valores = {c["id"]: str(c["valor"]) for c in json.loads(claims_path.read_text(encoding="utf-8"))}
    res = []
    for id_, valor in MARCADOR.findall(readme.read_text(encoding="utf-8")):
        if id_ not in valores:
            res.append((id_, "FALLA", valor, "id inexistente en claims.json"))
        else:
            res.append((id_, "OK" if valor == valores[id_] else "FALLA", valor, valores[id_]))
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
    print("\n== README ==")
    readme = raiz / "README.md"
    if not readme.exists():
        print("FALLA README.md no existe")
        fallos += 1
    else:
        marc = verificar_readme(readme, claims)
        for id_, est, en_readme, en_claims in marc:
            if est == "FALLA":
                print(f"FALLA {id_}: README dice {en_readme!r}, claims.json {en_claims!r}")
                fallos += 1
        print(f"{sum(m[1] == 'OK' for m in marc)}/{len(marc)} marcadores verificados")

    print("\nRESULTADO:", "TODO OK" if not fallos else f"{fallos} FALLA(S)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
