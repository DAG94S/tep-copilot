"""Demo de TEP Copilot: replay de corridas GRABADAS (funciona con la GPU apagada, sin llamadas a LLM).

Ejecutar: python -m streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt
import pandas as pd
import streamlit as st

from app import datos_app as da

st.set_page_config(page_title="TEP Copilot", layout="wide")

COLOR = {"VERIFIED": "#1a7f37", "PARTIAL": "#b08800", "BLOCKED": "#cf222e", "UNCERTAIN": "#6e40c9"}
ESTADO_UI = {"VERIFICADO": "VERIFIED", "PARCIAL": "PARTIAL", "BLOQUEADO": "BLOCKED", "INCIERTO": "UNCERTAIN",
             "INVALIDO": "INVALID", "NO_DETECTADO": "NOT DETECTED", "ERROR_LLM": "LLM ERROR"}
NOTA = "The LLM proposes; deterministic checks verify; a human approves. No control actions are ever issued."


# ---------- carga cacheada ----------
@st.cache_data
def registros(campana: str) -> list[dict]:
    return da.leer_jsonl(da.archivo_efectivo(da.RUNS / campana))


@st.cache_data
def registros_combinados() -> tuple[list[dict], int]:
    """Campaña principal con los INVALIDO sustituidos por sus reintentos (si existen) y cuántos se sustituyeron."""
    base = registros(da.CAMPANA_PRINCIPAL)
    rei = registros(da.CAMPANA_REINTENTOS) if (da.RUNS / da.CAMPANA_REINTENTOS).exists() else []
    comb = da.combinar_reintentos(base, rei)
    return comb, sum(1 for a, b in zip(base, comb) if a is not b)


@st.cache_data
def manifiesto(campana: str) -> dict:
    return da.leer_json(da.RUNS / campana / "manifiesto.json")


@st.cache_data
def t2(falla: int, nivel: int) -> dict:
    return da.serie_t2(falla, nivel)


@st.cache_data
def alarmas(falla: int) -> dict:
    return da.alarmas_proceso(falla)


@st.cache_data
def vista(nivel: int):
    from twin import gemela
    return gemela.construir(nivel)


def procedencia(campana: str) -> None:
    """Ruta, SHA-256 (de SHA256SUMS), commit y modelo de una campaña."""
    ruta = da.archivo_efectivo(da.RUNS / campana)
    man = manifiesto(campana)
    sha = da.sha256_registrado(ruta) if ruta.exists() else None
    st.caption(f"Source: `{ruta.relative_to(da.RAIZ)}` · SHA-256 (from SHA256SUMS): `{sha or 'not registered'}` · "
               f"commit: `{(man.get('commit') or 'n/a')[:10]}` · model: `{man.get('modelo', 'n/a')}` "
               f"({man.get('backend', 'n/a')})")


def pestana_control() -> None:
    regs = registros(da.CAMPANA_PRINCIPAL)
    if not regs:
        st.warning(f"Recorded run not found: data/runs/{da.CAMPANA_PRINCIPAL}. The control room needs it.")
        return
    c1, c2 = st.columns(2)
    falla = c1.selectbox("Fault (IDV)", sorted({r["falla"] for r in regs}), format_func=lambda i: f"IDV({i})")
    nombre = c2.radio("View", list(da.VISTAS), horizontal=True)
    nivel = da.VISTAS[nombre]
    v = vista(nivel)

    try:
        s = t2(falla, nivel)
        al = alarmas(falla)
    except (OSError, ValueError) as e:
        st.warning(f"Local Braatz data not available ({e}). Run scripts/descargar_datos.py.")
        return

    st.subheader("Detection (deterministic PCA T²)")
    df = pd.DataFrame({"sample": range(len(s["t2"])), "T²": s["t2"]})
    base = alt.Chart(df).mark_line(color="#0969da").encode(x="sample:Q", y=alt.Y("T²:Q", scale=alt.Scale(type="log")))
    capas = [base,
             alt.Chart(pd.DataFrame({"y": [s["limite"]]})).mark_rule(color="#cf222e", strokeDash=[6, 4]).encode(y="y:Q"),
             alt.Chart(pd.DataFrame({"x": [s["inicio_falla"]]})).mark_rule(color="#888", strokeDash=[2, 2]).encode(x="x:Q")]
    if s["primera_alarma"] is not None:
        capas.append(alt.Chart(pd.DataFrame({"x": [s["primera_alarma"]]})).mark_rule(color="#1a7f37").encode(x="x:Q"))
    st.altair_chart(alt.layer(*capas), use_container_width=True)
    pa = s["primera_alarma"]
    st.caption(f"T² limit (red) = {s['limite']:.1f} · fault onset (grey) = sample {s['inicio_falla']} · "
               + (f"first detection (green) = sample {pa}, {(pa - s['inicio_falla']) * 3} min after onset"
                  if pa is not None else "the fault is NOT detected by T² in this run"))

    st.subheader("Process alarms since fault onset (what the operator would face without the copilot)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Alarm events", al["total"])
    m2.metric("Max alarms in 10 min", al["tasa_10min"])
    m3.metric("Distinct variables alarming", al["variables"])
    m4.metric("EEMUA 191 flood (>10 in 10 min)", "YES" if al["inundacion"] else "no")

    st.subheader("Root-cause card (recorded Gemma-4-31B output, replayed)")
    r = da.buscar_registro(regs, falla, nivel)
    if r is None:
        st.warning("No recorded case for this fault and view.")
    elif r["estado"] in ("NO_DETECTADO", "INVALIDO", "ERROR_LLM"):
        motivo = {"NO_DETECTADO": "the statistical detector did not raise an alarm, so the LLM was never called",
                  "INVALIDO": "the model produced no valid JSON in any sample (degenerate output); nothing is shown",
                  "ERROR_LLM": "the LLM call failed"}[r["estado"]]
        st.info(f"{ESTADO_UI[r['estado']]}: {motivo}.")
    else:
        tarjeta(r, v)
    st.info(NOTA)


def tarjeta(r: dict, v) -> None:
    estado = ESTADO_UI.get(r["estado"], r["estado"])
    st.markdown(f"<span style='background:{COLOR.get(estado, '#555')};color:white;padding:4px 12px;border-radius:6px;"
                f"font-weight:600'>{estado}</span>", unsafe_allow_html=True)
    conf = r.get("confianza")
    if conf is not None:
        k = r.get("parametros", {}).get("k", "k")
        st.write(f"Confidence (agreement of the top cause across {k} samples): **{conf:.0%}**")
    cat = {c.codigo: c.descripcion for c in v.catalogo}
    st.markdown("**Top-3 proposed causes**")
    for i, c in enumerate(r.get("causas", [])[:3], 1):
        st.markdown(f"{i}. `{c}` — {cat.get(c, 'not in catalog')}")
    var = {x.tag: f"{x.descripcion} [{x.unidad}]" for x in v.variables}
    flecha = {"up": "↑", "down": "↓"}

    def linea(e, extra=""):
        return f"`{e['tag']}` {flecha.get(e['direction'], e['direction'])} {var.get(e['tag'], 'unknown tag')}{extra}"

    st.markdown("**Verified evidence**")
    for e in r.get("evidencia_verificada", []):
        st.markdown("- " + linea(e))
    osc = r.get("evidencia_oscilante", [])
    if osc:
        st.markdown("**Oscillating evidence** (accepted, direction not verifiable)")
        for e in osc:
            st.markdown("- " + linea(e, f" — {e['motivo']}"))
    rech = r.get("evidencia_rechazada", [])
    if rech:
        st.markdown("**Rejected claims** (not supported by the data)")
        for e in rech:
            st.markdown("- ~~" + linea(e) + f"~~ — {e['motivo']}")
    for m in r.get("motivos", []):
        st.error(m)
    d1, d2, _ = st.columns([1, 1, 4])
    clave = f"decision_{r['falla']}_{r['nivel']}"
    if d1.button("Approve", key=f"ap_{clave}"):
        st.session_state[clave] = "APPROVED"
    if d2.button("Escalate", key=f"es_{clave}"):
        st.session_state[clave] = "ESCALATED"
    if clave in st.session_state:
        st.success(f"Decision recorded in this session: {st.session_state[clave]} (no action sent to the process).")


def pestana_audit() -> None:
    st.subheader("Main campaign: Gemma-4-31B-IT, k=5 samples per case, faults 1-15 x disguise levels 0/1/2")
    regs, n_sustituidos = registros_combinados()
    if not regs:
        st.warning(f"Recorded run not found: data/runs/{da.CAMPANA_PRINCIPAL}")
    else:
        filas = []
        for f in da.resumen_por_nivel(regs):
            e = f["estados"]
            filas.append({"Level": f["nivel"], "Detected": f"{f['detectadas']}/{f['casos']}",
                          "Evaluable": f["evaluables"], "Top-1": f"{f['top1']}/{f['evaluables']}",
                          "Top-3": f"{f['top3']}/{f['evaluables']}",
                          "VERIFIED": e["VERIFICADO"], "PARTIAL": e["PARCIAL"], "BLOCKED": e["BLOQUEADO"],
                          "UNCERTAIN": e["INCIERTO"], "INVALID": e["INVALIDO"],
                          "Rejected claims": f"{f['rechazadas']}/{f['afirmaciones']}",
                          "Rejection rate": f"{f['tasa_rechazo']:.0%}" if f["tasa_rechazo"] is not None else "n/a"})
        st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
        st.caption("Evaluable = detected and valid JSON. Level 0 = original TEP, 1 = anonymous tags, 2 = full disguise. "
                   "Rejection rate = claims removed by the gate / claims made.")
        procedencia(da.CAMPANA_PRINCIPAL)
        ruta_rei = da.archivo_efectivo(da.RUNS / da.CAMPANA_REINTENTOS)
        if n_sustituidos and ruta_rei.exists():
            sha_rei = da.sha256_registrado(ruta_rei)
            st.caption(f"Cases that came back INVALID (degenerate output from the server) were re-run with the same "
                       f"parameters; {n_sustituidos} records were replaced by their retry. "
                       f"Retries: `{ruta_rei.relative_to(da.RAIZ)}` · SHA-256 (from SHA256SUMS): "
                       f"`{sha_rei or 'not registered'}`")

    st.subheader("FaultExplainer replication (their data, PCA and literal prompt)")
    from eval import replica_faultexplainer as rep
    rr = registros(da.CAMPANA_REPLICA)
    if not rr:
        st.warning(f"Recorded run not found: data/runs/{da.CAMPANA_REPLICA}")
        return
    filas = da.tabla_replica(rr, rep.LINEA_BASE)
    mark = lambda b: "n/a (PCA does not detect)" if b is None else ("✓" if b else "✗")
    tabla = [{"IDV": f["falla"], "Gemma-4-31B (majority of 5)": mark(f["gemma"]),
              "Samples correct": f"{f['muestras_ok']}/5" if f["muestras_ok"] is not None else "",
              **{n: mark(f[n]) for n in rep.LINEA_BASE},
              "Alias review": "yes" if f["revision_alias"] else ""} for f in filas]
    st.dataframe(pd.DataFrame(tabla), hide_index=True, use_container_width=True)
    t = da.totales_replica(filas, rep.LINEA_BASE)
    st.markdown(f"**Top-3 correct on {t['detectadas']} detected faults:** Gemma-4-31B {t['Gemma']}, "
                + ", ".join(f"{n} {t[n]}" for n in rep.LINEA_BASE) + ".")
    st.caption("Baselines are derived from Table 1 of the FaultExplainer paper (see eval/replica_faultexplainer.py). "
               "Protocol differences: they use n=1 at default temperature; we use k=5 with majority vote at T=0.7.")
    procedencia(da.CAMPANA_REPLICA)


def pestana_como() -> None:
    st.subheader("The invariant")
    st.code("statistics DETECT  ->  LLM PROPOSES  ->  deterministic gate VERIFIES  ->  human APPROVES\n"
            "(PCA T²)               (read-only)        (no control verbs, claims               (no write access\n"
            "                                           checked against the data)               by the LLM)", language="text")
    st.markdown("""
