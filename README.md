# TEP Copilot (working title)

**A control-room copilot that turns an alarm flood into one gate-verified root-cause card, and measures whether the model reasons about the plant or just recites the Tennessee Eastman textbook.**

Built for the AMD Developer Hackathon ACT III (lablab.ai), *Intelligent Industry* challenge, with the Google (Gemma) and Evolus tracks.
LLM: Gemma-4-31B-IT served on AMD hardware through AMD Token Factory (OpenAI-compatible API).

## What it does
Statistics detect → the LLM proposes → a deterministic gate verifies → a human approves.

1. A PCA T² / SPE detector (`core/`) flags the fault and ranks the variables that moved.
2. Gemma proposes three ranked root causes and cites sensor evidence (`llm/`), k=5 samples, majority vote.
3. A deterministic gate (`core/compuerta`) re-checks every cited claim against the data and rejects what the data does not support.
4. A human approves the card. The model has no write tools on the process and a control-verb filter flags any output phrased as a command to open, close, set, start, stop (and similar).

The differentiator is the **disguised twin** (`twin/`): the same plant at three levels, 0 = original TEP names, 1 = anonymous tags, 2 = full disguise. If the model recites TEP from memory, accuracy should collapse as the disguise grows. If it reasons from signals, it should not.

## Results
Gemma-4-31B-IT, thinking off, k=5 samples, T=0.7, majority vote, faults IDV 1-15 on the classic Braatz TEP test set (`d01_te`–`d15_te`, one simulation per fault). PCA detects 12 of 15 faults (IDV 3, 4, 9 are never detected and are excluded); the denominator is the evaluable cases. Main campaign = original run re-gated plus retries of the invalid cases (see Limitations).

| Disguise level | top-1 | top-3 |
|---|---|---|
| 0 original names | <!--claim:combinado_n0_top1-->3/12<!--/claim--> | <!--claim:combinado_n0_top3-->7/12<!--/claim--> |
| 1 anonymous tags | <!--claim:combinado_n1_top1-->4/12<!--/claim--> | <!--claim:combinado_n1_top3-->6/12<!--/claim--> |
| 2 full disguise | <!--claim:combinado_n2_top1-->4/12<!--/claim--> | <!--claim:combinado_n2_top3-->6/12<!--/claim--> |

The gate rejected <!--claim:combinado_rechazo-->24%<!--/claim--> of the evidence claims the model made. Top-3 drops by one case between the original plant and the disguised twin, so the sample does not show a collapse; with 12 cases per level it also cannot show equivalence.

**FaultExplainer replication.** We ran the FaultExplainer protocol (Khan et al. 2025): their data, their PCA (reproduced exactly) and their literal prompt. Top-3 on the faults their PCA detects: Gemma-4-31B <!--claim:replica_gemma_top3-->8/11<!--/claim-->, GPT-4o 7/11 and o1-preview 9/11 (their Table 1). Gemma misses IDV <!--claim:replica_gemma_fallas-->8,10,14<!--/claim-->; their PCA does not detect IDV <!--claim:replica_gemma_no_detectadas-->3,4,9,15<!--/claim-->. Protocol differences: they use n=1 with the API default temperature and hand-scored aliases; we use k=5 with majority vote at T=0.7. Free-text answers are scored by reading the three causes the model proposes; an independent LLM annotator (DeepSeek-V4-Flash, `eval/extraer_causas_llm.py`) gives the same result fault by fault: Gemma <!--claim:replica_anotador_gemma_top3-->8/11<!--/claim-->.

## Robust results: does the disguise cost accuracy?
**Robust check on Rieth et al. (thinking off).** 10 faults x 10 independent simulations per level (100 cases per level), same model and protocol as above.

| Disguise level | top-1 | top-3 |
|---|---|---|
| 0 original names | <!--claim:rieth_n0_top1-->45/100<!--/claim--> | <!--claim:rieth_n0_top3-->74/100<!--/claim--> |
| 1 anonymous tags | <!--claim:rieth_n1_top1-->46/100<!--/claim--> | <!--claim:rieth_n1_top3-->67/100<!--/claim--> |
| 2 full disguise | <!--claim:rieth_n2_top1-->44/100<!--/claim--> | <!--claim:rieth_n2_top3-->69/100<!--/claim--> |

