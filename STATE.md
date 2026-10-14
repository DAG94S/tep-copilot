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

## 2026-10-13 — CAMBIO DE PLAN: AMD Token Factory en lugar de crédito de GPU
- Discord, Maharshi [AMD], 13 oct 7:58 (texto pegado por Diego): en el ACT III **AMD no da crédito de GPU**; entrega
  **1 API key por equipo registrado** en lablab para modelos alojados en GPUs de AMD. Portal:
  `notebooks.amd.com/tokenfactory` (NO `notebooks.amd.com/hackathon`, que es de la AMD AI League). Sin tarjeta.
  Manual de usuario dentro del portal. "Gemma is also one of the models hosted".
- Discord, Rajesh [HACK], 12 oct 23:13 (pregunta, **sin respuesta conocida**): menciona `Gemma-4-31B-IT` y
  `DeepSeek-V4-Flash` en Token Factory y pregunta (a) si para Evolus cuenta un agente cuyo modelo es el endpoint de Token
  Factory conectado en "Your models" o hace falta vLLM propio; (b) si el premio de Google exige Gemma o Gemini API.
- Consecuencias (pendientes de verificar con el manual de Token Factory):
  · La campaña ya no necesita droplet ni `deploy/` (se conserva por si llega el crédito de $100).
  · El requisito "corre en AMD" se cumple con Token Factory (hardware AMD), pero se pierde evidencia propia
    (`rocm-smi`, logs de vLLM, benchmark de MI300X). Medir latencia/tok/s del lado cliente.
  · Track Evolus: ANTECEDENTES dice "modelo servido en nuestro propio vLLM en AMD Developer Cloud" → **riesgo**
    hasta que respondan la pregunta de Rajesh.
  · Si Token Factory permite apagar el thinking (`chat_template_kwargs`), depurar y medir directamente ahí.
- **Token Factory configurado** (manual en `api_documentation.txt`, no versionado). Base `https://developer.amd.com.cn/radeon/api/v1`
  (OpenAI-compatible), `AMD_TF_*` en `.env`, modelo `Gemma-4-31B-IT`: no piensa por defecto, `response_format` solo
  `json_object`, `seed` se descarta. Límites: 20 RPM, 8 concurrentes, tope diario 1 (USD/pts) que se reinicia a las
  16:00 UTC = **11:00 Ecuador** (según `/v1/usage`). Precio Gemma 0,50/3,00 por 1M tokens → ~0,002 por caso.
- **Esquema externo (verificado por Diego con `scripts/diagnosticar_token_factory.py`):** con `temperature=0` Gemma
  **degenera** ("```/////…" hasta max_tokens; incluso un saludo se corrompe tras "Hello."). Con temperatura por defecto
  o 0,7 → JSON válido en 4–6 s. Config elegida: `temperature 0.7` + `AMD_TF_EXTRA_BODY={"response_format":{"type":"json_object"}}`.
  IDV1 nivel 2 → top-1 correcto en 3/4 variantes. ⇒ No hay brazo determinista (T=0) en Token Factory: todo con k≥5 y voto.
- El clasificador de permisos de Claude Code bloquea las llamadas al dominio `.com.cn` ("data exfiltration"); Diego
  ejecuta los scripts con `!` mientras decide si lo autoriza.
- **Esquema externo (13 oct):** Token Factory/Gemma rechaza `n>1` → 400 "Model Gemma-4-31B-IT with provider self-dploy
  does not support the n parameter for multiple choices. Send n separate requests instead." Primer intento de campaña
  `tf_gemma31b_k5_v2` abortado (todo ERROR_LLM, carpeta borrada). Arreglo: `ClienteLLM(soporta_n=False)` /
  `AMD_TF_SOPORTA_N=false` → k llamadas separadas.