- **Detect:** PCA T² on normal-operation data raises the alarm and ranks variable contributions. No LLM involved.
- **Propose:** the LLM sees only tags, descriptions, units and a cause catalog. It has no tools and cannot write to the process.
- **Verify:** every cited sensor must actually deviate (|z| >= 3, right direction); unsupported claims are struck out,
  control verbs are blocked, and disagreement between k samples downgrades to UNCERTAIN.
- **Approve:** the human decides. The buttons here only log a decision in the session.
""")
    st.subheader("The disguised twin: does the model reason or recite?")
    st.markdown("The same plant data is shown under a different name: random tags, reordered variables, shuffled cause "
                "catalog and (level 2) renamed components, streams, equipment and units. The statistics are identical "
                "(an affine per-column transform plus a permutation), so only what the LLM reads changes. If accuracy "
                "survives the disguise, the model is reasoning, not reciting TEP from memory.")
    try:
        filas = da.variable_en_vistas(6)
        st.dataframe(pd.DataFrame([{"View": {0: "0 · Original TEP", 1: "1 · Anonymous tags", 2: "2 · Full disguise"}[f["vista"]],
                                    "Tag": f["tag"], "Description": f["descripcion"], "Unit": f["unidad"]} for f in filas]),
                     hide_index=True, use_container_width=True)
        st.caption("The same physical measurement (column 7 of the TEP data) rendered by twin.gemela.construir(0/1/2).")
    except (OSError, ValueError, IndexError) as e:
        st.warning(f"Could not build the twin views: {e}")


st.title("TEP Copilot")
st.caption("Control-room copilot on the Tennessee Eastman Process. Replay of recorded runs: no GPU, no live LLM calls.")
t_ctrl, t_aud, t_how = st.tabs(["Control room", "Audit", "How it works"])
with t_ctrl:
    pestana_control()
with t_aud:
    pestana_audit()
with t_how:
    pestana_como()