- Top-1 does not change with the disguise. Top-3 drops a few points, almost entirely from IDV8 (feed A/B/C composition): its top-3 hits go <!--claim:rieth_idv8_top3-->10/5/5<!--/claim--> across levels 0/1/2 (out of 10 each). IDV8 is the one fault where TEP-specific memory seems to help.
- Runs within a fault behave almost identically (a fault is mostly right or mostly wrong in all its runs), so the effective sample is about 10 faults, not 100 cases. The confidence interval therefore resamples whole faults (cluster bootstrap, 5000 replicates, fixed seed).
- Paired by case, original vs full disguise, discordant top-3 cases (right only in the original vs right only in the disguise): <!--claim:rieth_top3_pareado_n0_n2-->7 vs 2<!--/claim-->; McNemar exact p = <!--claim:rieth_top3_mcnemar_p_n0_n2-->0.18<!--/claim-->. Mean top-3 drop <!--claim:rieth_top3_caida_ic95_n0_n2-->5 pp [-4, 17]<!--/claim--> (95% CI). The drop is not statistically significant.
- Original vs anonymous tags: discordant <!--claim:rieth_top3_pareado_n0_n1-->8 vs 1<!--/claim-->, p = <!--claim:rieth_top3_mcnemar_p_n0_n1-->0.04<!--/claim-->, drop <!--claim:rieth_top3_caida_ic95_n0_n1-->7 pp [0, 18]<!--/claim-->. This p-value treats cases as independent and so overstates the evidence; the cluster CI touches zero.

**Thinking on (Braatz data, 12 evaluable cases per level; 3 of 15 faults are never detected).** Accuracy barely moves with the disguise, but reasoning effort rises.

| Disguise level | top-1 | top-3 |
|---|---|---|
| 0 original names | <!--claim:think_n0_top1-->5/12<!--/claim--> | <!--claim:think_n0_top3-->8/12<!--/claim--> |
| 1 anonymous tags | <!--claim:think_n1_top1-->5/12<!--/claim--> | <!--claim:think_n1_top3-->9/12<!--/claim--> |
| 2 full disguise | <!--claim:think_n2_top1-->5/12<!--/claim--> | <!--claim:think_n2_top3-->7/12<!--/claim--> |

Median reasoning tokens per case (k=5 calls) at levels 0 / 1 / 2: <!--claim:think_razonamiento_mediana-->16750 / 21215 / 22528<!--/claim-->. Median seconds per case: <!--claim:think_segundos_mediana-->451 / 694 / 702<!--/claim-->.

**Thinking makes the model invent more evidence.** Same 36 cases (12 faults × 3 levels) with thinking off and on: top-1 goes from <!--claim:think_top1_pares-->11 / 15 of 36<!--/claim--> (off / on), but the share of each card's evidence that the gate rejects as unsupported by the data rises from <!--claim:think_rechazo_medias-->22% / 36%<!--/claim--> (mean per case; rejected/claimed in total: <!--claim:think_afirmaciones-->35/143 / 68/182<!--/claim-->). Rejection is higher / lower / equal with thinking in <!--claim:think_rechazo_pares-->24 / 2 / 10<!--/claim--> cases (Wilcoxon p = <!--claim:think_rechazo_wilcoxon_p-->0.00015<!--/claim-->). Because the levels of one fault are not independent, we also average each fault over its levels: higher / lower / equal in <!--claim:think_rechazo_fallas-->9 / 1 / 2<!--/claim--> faults, Wilcoxon p = <!--claim:think_rechazo_fallas_wilcoxon_p-->0.0039<!--/claim-->. The gate matters more, not less, with a model that reasons.

**The disguise costs the model effort, not accuracy, except on IDV8.** The Rieth arm with thinking was stopped at 95/200 cases when Gemma-4-31B-IT was removed from Token Factory on 15 Oct; no numbers from it are reported.

