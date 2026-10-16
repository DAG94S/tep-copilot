# AGENTS.md — TEP Copilot (nombre provisional)

Copiloto de sala de control sobre el Tennessee Eastman Process (TEP) que **demuestra que razona y no recita**.
AMD Developer Hackathon ACT III (lablab.ai) · reto *Intelligent Industry* + premios Google (Gemma) y Evolus.
Solo + carga docente. Estándar audit-ready: nada se afirma sin script + dato pineado.
Diseño completo en `docs/PROYECTO.md`; viabilidad en `docs/VIABILIDAD.md`.

## Invariante (no negociable)
La estadística detecta → el LLM propone → la compuerta determinista verifica → el humano aprueba.
El LLM nunca tiene herramientas de escritura sobre el proceso ni emite verbos de control (abrir, cerrar, fijar, arrancar, parar).

## Stack
Python 3.11+, numpy/pandas/scikit-learn/scipy, pyreadr, pydantic, requests, Streamlit.
LLM: `Gemma-4-31B-IT` en **AMD Token Factory** (API OpenAI-compatible sobre hardware AMD; ACT III no dio crédito de GPU,
el FAQ oficial acepta Token Factory). k=5 llamadas separadas (no admite `n>1`), T=0,7 (T=0 degenera), thinking off por
defecto; brazo con thinking vía `--razonamiento minimal`. Límites: **20 RPM** y tokens/min por usuario → **máx. 2 procesos**
`eval.correr` a la vez; tope 1 USD/día que se reinicia a las 16:00 UTC (11:00 Ecuador).
Orquestación de negocio: Evolus (REST + agente OpenAI-compatible), agente "TEP Shift Copilot" sobre la conexión `amd`
(Token Factory → Gemma-4-31B-IT) + Knowledge Library `TEP process & procedures`.

## Comandos (se crean a medida que avanza el proyecto)
```bash
python3 scripts/descargar_datos.py             # Braatz d00–d21 → SHA256SUMS (Rieth: scripts/descargar_rieth.py)
.venv/bin/python -m eval.correr --campana X --backend AMD_TF ...  # campañas (ver STATE.md para los parámetros)
.venv/bin/python scripts/verify_claims.py       # verifica SHA256SUMS, claims.json y los marcadores del README (necesita numpy/scipy)
python3 -m streamlit run app/streamlit_app.py  # demo: replay de corridas grabadas / modo vivo
docker compose up --build                      # réplica containerizada
```

## Reglas duras
1. Prohibido commitear keys: `.env` local, `.env.example` versionado.
2. Datos: TEP de Rieth et al. 2017 (Harvard Dataverse, dominio público) y espejo Braatz d00–d21.
   Todo archivo de `data/` se registra en `SHA256SUMS`. `data/raw/` no se versiona (más de 1 GB), salvo `data/raw/braatz/` (26 MB, con su LICENSE): la demo la necesita.
   Rieth: solo los archivos *Training* (Faulty_Testing no cabe en la RAM de WSL); se extraen con R base, no pyreadr.
3. Todo número del README, del deck o de la demo sale de `data/runs/` o `data/processed/` vía script. Nada hardcodeado en la UI.
4. La demo debe funcionar sin red: replay de corridas reales grabadas en Token Factory (con SHA), incluidas las salidas de Evolus.
5. Español en código y docs internas; inglés en README, video y slides.
6. Cambios de umbral, protocolo o esquema externo (Token Factory/Evolus) → `STATE.md` con fecha y error exacto.
   Toda asociación caso a caso se comprueba **dentro de cada falla** antes de afirmarla (las corridas de una falla se parecen).
7. Corridas con LLM: registros ERROR_LLM (429/500) se apartan a `errores_429.jsonl` y se reanuda con `--continuar`;
   reintentos de INVALIDO en carpeta aparte. Nada se pinea con errores dentro.
8. Evolus: el workspace solo cuenta si se crea desde el enlace del evento (12 oct). Antes de eso, solo mocks.
9. Citar siempre el trabajo previo (FaultExplainer, MIT; ver `docs/ANTECEDENTES.md`). El código reutilizado va con su licencia y atribución.

## Estructura
`core/` detección determinista (datos TEP, alarmas, PCA T²/SPE, compuerta de sensores) ·
`llm/` cliente OpenAI-compatible (Token Factory) y prompts · `twin/` planta gemela disfrazada · `eval/` campañas de evaluación ·
`evolus/` cliente REST · `app/` demo · `knowledge/` documentos para la Knowledge Library ·
`scripts/` descarga y verificación · `tests/` · `data/{raw,processed,runs}` · `docs/` diseño y decisiones.
