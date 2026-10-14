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
Gemma-4-31B-IT, thinking off, k=5 samples, T=0.7, majority vote, faults IDV 1-15 on the Rieth et al. (2017) data. PCA detects 12 of 15 faults (IDV 3, 4, 9 are never detected and are excluded); the denominator is the evaluable cases. Main campaign = original run re-gated plus retries of the invalid cases (see Limitations).

| Disguise level | top-1 | top-3 |
|---|---|---|
| 0 original names | <!--claim:combinado_n0_top1-->3/12<!--/claim--> | <!--claim:combinado_n0_top3-->7/12<!--/claim--> |
| 1 anonymous tags | <!--claim:combinado_n1_top1-->4/12<!--/claim--> | <!--claim:combinado_n1_top3-->6/12<!--/claim--> |
| 2 full disguise | <!--claim:combinado_n2_top1-->4/12<!--/claim--> | <!--claim:combinado_n2_top3-->6/12<!--/claim--> |

The gate rejected <!--claim:combinado_rechazo-->24%<!--/claim--> of the evidence claims the model made. Top-3 drops by one case between the original plant and the disguised twin, so the sample does not show a collapse; with 12 cases per level it also cannot show equivalence.

**FaultExplainer replication.** We ran the FaultExplainer protocol (Khan et al. 2025): their data, their PCA (reproduced exactly) and their literal prompt. Top-3 on the faults their PCA detects: Gemma-4-31B <!--claim:replica_gemma_top3-->8/11<!--/claim-->, GPT-4o 7/11 and o1-preview 9/11 (their Table 1). Gemma misses IDV <!--claim:replica_gemma_fallas-->8,10,14<!--/claim-->; their PCA does not detect IDV <!--claim:replica_gemma_no_detectadas-->3,4,9,15<!--/claim-->. Protocol differences: they use n=1 with the API default temperature and hand-scored aliases; we use k=5 with majority vote at T=0.7.

**Reasoning on vs off:** pending (campaign running; no numbers yet).

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
Tennessee Eastman Process, Rieth et al. (2017), Harvard Dataverse, doi:10.7910/DVN/6C3JR1 (public domain). The replication uses the CSVs shipped with FaultExplainer.

## Limitations
- Without thinking, Gemma performs modestly: top-1 stays at 3-4 of 12 and its errors fall mostly on the feed faults (IDV 7, 8, 1). IDV 15 is always misattributed to them.
- Detection is not ours to claim: the PCA misses IDV 3, 4 and 9.
- Token Factory's experimental Gemma deployment sometimes degenerated into garbage output ("y_y_y...") even at T=0.7, and did so in every T=0 test. Invalid cases (IDV 14-15) were retried after the server recovered; the combination rule is in `scripts/verify_claims.py`. No deterministic (T=0) arm exists.
- Small samples: 12 cases per level, one simulation run per fault, no confidence intervals.
- We have no `rocm-smi` or server logs of our own; AMD hardware use rests on the Token Factory endpoint and its usage record.
- The gate was changed after the first run (oscillating evidence is judged by RMS); both versions are in `claims.json`/STATE.md.

## License
MIT. Gemma weights are not included and remain under their own license.