## Second model: Qwen3.8-27B (same protocol, same AMD Token Factory)

We repeated the Braatz campaigns with Qwen3.8-27B, the closest model left on Token Factory (dense, similar size, same price). One run per fault, 12 evaluable cases per level, so treat these as consistency checks, not as a model ranking.

| Disguise level | Qwen top-1 (thinking off / on) | Qwen top-3 (thinking off / on) |
|---|---|---|
| 0 original names | <!--claim:qwen_n0_top1-->7/12<!--/claim--> / <!--claim:qwen_think_n0_top1-->4/12<!--/claim--> | <!--claim:qwen_n0_top3-->9/12<!--/claim--> / <!--claim:qwen_think_n0_top3-->7/12<!--/claim--> |
| 1 anonymous tags | <!--claim:qwen_n1_top1-->6/12<!--/claim--> / <!--claim:qwen_think_n1_top1-->4/12<!--/claim--> | <!--claim:qwen_n1_top3-->9/12<!--/claim--> / <!--claim:qwen_think_n1_top3-->6/12<!--/claim--> |
| 2 full disguise | <!--claim:qwen_n2_top1-->6/12<!--/claim--> / <!--claim:qwen_think_n2_top1-->5/12<!--/claim--> | <!--claim:qwen_n2_top3-->8/12<!--/claim--> / <!--claim:qwen_think_n2_top3-->5/12<!--/claim--> |

- **Qwen does not recite TEP either:** without thinking, the disguise costs one case at most.
- **The gate catches more unsupported evidence from Qwen than from Gemma:** mean rejection per case Gemma / Qwen <!--claim:qwen_vs_gemma_rechazo_medias-->22% / 31%<!--/claim-->; higher / lower / equal for Qwen in <!--claim:qwen_vs_gemma_rechazo_fallas-->9 / 2 / 1<!--/claim--> faults (Wilcoxon p = <!--claim:qwen_vs_gemma_rechazo_fallas_wilcoxon_p-->0.04<!--/claim-->, borderline with 12 faults).
- **Thinking is not a free upgrade:** for Qwen it lowers top-1 (off / on: <!--claim:qwen_think_top1_pares-->19 / 13 of 36<!--/claim-->), while mean rejection per case goes <!--claim:qwen_think_rechazo_medias-->31% / 36%<!--/claim-->; by fault higher / lower / equal in <!--claim:qwen_think_rechazo_fallas-->7 / 2 / 3<!--/claim--> (p = <!--claim:qwen_think_rechazo_fallas_wilcoxon_p-->0.074<!--/claim-->, not significant). Same direction as Gemma, weaker. Qwen thinking used `reasoning_effort=low`, the lowest level it accepts (Gemma used `minimal`).
- **FaultExplainer replication with Qwen:** <!--claim:replica_anotador_qwen_top3-->5/11<!--/claim--> (hits on IDV <!--claim:replica_anotador_qwen_fallas-->1,5,6,7,12<!--/claim-->), scored by the LLM annotator; Qwen's free-text answers run up to 30,000 characters and list many causes before concluding, so first-mention scoring is unreliable for it. Qwen beats Gemma with our structured JSON contract and loses to it on free text: the format matters.

## How we keep it honest
- `SHA256SUMS` pins every file under `data/`, the recorded runs and the vendored FaultExplainer commit.
- `claims.json` defines each number; `scripts/verify_claims.py` recomputes it from the recorded JSONL.
- Every figure in this README is wrapped in a claim marker; the same script checks that each marker matches `claims.json` and fails otherwise.
- The demo replays real recorded runs, so it works without any GPU or API key.

```bash
python3 scripts/verify_claims.py   # checks hashes, recomputes claims, checks README markers
```

## Architecture
`core/` TEP data, alarms, PCA T²/SPE, evidence gate · `llm/` OpenAI-compatible client and prompts · `twin/` disguised plant · `eval/` campaigns and re-gating · `evolus/` Evolus REST client and agent instructions · `app/` Streamlit demo (control room, audit, how it works) · `knowledge/` documents for Evolus Knowledge Library · `scripts/` download, verification, probes.

