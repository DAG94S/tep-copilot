# Textos para la entrega en lablab (borrador, 16 oct)

Todas las cifras salen de `claims.json` (verificadas con `scripts/verify_claims.py`). Si cambia un claim, cambiar aquí.
Contar caracteres antes de pegar: título ≤ 50, descripción corta ≤ 255, larga ≥ 100 palabras.

## Título (elegido por Diego el 17-oct: opción 3)
1. `TEP Copilot: an AI that proves it isn't reciting` (48)
2. `TEP Copilot: gate-verified root-cause cards` (43)
3. `TEP Copilot: reasoning, not reciting` (36)

## Descripción corta (≤ 255)
Control-room copilot for the Tennessee Eastman Process: statistics detect, Gemma proposes a root cause, a deterministic gate strikes unsupported evidence, a human approves. A disguised-plant probe shows it reasons instead of reciting.

(234 caracteres)

## Descripción larga (≥ 100 palabras)
In a plant upset, operators face alarm floods: at Milford Haven in 1994 it was 275 alarms in under 11 minutes. LLM copilots can diagnose faults, but on the Tennessee Eastman Process (TEP), a benchmark that sits in every training set, nobody checks whether the model reasons about the plant or recites the textbook.

TEP Copilot turns an alarm flood into one root-cause card. Statistics detect (PCA T²), Gemma-4-31B on AMD Token Factory proposes three causes with sensor evidence, a deterministic gate removes every claim the data does not support and blocks control verbs, and a human approves. The LLM has no write access to the process. After approval, an Evolus agent with a Knowledge Library drafts the work order and shift handover, and an Evolus AI Tool translates it for the next shift.

What we measured, every number recomputed from pinned runs by a script:
- **Reasoning, not reciting.** A disguised twin renames tags, units, components and equipment while keeping the statistics identical. On 10 faults × 10 independent simulations, top-1 accuracy stays at 45/100 on the original plant and 44/100 fully disguised; only IDV8 seems to lean on memory.
- **The gate matters more when the model thinks.** With thinking on, Gemma gets more right but the share of its evidence the gate rejects rises from 22% to 36% per case (worse in 9 of 12 faults, p = 0.004).
- **Early warning.** In 4 of 4 faults that flood, the card arrives before the flood.
- **Benchmark.** On the FaultExplainer protocol, Gemma-4-31B scores 8/11 vs GPT-4o 7/11 and o1-preview 9/11.

A second model (Qwen3.8-27B) confirms that the disguise does not break accuracy. The demo replays recorded runs, so it works offline.

(284 palabras)

## Reto y etiquetas
- Reto: **Intelligent Industry**. Además compite por el premio de Google (Gemma) y por el track de Evolus (Business Agents).
- Etiquetas: AMD Token Factory, Gemma, Google DeepMind, Evolus, Qwen, Streamlit, Python, Industrial AI, LLM evaluation.

## Pendiente de Diego
- ~~Elegir el título~~ → `TEP Copilot: reasoning, not reciting` (17-oct).
- Confirmar si se marca también el track de Evolus en el formulario.
- Cita de Milford Haven verificada (17-oct): HSE 1997, ISBN 0 7176 1413 1, párr. 102: "in the last 10.7 minutes before the explosion the two operators had to recognise, acknowledge and take appropriate action on 275 alarms"; párr. 101: una cada 2-3 s; párr. 105: alarma de nivel alto del flare drum a las 12:56, ~25 min antes, "no evidence that it was seen". PDF: https://www.icheme.org/media/13706/the-explosion-and-fires-at-the-texaco-refinery-milford-haven.pdf
