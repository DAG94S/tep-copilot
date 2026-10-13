# STATE.md — TEP Copilot: registro de decisiones y avances

## 2026-10-09 — Cambio de proyecto y decisiones base
- **Se descarta AuditCorp-EC (SERCOP/SRI).** Motivo: los premios principales del ACT III solo se dan en 4 retos
  (Intelligent Industry, Health, Commerce, Experience) y la idea de compras públicas no encaja en ninguno.
  Solo competía por Evolus (créditos de plataforma, no efectivo). Además, su validación era circular (casos sintéticos).
- **Proyecto elegido:** copiloto de sala de control sobre el Tennessee Eastman Process que demuestra que razona.
  Reto *Intelligent Industry*, más los premios de Google (se asume Gemma, sin confirmar) y Evolus.
- **Diferenciador:** la sonda de **planta gemela disfrazada**. Es la única pieza sin antecedente encontrado;
  la calibración, la compuerta y el Pareto ya tienen trabajo previo en 2026 (ver `docs/ANTECEDENTES.md`).
- **Línea base:** FaultExplainer, GPT-4o 7/11 y o1-preview 9/11 (no 6/11, corregido). Su protocolo:
  PCA al 90%, T² con α=0,01, 6 alarmas consecutivas, top-6 contribuciones, 15 causas, acierto si la causa está en el top-3,
  n=1 por falla. Se replicará tal cual y aparte se reportará una versión robusta (n≥10, con SPE).
- **Modelo:** Gemma 4 31B (fp8) + 26B-A4B en 1×MI300X; E2B/E4B en local. Apache-2.0, no gated. Modo *thinking* desactivado.
- **Hosting de la demo:** Streamlit Community Cloud, con Render como respaldo (HF Docker Spaces ya es de pago).
- **Deadline:** 18 oct 15:00 UTC = **10:00 hora de Ecuador**.
- **Viabilidad:** ejecutable con cambios (`docs/VIABILIDAD.md`).
- **Carpeta:** se borró todo lo de AuditCorp-EC. Respaldo temporal en el scratchpad de la sesión
  (`respaldo_auditcorp_2026-10-09.tgz`). Se creó la estructura nueva.

## Pendiente antes del kickoff (12 oct)
Ver `docs/CHECKLIST.md`.

## 2026-10-09 (tarde) — Mudanza a WSL
- El proyecto pasa de OneDrive (`10_Investigacion/AMD_HACKATON`) a `~/proyectos/tep-copilot`. Motivos: TEP pesa ~1,3 GB (no debe
  sincronizarse con OneDrive), `/mnt/e` es lento para pip/Docker/git y OneDrive puede bloquear archivos. Copia verificada con SHA-256
  (25 archivos idénticos). En OneDrive solo queda `LEEME.md` apuntando aquí.
- `git init -b main`: archivos en staging, sin commit todavía.
- La memoria engram del proyecto sigue con la clave `amd_hackaton`.

## 2026-10-09 (noche) — Inscripción y crédito de GPU
- Inscrito en el ACT III; equipo `TEP_copilot` (solo, Closed); conectado al Discord de lablab.
- Solicitud de crédito AMD Developer Cloud enviada (perfiles: ORCID y GitHub DAG94S). AMD avisa demoras de hasta 5 días hábiles
  (podría llegar el 16 oct). Correo a devcloudrequests@amd.com enviado pidiendo prioridad por la fecha límite.
- **Plan B con fecha de corte:** si el martes 13 oct no hay crédito, pago por uso en AMD Developer Cloud
  (MI300X ≈ $1,99/h; campaña mínima ≈ 3 GPU-h ≈ $6; realista 10–20 h ≈ $20–40). Requiere tarjeta.