## 2026-10-13 — PRIMERA CAMPAÑA REPORTABLE EN AMD: `data/runs/tf_gemma31b_k5_v2` (pineada en SHA256SUMS)
- Gemma-4-31B-IT en Token Factory, thinking OFF, k=5 (llamadas separadas), T=0,7, json_object, calibración ampliado,
  prompt v2 (3 causas), fallas 1–15 × niveles 0/1/2. ~25 s por caso. Tokens: 375.625 prompt + 71.648 completion (≈0,40 pts).
- Detectadas 12/15 por nivel (faltan 3, 4, 9; la 15 se detecta tarde). Resultados (evaluables = sin INVALIDO):
  nivel 0: top-1 3/11, top-3 7/11 · nivel 1: top-1 4/10, top-3 5/10 · nivel 2: top-1 4/10, top-3 5/10.
  Compuerta: rechazo de afirmaciones 25–30%; 1 BLOQUEADO (IDV14 n0).
- Sesgo: sin thinking, los errores caen casi siempre en IDV 7/8/1 (alimentación). Comparado con dev2 (Gemini, thinking
  forzado, top-3 n0 11/12), **el razonamiento importa mucho**.
- Acuerdo top-1 entre las 5 muestras ≈100%, pero los textos SÍ varían (solo 2/36 casos con 5 textos idénticos) →
  el muestreo funciona; el modelo es consistente en la causa principal.
- INVALIDO: IDV14 n1/n2 e IDV15 n0/n1/n2 → salidas degeneradas ("y_y_y…", "____") incluso con T=0,7. El despliegue
  *experimental* de Gemma en Token Factory degenera a veces → reintentar inválidos.
- **Tarde del 13 oct — servidor de Token Factory degradado.** Tras la campaña, TODAS las salidas de Gemma degeneran
  ('{"////…', 'y_y_y…'), incluso IDV6 n0, que en la campaña salió limpio (chequeo de salud en `data/dev/tf_salud_idv6`).
  Sin modo json (`--sin-json`, nuevo) también degenera → fallo del despliegue *experimental*, no del prompt.
  Se detuvieron todas las corridas; se borraron las carpetas abortadas (reintentos n0/n12 y réplica: todo INVALIDO).
- Thinking ON (`--razonamiento high`): 8.000 tokens de razonamiento en 234 s sin llegar a responder (dev) → demasiado
  caro para el tope diario (~0,024 pts/llamada); el piloto `low` se abortó con el servidor degradado.
- Bug propio corregido: la réplica heredaba `response_format: json_object` de `AMD_TF_EXTRA_BODY` aunque su prompt es
  prosa libre → ahora lo elimina siempre.
- **Plan:** reintentar mañana tras el reinicio del tope (11:00 Ecuador): chequeo de salud → réplica k=5 → reintentos
  de inválidos. Si el servidor sigue inestable, preguntar en Discord y usar Google (Gemma 31B) como respaldo de desarrollo.

## 2026-10-13 (noche) — RÉPLICA FaultExplainer en AMD: `data/runs/tf_replica_fe_k5` (pineada)
- Token Factory volvió a responder bien (chequeo `data/dev/tf_salud_idv6_b`: IDV6 n0 VERIFICADO, top-1).
- Sus datos (42 CSV pineados), su PCA (reproduce exactamente: detecta 1,2,5,6,7,8,10,11,12,13,14; no 3,4,9,15) y su
  prompt literal (un mensaje user, prosa). Gemma-4-31B-IT, thinking OFF, k=5, T=0,7, acierto top-3 por mayoría de muestras.
- **Gemma 4 31B: 8/11** (aciertos 1, 2, 5, 6, 7, 11, 12, 13; falla 8, 10, 14) vs **GPT-4o 7/11** y **o1-preview 9/11**
  (línea base derivada de su Tabla 1; confirmar contra el PDF antes de citar por falla). Fallas 5 y 6 marcadas
  "revisión de alias" solo porque el texto menciona más IDV; las 5 muestras aciertan en ambas → no cambia el conteo.
