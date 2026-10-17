# Deck y guion del video (borrador, 17 oct)

Slides y narración en inglés (regla 5); notas de producción en español.
Cada cifra lleva entre corchetes el id de su claim en `claims.json`; antes de grabar, correr `scripts/verify_claims.py`
y comprobar que los valores siguen iguales. Nada de cifras que no estén en `claims.json`.
`[PENDIENTE 18-oct]` = hueco para el resultado Rieth con vs sin thinking en el mismo despliegue
(`scripts/analizar_thinking_rieth.py`); si no está completo a las 07:00 (Ecuador), se usa la variante B de la slide 7.

Video: ≤ 5 min (MP4 ≤ 300 MB). Narración ~560 palabras ≈ 4:15 a 130 palabras/min; el resto es demo sin voz.
Lablab pide además portada 16:9 y slides en PDF: el deck de abajo sirve para las dos cosas (portada = slide 1).

---

## Deck (12 slides)

### 1. Cover
- **TEP Copilot: reasoning, not reciting**
- "An AI copilot that proves it isn't reciting the textbook."
- AMD Developer Hackathon ACT III · Intelligent Industry · Gemma on AMD Token Factory · Evolus
- Diego García
- Visual: tarjeta de causa raíz sobre un fondo de alarmas en rojo (captura de la demo, pestaña Live replay).

### 2. The problem: alarm floods
- Milford Haven, 1994: 275 alarms in the last 10.7 minutes before the explosion, one every 2-3 seconds; the flare drum
  high-level alarm sounded ~25 minutes before, with no evidence it was seen. *(Fuente verificada 17-oct: HSE 1997,
  "The explosion and fires at the Texaco Refinery, Milford Haven, 24 July 1994", ISBN 0 7176 1413 1, párrafos 101, 102
  y 105. Ojo: el 275 sale de 1 de los 16 journals de alarmas, los 4 más relevantes se perdieron: es un mínimo.)*
- EEMUA target: ≤ 10 alarms in the first 10 minutes after a major upset (HSE Chemical Information Sheet No 6, citing EEMUA 191).
- LLM copilots can diagnose faults, but on the Tennessee Eastman Process (in every training set) **nobody checks whether
  the model reasons about the plant or recites the textbook.**

### 3. The invariant
`Statistics detect → the LLM proposes → a deterministic gate verifies → a human approves`
- PCA T² / SPE flags the fault and ranks the variables that moved.
- Gemma-4-31B-IT (AMD Token Factory) proposes 3 ranked causes with sensor evidence; k=5 samples, majority vote.
- The gate re-checks every cited sensor and direction against the data and strikes what the data does not support;
  a control-verb filter flags any command (open, close, set, start, stop…).
- The model has **no write access** to the process.
- Visual: diagrama de 4 cajas (el de "How it works" de la demo).

### 4. Demo: from alarm flood to one card
- Capturas de Live replay: alarmas desde el inicio de la falla → tarjeta → evidencia rechazada tachada → aprobar.
- "One card instead of the flood": median alarms per card [alarmas_por_tarjeta_mediana] = 5.5.
- Latency p50 / p95 per case: 22 s / 58 s [latencia_p50_s, latencia_p95_s]; cost per incident $0.00015 [coste_por_incidente].

### 5. The disguised twin: reasoning or reciting?
- Same plant, three levels: 0 = original TEP names · 1 = anonymous tags · 2 = full disguise (tags, units, components,
  equipment renamed; statistics identical).
- If the model recites, accuracy collapses with the disguise. If it reasons from signals, it holds.
- Visual: la misma tarjeta en nivel 0 y nivel 2 lado a lado.

### 6. Result: it reasons
- Rieth et al. 2017, 10 faults × 10 independent simulations, 100 cases per level, thinking off:
  top-1 **45 / 46 / 44 of 100** [rieth_n0_top1, rieth_n1_top1, rieth_n2_top1].