## Evolus integration
The agent "TEP Shift Copilot" runs on the Token Factory connection (Gemma-4-31B-IT, reasoning left at the model default, i.e. thinking off, as in the main campaign). From a diagnosis that is already approved, it drafts a work order and a shift handover, citing only gate-verified evidence as support (rejected evidence is passed along, labelled as rejected). Its output goes through the same control-verb filter. The recorded run `data/runs/evolus/agente_2026-10-14_sinrazonamiento` has <!--claim:evolus_llamadas-->2<!--/claim--> real calls (IDV 6, levels 0 and 2) and <!--claim:evolus_ordenes_control-->0<!--/claim--> control orders in the output. The quality is shallow (the agent has no Knowledge Library yet), and the exact exchanges are saved. We have not received an official answer on whether a Token Factory model counts for the Evolus track.

## Run it
```bash
cp .env.example .env                           # fill in only to run live; never commit .env
pip install -r requirements.txt
python3 scripts/verify_claims.py               # hashes, claims and README markers
python3 -m streamlit run app/streamlit_app.py  # demo: replay of recorded runs
docker compose up --build                      # containerized demo on :8501
python3 -m pytest -q tests/
```
The TEP data download (`python3 scripts/descargar_datos.py`) is only needed for new live runs; `data/raw/` is not versioned.

## Prior work & attribution
- FaultExplainer (Khan, Nahar, Chen, Flores, Li; *Computers & Chemical Engineering* 2025; arXiv 2412.14492; github.com/li-group/FaultExplainer, MIT). Vendored at commit `2fcfee97` in `third_party/faultexplainer/` with its license; our replication uses their code and prompt.
- TEP RCA Workbench (Chennan Li): near-identical architecture (deterministic detection, read-only tools, human gate, control-verb regex).
- Also: AIChE 2025 multi-agent RAG on TEP; Kunze & Fay 2025 (causal graph for alarm-flood root cause); Zhou & Liang 2026 (LLM calibration on TEP, IEEE DataPort).
- A copilot with a human in the loop is not novel by itself. What we add is the disguised-twin probe, which we have not found in prior work, and a verification pipeline for every number.

## Data
- Main campaign and thinking arm: Braatz TEP data (Russell, Chiang & Braatz 2000; Downs & Vogel 1993 simulator), mirror github.com/jkitchin/tennessee-eastman-profbraatz at a pinned commit (license in `data/raw/braatz/LICENSE`).
- Robust check: Rieth et al. (2017), Harvard Dataverse, doi:10.7910/DVN/6C3JR1 (public domain), training files, simulation runs 1-10 per fault (`data/processed/rieth/PROCEDENCIA.md`).
- FaultExplainer replication: the CSVs shipped with FaultExplainer.

## Limitations
- Without thinking, Gemma performs modestly: top-1 stays at 3-4 of 12 and its errors fall mostly on the feed faults (IDV 7, 8, 1). IDV 15 is always misattributed to them.
- Detection is not ours to claim: the PCA misses IDV 3, 4 and 9.
- Token Factory's experimental Gemma deployment sometimes degenerated into garbage output ("y_y_y...") even at T=0.7, and did so in every T=0 test. Invalid cases (IDV 14-15) were retried after the server recovered; the combination rule is in `scripts/verify_claims.py`. No deterministic (T=0) arm exists.
- Small samples: the main and thinking campaigns have 12 cases per level (one run per fault, no confidence intervals). The Rieth check has 100 cases per level but only 10 faults, and runs of one fault are nearly identical, so its effective size is about 10; the McNemar p-values ignore that clustering, the bootstrap CI does not. Thinking-on results are not yet replicated on Rieth.
- We have no `rocm-smi` or server logs of our own; AMD hardware use rests on the Token Factory endpoint and its usage record.
- The gate was changed after the first run (oscillating evidence is judged by RMS); both versions are in `claims.json`/STATE.md.

## License
MIT. Gemma weights are not included and remain under their own license.
