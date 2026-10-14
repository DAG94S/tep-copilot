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
LLM: Gemma 4 (31B en fp8 principal, 26B-A4B secundario; E2B/E4B para pruebas locales) en vLLM-ROCm
sobre 1×MI300X de AMD Developer Cloud, con modo *thinking* desactivado. Imagen fijada por digest (`vllm/vllm-openai-rocm`, v0.31.0).
Orquestación de negocio: Evolus (REST API), con el agente corriendo sobre nuestro propio endpoint vLLM.

## Comandos (se crean a medida que avanza el proyecto)
```bash
python3 scripts/descargar_datos.py             # pendiente: baja TEP y lo registra en SHA256SUMS
.venv/bin/python scripts/verify_claims.py       # verifica SHA256SUMS, claims.json y los marcadores del README (necesita numpy/scipy)
python3 -m streamlit run app/streamlit_app.py  # demo: replay de corridas grabadas / modo vivo
docker compose up --build                      # réplica containerizada
```

## Reglas duras
1. Prohibido commitear keys: `.env` local, `.env.example` versionado.
2. Datos: TEP de Rieth et al. 2017 (Harvard Dataverse, dominio público) y espejo Braatz d00–d21.
   Todo archivo de `data/` se registra en `SHA256SUMS`. `data/raw/` no se versiona (más de 1 GB).
   El archivo `Faulty_Testing` (~4 GB en RAM) se procesa en el droplet, no en WSL.
3. Todo número del README, del deck o de la demo sale de `data/runs/` o `data/processed/` vía script. Nada hardcodeado en la UI.
4. La demo debe funcionar con la GPU apagada: replay de corridas reales grabadas en MI300X (con SHA), incluidas las salidas de Evolus.
5. Español en código y docs internas; inglés en README, video y slides.
6. Cambios de umbral, protocolo o esquema externo (vLLM/Evolus) → `STATE.md` con fecha y error exacto.
7. GPU: campaña diseñada para ≤3 GPU-h. **Destruir el droplet** apenas termine (cobra aunque esté apagado). Guardar logs de arranque y del modelo.
8. Evolus: el workspace solo cuenta si se crea desde el enlace del evento (12 oct). Antes de eso, solo mocks.
9. Citar siempre el trabajo previo (FaultExplainer, MIT; ver `docs/ANTECEDENTES.md`). El código reutilizado va con su licencia y atribución.

## Estructura
`core/` detección determinista (datos TEP, alarmas, PCA T²/SPE, compuerta de sensores) ·
`llm/` cliente vLLM y prompts · `twin/` planta gemela disfrazada · `eval/` campañas de evaluación ·
`evolus/` cliente REST · `app/` demo · `knowledge/` documentos para la Knowledge Library ·
`scripts/` descarga y verificación · `tests/` · `data/{raw,processed,runs}` · `docs/` diseño y decisiones.