- Top-3 drop original → full disguise 5 pp, 95% CI [−4, 17] (cluster bootstrap by fault) [rieth_top3_caida_ic95_n0_n2]:
  not significant. Almost all of it is IDV8: 10 / 5 / 5 [rieth_idv8_top3]. IDV8 is the one fault where memory helps.
- Second model, Qwen3.8-27B: the disguise costs at most one case out of 12 (thinking off) [qwen_n*_top*].
- Nota honesta en pequeño: tamaño efectivo ~10 fallas, no 100 casos.

### 7. Thinking makes the model invent evidence; the gate catches it
- Braatz, same 36 cases with thinking off / on: top-1 11 → 15 of 36 [think_top1_pares], but the share of evidence the gate
  rejects rises **22% → 36%** per case [think_rechazo_medias]; higher in 9 of 12 faults, p = 0.0039 [think_rechazo_fallas,
  think_rechazo_fallas_wilcoxon_p].
- Qwen: same direction, weaker (31% → 36%, not significant) [qwen_think_rechazo_medias, qwen_think_rechazo_fallas_wilcoxon_p].
- **Variante A (si Rieth thinkpl + sd terminan):** [PENDIENTE 18-oct] "Replicated on Rieth, 100 cases per level, same
  deployment: rejection X% → Y%, higher in N of 10 faults" (solo si se sostiene dentro de cada falla).
- **Variante B (si no terminan):** no mencionar Rieth con thinking en la slide; en Limitations, "Rieth thinking arm
  partial, not reported".
- Mensaje: "The smarter the model, the more the gate matters."

### 8. The card arrives before the flood
- In 4 of 4 faults that flood, the card comes first [anticipacion_inundaciones]: 9, 615, 1,488 and 1,143 minutes ahead
  [anticipacion_minutos].
- Visual: línea de tiempo por falla (tarjeta vs inicio de inundación).

### 9. Benchmark: FaultExplainer protocol
- Their data, their PCA, their literal prompt. Top-3 on the faults their PCA detects:
  Gemma-4-31B **8/11** [replica_gemma_top3] · GPT-4o 7/11 · o1-preview 9/11 (their Table 1).
- Independent LLM annotator gives the same score [replica_anotador_gemma_top3].
- Cita: Khan et al. 2025, FaultExplainer (MIT).

### 10. Evolus: from approved card to work order
- Three blocks, all driven by API: agent "TEP Shift Copilot" on our AMD Token Factory connection, Knowledge Library
  "TEP process & procedures", AI Tool "translate".
- Same agent, two models (Gemma, Qwen): 6/6 handovers in English [evolus_v3_ingles], 0 control orders
  [evolus_v3_ordenes_control], disguised codes answered "no library entry", never guessed: 2/2
  [evolus_v3_disfrazado_sin_adivinar].
- Finding: Evolus injects a hidden "respond in Italian" default; Gemma wrote 2/3 handovers in Italian
  [evolus_v2_gemma_italiano] until an explicit language policy fixed it.

### 11. Audit-ready by construction
- Every number in README, deck and demo is recomputed from pinned runs: `SHA256SUMS` + `claims.json` +
  `scripts/verify_claims.py` (fails if any figure drifts).
- The demo replays real recorded runs: works offline, no GPU or key needed.
- Limitations stated: small Braatz samples (12 cases/level), effective n ≈ 10 faults on Rieth, PCA misses IDV 3, 4, 9.

### 12. Close
- "Every team will show you an AI that diagnoses faults. We show you one that proves it isn't reciting the textbook."
- Repo URL · demo URL · built on AMD Token Factory (Gemma-4-31B-IT) · Evolus.

---

## Guion del video (narración en inglés, ~4:30)

Producción: grabar pantalla a 1080p (OBS); la demo en Streamlit, pestaña Live replay ya cargada en IDV6 nivel 0.
Voz en off; se puede grabar la voz aparte y montarla. Los tiempos son orientativos.