- Diferencias de protocolo a declarar: ellos n=1 (temperatura por defecto de la API); nosotros k=5 mayoría, T=0,7
  (T=0 degenera en Token Factory); su acierto con alias se puntuó a mano.

## 2026-10-14 — Evolus acepta Token Factory como modelo propio (captura de Diego)
- Asistente "Your models" de Evolus, paso 4/4: conexión `amd`, base `https://developer.amd.com.cn/radeon/api/v1`.
  Prueba con `Gemma-4-31B-IT`: responde (1035 ms), **tool calling OK** (1108 ms), streaming OK (920 ms),
  razonamiento OK con herramientas en todos los niveles off→very high (6178 ms), `/models` lista **12** modelos.
- Se marcaron 15 modelos pero el servidor lista 12 → al menos 3 de los elegidos no existen allí (sospechosos:
  `gpt-oss-120b`, `deepseek-v4p1-flash`, `glm-5p3-flash`, en minúsculas). Dejar solo los que lista `/models`.
- Consecuencia: el agente de Evolus puede correr sobre hardware AMD sin vLLM propio. Sigue sin respuesta oficial si
  eso cuenta para el premio de Evolus (pregunta de Rajesh, 12 oct); ajustar ANTECEDENTES ("nuestro propio vLLM").
- Evidencia: captura en el chat, no versionada. Pendiente: grabar una llamada real del agente en `data/runs/evolus/`.

## 2026-10-14 — Reintentos de inválidos: `data/runs/tf_gemma31b_k5_v2_reintentos` (pineada)
- Chequeo de salud previo (`data/dev/tf_salud_idv6_c`): IDV6 n0 VERIFICADO, top-1. Servidor sano a las 15:41 UTC
  (antes del reinicio del tope de las 16:00 UTC).
- Mismos parámetros que `tf_gemma31b_k5_v2` (k=5, T=0,7, ampliado, t2, sin esquema, max_tokens 1500) sobre fallas
  14–15 × niveles 0/1/2, con la compuerta vigente (acepta oscilantes). **0 INVALIDO.** IDV14 n0 se repitió como control
  (en la original, tras recompuertar, ya era VERIFICADO top-3; aquí también).
- IDV14: top-3 ✅ en n1 y n2 (top-1 ❌). IDV15: top-3 ❌ en los 3 niveles (cae en IDV 7/1/8, el sesgo de alimentación).
- **Regla de combinación:** registros efectivos de la original (`recompuertado.jsonl`) y cada INVALIDO sustituido por
  su reintento. Resultado combinado (evaluables 12 por nivel; 3 NO_DETECTADO: 3, 4, 9):
  top-1 n0/n1/n2 = **3/12, 4/12, 4/12**; top-3 = **7/12, 6/12, 6/12**; rechazo 23/24/26 %.
  La caída top-3 entre el original y la gemela es de 1 caso.
- Pendiente: llevar la combinación a `verify_claims.py`/`claims.json` antes de citar estas cifras.

## 2026-10-14 — Agente de Evolus creado; Gemma de Token Factory caído (~16:00 UTC)
- Agente `TEP Shift Copilot` (app.evolus.ai, desde cero, instrucciones = `evolus/agente_instrucciones.md` v1).
  Modelo: conexión `amd` → `Gemma-4-31B-IT` (por defecto había quedado DeepSeek-V4-Flash). Temperatura "Automatic"
  (no se envía; ≠ campaña, que usó 0,7). Reasoning: quedó en "Minimal" (ver entrada siguiente). Widgets desactivados. Fallback de la conexión: "Stop" (nunca modelos de Evolus).
  `GET /v1/models` → 1 agente, id `<applicationId>:<agentId>`.
- **Esquema externo:** con el agente sin respuesta, Evolus devuelve **200** con el error como texto del asistente:
  "Your model 'gemma-4-31b-it' could not answer: The model endpoint could not be reached or did not answer in time."
  (68 s en streaming; sin streaming el cliente agotó 180 s). ⇒ el script debe tratar ese texto como error, no como
  respuesta.
