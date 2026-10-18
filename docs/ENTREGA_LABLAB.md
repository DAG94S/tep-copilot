# Textos para la entrega en lablab (v2, 18 oct)

Todas las cifras salen de `claims.json` (verificadas con `scripts/verify_claims.py`). Si cambia un claim, cambiar aquí.
Límites del formulario (guía de lablab): título 5-50, descripción corta 50-255, larga 600-2000 caracteres; video MP4 ≤ 300 MB; slides en PDF.

## Título (elegido por Diego el 17-oct: opción 3)
1. `TEP Copilot: an AI that proves it isn't reciting` (48)
2. `TEP Copilot: gate-verified root-cause cards` (43)
3. `TEP Copilot: reasoning, not reciting` (36)

## Descripción corta (50-255 caracteres; v2, 18-oct)
Control-room copilot for refineries and chemical plants: Gemma 4 on AMD proposes the root cause of an alarm flood, a deterministic gate strikes unsupported evidence, a human approves. A disguised twin tests that it reasons, not recites.

(236 caracteres)

## Descripción larga (600-2000 caracteres; v2, 18-oct, alineada con el pitch v3)
In a plant upset, operators drown in alarms: at Milford Haven in 1994, two operators faced 275 alarms in under 11 minutes. Plants now want AI copilots in that room, but an AI that sounds right and is wrong is one more alarm.

TEP Copilot turns an alarm flood into one root-cause card the operator can check. Statistics detect the fault (PCA T²); Gemma-4-31B-IT on AMD Token Factory proposes three ranked causes with sensor evidence; a deterministic gate strikes every claim the data does not support and flags control verbs; a human approves. The model has no write access to the process. After approval, an Evolus agent with a Knowledge Library drafts the work order and shift handover, and an Evolus AI Tool translates it.

Does it reason or recite? TEP has been public since 1993, so we tested it as an experiment: 2 public datasets, 2 models, 3 disguise levels, thinking off/on, k=5 samples, comparisons within each fault.
- A disguised twin renames every tag and unit: Gemma top-1 stays at 45/100 on the original plant and 44/100 fully disguised.
- Two models: Qwen3.8-27B names the top cause more often, but the gate rejects more of its evidence (31% vs 22%, 9 of 12 faults).
- Thinking on raises the evidence the gate rejects from 22% to 36% (9 of 12 faults).
- The card arrives before the alarm flood in 4 of 4 flooding faults.
- FaultExplainer protocol: Gemma 8/11, between GPT-4o (7/11) and o1-preview (9/11).

For refinery and chemical-plant control rooms; estimated inference cost $0.00015 per incident. Every result is recomputed by a script from pinned runs; the demo replays them offline.

(1603 caracteres. La línea de thinking es provisional: se completa con la réplica en Rieth.)

## Reto y etiquetas
- Reto: **Intelligent Industry**. Además compite por el premio de Google (Gemma) y por el track de Evolus (Business Agents).
- Etiquetas: AMD Token Factory, Gemma, Google DeepMind, Evolus, Qwen, Streamlit, Python, Industrial AI, LLM evaluation.

## Pendiente de Diego
- ~~Elegir el título~~ → `TEP Copilot: reasoning, not reciting` (17-oct).
- Confirmar si se marca también el track de Evolus en el formulario.
- Cita de Milford Haven verificada (17-oct): HSE 1997, ISBN 0 7176 1413 1, párr. 102: "in the last 10.7 minutes before the explosion the two operators had to recognise, acknowledge and take appropriate action on 275 alarms"; párr. 101: una cada 2-3 s; párr. 105: alarma de nivel alto del flare drum a las 12:56, ~25 min antes, "no evidence that it was seen". PDF: https://www.icheme.org/media/13706/the-explosion-and-fires-at-the-texaco-refinery-milford-haven.pdf