- Riesgo abierto: el crédito de $100 es solo para cuentas ADP nuevas; si la cuenta del usuario ya existía puede rechazarse.
- Preguntas pendientes en Discord (#ineedhelp): pods/créditos por equipo en el ACT III y qué tecnología cuenta para el premio de Google.

## 2026-10-09 (noche) — Datos y primer detector
- `scripts/descargar_datos.py`: espejo Braatz d00–d21 (commit `9a6c8e5f…`, licencia tipo NCSA/UIUC con atribución).
  46 archivos, 26 MB, SHA-256 en `SHA256SUMS`; segunda ejecución verifica sin cambios.
- **Schema externo:** `d00.dat` viene TRANSPUESTO (52×500, no 480×52 como indica el README del espejo).
  Normalizado en `core/datos.py`.
- `core/pca_t2.py`: PCA 90%, T² α=0,01, 6 alarmas consecutivas, contribuciones de Kourti-MacGregor. Con d00 como entrenamiento
  (500 muestras): A=31 componentes, UCL=57,02; sin falsas alarmas en d00_te.
  No detectadas: IDV 3, 9, 15 y 19. FaultExplainer reporta 3, 4, 9, 15 (usa otros datos: Rieth). **Aún no es una réplica**;
  falta correr con Rieth y fijar el protocolo exacto antes de comparar con su 7/11.
- Entorno: `.venv` (ignorado por git), `pytest` en `requirements.txt`.

## 2026-10-12 — Kickoff · planta gemela (`twin/`)
- Crédito AMD: el portal no muestra el estado de la solicitud; solo llega por correo. Sin aprobación a la fecha.
  Corte del plan B sigue siendo el martes 13.
- `core/tep.py`: variables, unidades, 15 causas y descripción del proceso **como plantillas** (Downs & Vogel 1993).
- `twin/gemela.py`: tres niveles anidados de disfraz (semilla 20261012):
  0 = TEP original · 1 = sin nombre/tags XMEAS/IDV, variables reordenadas, catálogo barajado con códigos ·
  2 = además componentes (K–U), corrientes de 3 dígitos, equipos (converter, flash drum…) y unidades (°F, psig, lb/h…).
- **Decisión de protocolo:** la sonda compara niveles 0/1/2 renderizados desde la *misma* plantilla propia, así el contenido
  físico es idéntico por construcción. La réplica de FaultExplainer es un brazo aparte con su `prompts.py` (MIT) tal cual.
- Garantía verificada por test: los datos gemelos son afines por columna + permutación → T², primera alarma y contribuciones
  idénticas a TEP (rtol 1e-6) en IDV 1, 6 y 14. Detector de fugas (regex) bloquea cualquier vista que deje ver TEP.
- 23 tests en verde.
- `core/compuerta.py` + `core/esquema.py`: contrato JSON (claves en inglés, sin campo de acciones), verificación de causas
  contra el catálogo, órdenes de control (regex de imperativos; lo descriptivo pasa), evidencia con |z| mediano ≥ 3 y signo
  coherente, voto entre k muestras (acuerdo < 60% → INCIERTO). Estados: VERIFICADO / PARCIAL / BLOQUEADO / INCIERTO.
- `core/pca_t2.py`: SPE con límite de Jackson & Mudholkar (extensión nuestra; el protocolo FaultExplainer sigue en T²).
  `core/alarmas.py`: límites por percentil 99,9 de d00, solo XMEAS, retardo 2, inundación EEMUA (>10 en 10 min).
- **Problema abierto (medido):** con d00 (500 muestras) como entrenamiento, SPE > límite en el **15%** de d00_te
  (límite 11,61) y hay **178** eventos de alarma en d00_te. d01_te sí inunda (máx. 12 en 10 min; 2 antes de la falla).
  Hipótesis sin verificar: 500 muestras no bastan para el percentil 99,9 ni para el subespacio residual.
  Opción: calibrar límites con los tramos normales previos a la falla (índices 0–159) de los 21 `dXX_te`, o con
  FaultFree_Training de Rieth. Test marcado `xfail(strict=True)` hasta resolverlo.

## 2026-10-12 (noche) — Workspace de Evolus creado desde el evento
- Workspace `TEP_copilot` creado en app.evolus.ai con el código de evento **AMDACT3**: 50.000 créditos, activo hasta el
  **15 nov 2026, 17:59** (la página de lablab decía 31 oct; vale lo que muestra Evolus). Sin tarjeta.
- API key guardada en `.env` (ignorado por git, chmod 600). Se mostró en el chat de la sesión → **rotarla**.
- **Esquema externo (verificado):** `GET /api/v1/ai-tools` solo con `X-ApiKey` → `401 auth.unauthorized`.
  Según evolus.ai/developers, también hace falta `X-Application-Id` (ID del espacio, en la página "API keys").
  El chat del agente usa otra base: `https://api.evolus.ai/v1` con `Authorization: Bearer`.
  Las llamadas a un modelo propio (vLLM) no consumen créditos de Evolus.
- Con `X-ApiKey` + `X-Application-Id` → `GET /api/v1/ai-tools` 200: 11 herramientas (doc-structure, translate, summarize,
  email, rewrite, simplify, anonymize, tables, minutes, sentiment, compare). `GET /v1/models` (Bearer) 200, sin agentes aún.
- **Coste medido:** `POST /api/v1/ai-tools/translate/run` con body `{"text", "options": {"target": "es", "style"}}`
  → 200 en 3,0 s, `creditsConsumed` = **1,358** por una frase de 85 caracteres (`data/runs/evolus/prueba_translate_2026-10-12.json`).
  Con 50.000 créditos el presupuesto de Evolus no es una restricción.
- **Decisión de Diego:** no se rota la API key de Evolus (riesgo aceptado: workspace del evento, créditos gratuitos).
- Premio de Google: nada en Discord a la fecha. **Supuesto de trabajo:** Gemma cuenta. Sin confirmar.
- Hardware local: GTX 1060 6 GB, 16 GB RAM. Ollama corre en Windows y desde WSL no es accesible por HTTP
  (escucha en 127.0.0.1), pero sí por interop (`ollama.exe`). Se baja `gemma4:e2b-it-qat` solo para probar la tubería.
- Gemini API ofrece `gemma-4-31b-it` y `gemma-4-26b-a4b-it` (ai.google.dev/gemma/docs/core/gemma_on_gemini_api):
  mismo modelo que la campaña en AMD → **solo para depurar prompts**; ningún número reportado sale de ahí.

## 2026-10-12 (noche) — Calibración resuelta, cliente Evolus
- **Hipótesis confirmada (medida, `scripts/medir_calibracion.py` → `data/processed/calibracion.json`):** calibrando con
  `normal_ampliado()` (d00 + muestras 0–19 de d01..d21 de *entrenamiento*, 920×52; ningún `_te`), en d00_te:
  SPE > límite 15,0% → **2,6%**; eventos de alarma 178 → **49** (≈1 por hora en 48 h; EEMUA admite ≤6 por hora en régimen);
  A 31 → 28. Persiste una falsa alarma T² sostenida en la muestra 826 de d00_te.
  Límite SPE empírico p99 vs Jackson-Mudholkar: no cambia qué fallas se detectan → se queda Jackson-Mudholkar.
- Detección con ampliado: T² 17/21 (faltan 3, 4, 9, 19), SPE 16/21 (faltan 3, 4, 9, 15, 19).
- **Decisión:** dos calibraciones, cada una en su brazo.
  · Réplica FaultExplainer → T² entrenado con d00 (análogo de su protocolo). No se toca.
  · Copiloto, alarmas, SPE y versión robusta → `normal_ampliado()`.
  El test xfail se sustituye por uno sobre la calibración ampliada.
- `evolus/cliente.py` + `evolus/replay.py`: reintentos, throttle 1 s, `ErrorEvolus` con errorCode/traceId, grabación JSONL
  sin cabeceras y `ClienteReplay` para la demo sin GPU. Esquemas de workflow (body de execute, campo de estado) **sin verificar**.

## 2026-10-12 (noche) — Primeras corridas reales (DEPURACIÓN, no reportables; `data/dev/`, no versionado)
- **Gemma 4 31B vía API de Gemini** (`GOOGLE_*` en `.env`): IDV1 e IDV6 aciertan top-1 en nivel 0 **y** nivel 2
  (compuerta: 2 VERIFICADO, 2 PARCIAL). 67–109 s por llamada, ~2.100 tokens de prompt.
- **Esquema externo (Gemini OpenAI-compat):** rechaza `seed` (400 "Unknown name seed") → `--semilla` ahora es opcional.
  No permite apagar el *thinking* de Gemma 4: `reasoning_effort` y `thinking_budget` → 400 "Thinking budget is not
  supported for this model". La salida trae `<thought>…</thought>` → `llm/parseo.py` lo descarta antes de extraer el JSON.
  **Desviación de protocolo:** en Gemini el modelo piensa; en la campaña de vLLM irá con `enable_thinking=False`.
- **Gemma 4 E2B en Ollama local** (GTX 1060, `OLLAMA_HOST=0.0.0.0` en Windows; se llega por el gateway de WSL):
  ~35 s por caso, agota 1.500 tokens; 2/4 JSON inválidos, 0/4 aciertos. Sirve solo como humo del pipeline.
- `eval.correr`: nuevos `--max-tokens` y `--dev` (escribe en `data/dev/`, ignorado por git).

## 2026-10-12 (noche) — Réplica FaultExplainer documentada y despliegue AMD preparado
- `third_party/faultexplainer/` (MIT, commit `2fcfee97…`, pineado en SHA256SUMS) + `docs/REPLICA_FAULTEXPLAINER.md`
  (protocolo con archivo:línea). Hallazgos: su repo trae **sus propios CSV `fault0..20`** (500 filas, 52 variables);
  contribuciones en **un solo punto** (6.ª alarma) truncando por componente antes de sumar, escalado `ddof=0`; el LLM ve
  último valor, media normal y % de cambio (sin z); un solo mensaje user en prosa; acierto = causa o alias en top-3,
  puntuado a mano. Derivado de su Tabla 1 (confirmar con el PDF): GPT-4o acierta 2, 6, 7, 11, 12, 13, 14 (7/11);
  o1-preview 1, 2, 6, 7, 8, 11, 12, 13, 14 (9/11); PCA no detecta 3, 4, 9, 15.
  **Decisión pendiente:** la réplica debe usar SUS CSV y SU fórmula/prompt, no Braatz. Se implementa como brazo aparte.
- `deploy/` (levantar_vllm.sh, campana.sh, traer_resultados.sh) + `docs/CAMPANA_AMD.md`. Verificado: imagen
  `vllm/vllm-openai-rocm:v0.31.0` digest `sha256:749f6f3f…b1f`; modelos `google/gemma-4-31B-it` y `google/gemma-4-26B-A4B-it`
  (Apache-2.0, no gated); thinking se apaga con `chat_template_kwargs.enable_thinking=false` (y flag de servidor
  `--default-chat-template-kwargs`). **Sin verificar:** fp8 y TRITON_ATTN con Gemma 4 en ROCm (fallback bf16/auto).
- `desde_env` lee `{PREFIJO}_EXTRA_BODY` (JSON) y `{PREFIJO}_TIMEOUT`. `pytest.ini` limita la colección a `tests/`.

## 2026-10-12 (noche) — Depuración 1 con Gemini gratis (interrumpida en 31/45) y cambio de prompt
- Capa gratuita de Gemini: 4 errores de servidor (500 y ReadTimeout a 120 s) en 20 casos; latencias de 51 a 243 s.
  Key de pago (proyecto con facturación de Diego): 2/2 llamadas en ~52 s sin errores → `GOOGLE_API_KEY`
  (la gratuita queda como `GOOGLE_FREE_API_KEY`), `GOOGLE_TIMEOUT=300`.
- Resultado parcial dev1 (prompt "1 to 3 causes", k=1, sin reportar): aciertos top-1 en IDV 1, 2, 4, 6, 7 en todos
  los niveles disponibles; errores **idénticos entre niveles** (IDV5→7, IDV8→7, IDV10→1, IDV11→4). Sin caída en la gemela
  por ahora. Gemma casi siempre da UNA sola causa → la métrica top-3 queda castigada.
- **Cambio de prompt (v2):** regla 1 → "List exactly 3 different causes…" (alineado con el top-3 de FaultExplainer).
  dev2 corre con la key de pago, un proceso por nivel (`data/dev/google_31b_dev2_n{0,1,2}`).
- **dev2 final** (prompt v2, k=1, Gemini de pago con thinking forzado; reintentos con max_tokens 16000; NO reportable):
  top-3 nivel 0/1/2 = **11/12, 8/12, 7/11**; top-1 = 6/12, 4/12, 3/11. Caen en la gemela: IDV5 (✅→❌ en n1 y n2,
  siempre [7,1,2]), IDV13 (✅→❌), IDV14 (🟡→❌, n2 BLOQUEADO por la compuerta). IDV2 n2: ReadTimeout 3×300 s (no responde).
  Los casos que se cuelgan pensando son siempre disfrazados. Hipótesis para la campaña AMD (k≥5): Gemma razona cuando la
  señal física es clara y se apoya en la memoria de TEP cuando es sutil. Medir también tokens de razonamiento por nivel.
- **Aclaración de presupuesto:** "≤3 GPU-h" es un diseño conservador propio (por si había que pagar), no un límite del
  crédito: $100 ≈ 50 GPU-h. Si llega el crédito: apuntar a ~10–15 GPU-h (k=10, thinking on/off, un segundo modelo).
