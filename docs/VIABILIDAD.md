# VIABILIDAD — verificada el 2026-10-09

Validación hecha por un subagente, con evidencia observada (URL o comando). Veredicto global: **ejecutable con cambios**.

| # | Requisito | Veredicto | Evidencia | Mitigación |
|---|---|---|---|---|
| 1 | Datos TEP (Rieth 2017) | GO (riesgo de RAM) | API de Dataverse: 4 archivos sin restricción, descarga sin login (303 a S3). Se probó FaultFree_Training (24,7 MB, md5 OK); `pyreadr` lo lee como (250000, 55). Dominio público. Faulty_Training 494 MB, Faulty_Testing 837 MB | Procesar Faulty_Testing (~4 GB en RAM) en el droplet. En local usar el espejo Braatz d00–d21 (github jkitchin/tennessee-eastman-profbraatz) |
| 2 | Descripción del proceso | GO | FaultExplainer `backend/prompts.py` (`INTRO_MESSAGE`: reacciones, 41 XMEAS + 11 XMV, 15 IDV) y `cg.adjlist`. Repo MIT | No copiar el paper (CC BY-NC-ND 4.0); redibujar el diagrama de flujo |
| 3 | FaultExplainer | GO | LICENSE MIT. Tabla 1 del paper: GPT-4o **7/11**, o1-preview 9/11 | Replicar el protocolo exacto; ojo, su prompt dice "16 causas" pero enumera 15 |
| 4 | Simulador TEP | RIESGO (opcional) | `tep2py` y `pytep` no están en PyPI (pytep necesita MATLAB). jkitchin `tep-sim` solo se instala desde git | Fuera de la ruta crítica |
| 5 | Gemma 4 en vLLM | GO | La receta de vLLM pone 31B y 26B-A4B en 1×MI300X. HF: no gated, apache-2.0. Imagen `vllm-openai-rocm` v0.31.0 (2026-10-04) | Fijar por digest; `TRITON_ATTN` |
| 6 | AMD Developer Cloud | RIESGO (plazo) | Aprobación en 2–3 días hábiles; los créditos caducan 30 días tras activarlos. MI300X a $1,99/h, cobra aunque esté apagado | $100 ≈ 50 h. 31B fp8 ≈ 1.219 tok/s → la campaña de unas 12k llamadas cabe en menos de 2 h |
| 7 | Evolus | RIESGO | Documentados: `POST /api/v1/workflows/{id}/execute`, `/ai-tools/{tool}/run`, `run-file`, libraries, modelo propio con vLLM, 60 peticiones/min. El workspace debe crearse desde el enlace del evento | Coste en créditos por llamada sin verificar → medirlo el 12 oct |
| 8 | Premio Google | NO VERIFICADO | La página solo dice "$5,000 in prizes from Google". En el ACT II fue para Gemma | Preguntar en Discord |
| 9 | Hosting de la demo | RIESGO | HF Docker Spaces es de pago. Render free: 512 MB, se duerme. Streamlit Cloud: 2,7 GB, hiberna a las 12 h | Streamlit Cloud con replay liviano; Render de respaldo |
| 10 | GPU local (GTX 1060) | GO (E2B) | Driver 582.66 (Ollama pide ≥570). `gemma4:e2b-it-qat` 4,3 GB; `e4b-it-qat` 6,1 GB | E4B se reparte con la CPU; sin probar |
| 11 | Originalidad | RIESGO | Zhou & Liang (IEEE DataPort, 13-sep-2026): 1.676 corridas TEP, 13.273 llamadas a LLM, calibración conformal. AgentRCA (arXiv 2607.22385) y ADMITBench (arXiv 2608.03866): **citas del subagente sin verificar a mano** | Lo defendible es la gemela disfrazada; citar el resto |
| 12 | Calendario | RIESGO | Cierre: 18 oct 10:00 hora de Ecuador | Ver los riesgos en `PROYECTO.md` |

Correcciones al diseño que salieron de esta validación:
- La línea base es 7/11, no 6/11.
- Se agrega la Gemma 4 12B al Pareto.
- La 31B se sirve en fp8.
- Modo *thinking* desactivado.
- El agente principal tiene que vivir dentro de Evolus.
- Las fechas del workspace de Evolus no coinciden: 31 oct según lablab, 15 nov según Evolus.