- Causa: Token Factory directo → `Gemma-4-31B-IT` **500** `no_available_workers` ("all circuits open or unhealthy");
  `DeepSeek-V4-Flash` 200 en 1,9 s. A las 15:41 UTC Gemma funcionaba. Los nombres de modelo distinguen mayúsculas
  (`gemma-4-31b-it` → 404 model_not_found); falta ver si Evolus envía el nombre en minúsculas o solo lo muestra así.
- Tope diario: el período empieza 16:00 UTC (`daily_reset_timezone` Asia/Shanghai); uso ≈ 0.

## 2026-10-14 — PRIMERA LLAMADA REAL AL AGENTE DE EVOLUS: `data/runs/evolus/agente_2026-10-14` (pineada)
- Gemma de Token Factory volvió a las 16:06 UTC. `scripts/evolus_agente.py --casos 6:0,6:2` (16:06:48–16:09:33 UTC).
- Las dos salidas siguen el formato (orden de trabajo + traspaso), **0 órdenes de control** (`ordenes_de_control`),
  sin causas ni tags inventados; en nivel 2 conserva los tags disfrazados. 74 s y 76 s por llamada (TF directo: 4–6 s).
- Calidad: superficial. Sin Knowledge Library no sabe qué es IDV(6) ("Inspect IDV(6)…"); en 6:2 dice que la hora de la
  alarma "not provided" aunque el índice está en el mensaje. Dice "rejected evidence not provided" (correcto: no hubo).
- **Evidencia de que corrió en AMD:** `uso_token_factory.json` (GET /v1/usage justo después): desde 16:00 UTC, 8
  peticiones (4 errores = la caída previa), `last_request_at` 16:09:34 = fin de la corrida, modelo Gemma-4-31B-IT.
- **Desviación:** `reasoning_tokens` hoy = 1.770 de 2.148 de completion → el agente quedó con **"Reasoning: Minimal"**
  (no "Model default", corrección de Diego), que enciende el thinking de Gemma. Explica los ~75 s. Para alinearlo con
  la campaña (thinking off) → "Model default" y repetir; la UI no ofrece "Off".
- `sha256_instrucciones` del manifiesto es del archivo `evolus/agente_instrucciones.md` completo (cabecera en
  español + bloque pegado), no solo del bloque.
- **Repetición con "Reasoning: Model default"** → `data/runs/evolus/agente_2026-10-14_sinrazonamiento` (pineada; es la
  que cita el README): 7,3 s y 30,0 s (antes ~75 s), 0 órdenes de control, y ahora sí cita "sample index 173" en ambos
  niveles. Los `reasoning_tokens` de `/v1/usage` no sirven para aislarla: el piloto con thinking corría a la vez.

## 2026-10-14 — Piloto con thinking (dev) y lanzamiento de la campaña con razonamiento
- Piloto `data/dev/tf_think_piloto2_{minimal,low}` (IDV1/6 × n0/n2, k=1, max_tokens 8000). `minimal` y `low` dan
  **los mismos tokens** (1.859 vs 1.858 en IDV1 n0) → Token Factory parece ignorar el nivel; `low` se detuvo.
  minimal: 4/4 top-1. Sin thinking (campaña), IDV1 n0 fallaba top-1 ([7,8,1]); el resto ya acertaba.
  En la gemela (n2) piensa más y tarda más: IDV1 3.320 tokens/125 s vs 1.859/59 s; IDV6 2.052/130 s vs 1.380/46 s.
- **Campaña reportable `data/runs/tf_gemma31b_k5_think_n{0,1,2}`**: mismos parámetros que `tf_gemma31b_k5_v2`
  (k=5, T=0,7, ampliado, t2, sin esquema) salvo `--razonamiento minimal` y `--max-tokens 8000`; un proceso por nivel.