**[0:00–0:25] Slide 1 → 2. Hook**
> In 1994, at the Milford Haven refinery, two operators faced 275 alarms in the last eleven minutes before an explosion,
> one every two to three seconds. The alarm that mattered had sounded 25 minutes earlier, and there is no evidence anyone
> saw it. Alarm floods are still how plant upsets look from the control room.

*(cita verificada: HSE 1997, párrafos 101, 102 y 105; ver slide 2)*

**[0:25–0:55] Slide 2. The real question**
> AI copilots can already name the cause of a fault. But they are tested on the Tennessee Eastman Process, a benchmark
> that sits in every training set. So does the model reason about the plant, or does it recite the textbook? Nobody
> checks. We did.

**[0:55–1:20] Slide 3. Invariant**
> TEP Copilot follows one rule. Statistics detect. Gemma 4, running on AMD Token Factory, proposes three causes and cites
> the sensors behind them. A deterministic gate re-checks every one of those claims against the data and strikes what
> the data does not support. And a human approves. The model never gets write access to the process.

**[1:20–2:20] Demo (pantalla, Live replay)**
> Here is a fault starting. Without the copilot, this is what the operator faces: alarms piling up. With it, one card.
> *(señalar la tarjeta)* Three ranked causes, the agreement between five samples, and the evidence. This sensor the
> model cited did not actually move that way, so the gate struck it out. The operator approves…
> *(clic en aprobar)* …and an Evolus agent, using a knowledge library of plant procedures, drafts the work order and the
> shift handover. Every action stays with the operator; the agent writes no control commands.
> *(mostrar la traducción)* An Evolus AI tool translates it for the next shift.

Nota: si el replay de Evolus de la demo sigue siendo la corrida de Qwen, decir "an Evolus agent" sin nombrar el modelo,
o cambiar la demo a la corrida Gemma v3 antes de grabar.

**[2:20–3:05] Slides 5–6. Disguised twin**
> Now the test. We built a disguised twin of the plant: every tag, unit, component and piece of equipment renamed, with
> identical statistics. If the model is reciting, accuracy should collapse. On ten faults with ten independent
> simulations each, top-1 accuracy is 45 out of 100 on the original plant and 44 out of 100 fully disguised. The model
> is reading the signals. The only fault where memory seems to help is IDV 8, and we report that too. A second model,
> Qwen, shows the same.

**[3:05–3:40] Slide 7. Thinking and the gate**
> Then we turned thinking on. Gemma gets a few more causes right, but the share of its evidence the gate rejects rises
> from 22 to 36 percent, in 9 of 12 faults. Thinking makes the model more confident about evidence that isn't there.
> The smarter the model, the more the gate matters.

*(variante A: añadir una frase con la réplica en Rieth si se sostiene dentro de cada falla)*

**[3:40–4:05] Slides 8–9. Early warning and benchmark**
> In every fault that floods the control room, the card arrives before the flood, from nine minutes to more than a day
> ahead. And on the published FaultExplainer protocol, Gemma 4 scores 8 of 11, between GPT-4o and o1-preview.

**[4:05–4:30] Slides 10–11. Evolus and audit**
> Evolus turns the approved card into paperwork, and along the way we found and fixed a hidden default that made the
> agent write in Italian. Every number you have seen is recomputed from recorded runs by a script, and the demo replays
> those runs, so it works offline.

**[4:30–4:45] Slide 12. Close**
> Every team will show you an AI that diagnoses faults. We show you one that proves it isn't reciting the textbook.

---

## Checklist de producción
- [x] Título: "TEP Copilot: reasoning, not reciting" (Diego, 17-oct).
- [x] Cita de Milford Haven verificada en el informe HSE de 1997 (17-oct).
- [ ] Demo: decidir si el replay de Evolus pasa a la corrida Gemma v3 (`agente_2026-10-16_biblioteca_gemma_v3`).
- [ ] Slide 7: variante A o B según el estado de Rieth a las 07:00 del 18-oct.
- [ ] Exportar deck a PDF; portada 16:9 = slide 1.
- [ ] `verify_claims.py` en verde justo antes de exportar el deck y de grabar.
