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
- **Deadline:** contador de lablab el 18-oct: ~10:00 UTC (05:00 Ecuador). Ver la entrada de las 05:56 UTC.
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

## 2026-10-14 — Datos de Rieth para la versión robusta (20 simulaciones por falla)
- `scripts/descargar_rieth.py`: Dataverse doi:10.7910/DVN/6C3JR1, solo `TEP_FaultFree_Training` y `TEP_Faulty_Training`
  (MD5 publicado verificado; **Dataverse da 403 sin User-Agent**). pyreadr superó 5,9 GB de RAM al cargar
  Faulty_Training (WSL 7,9 GB) → abortado; **R base** lo carga con pico 3,1 GB (`scripts/extraer_rieth.R` →
  `scripts/convertir_rieth.py`). Faulty_Training trae **fallas 1–20** (no la 21).
- `data/processed/rieth/`: corridas 1–20 por falla, (20, 500, 52) float32, pineadas. `core/datos.cargar_rieth`.
  Orden de columnas = Braatz (test con medias de la normal vs d00). Falla en la muestra 20.
- Detección T² (calibración `normal_ampliado` de Braatz; `data/processed/rieth/deteccion_t2.json`): 20/20 en
  1, 2, 5, 6, 7, 8, 10, 12, 13, 14 (10 tarde: mediana 179 muestras); 3, 4, 9, 11, 15 ≤4/20 con retardos ~305
  ≈ falsas alarmas tardías (4/20 corridas normales también alarman en 500 muestras). 0/300 alarmas antes de la falla.
  ⚠ IDV11 se detecta en Braatz pero no en Rieth-train con T².

## 2026-10-14 — Versión robusta (Rieth): plan y lanzamiento del brazo sin thinking
- Decisión con Diego: **A hoy** = sin thinking, fallas 1,2,5,6,7,8,10,12,13,14 (detectadas 20/20 en Rieth) × corridas
  1–10 × niveles 0/1/2 = 300 casos, mismos parámetros que `tf_gemma31b_k5_v2` (k=5, T=0,7, ampliado, t2, sin esquema,
  max_tokens 1500) → `data/runs/tf_rieth_k5_n{0,1,2}`. **B mañana** (tras el reinicio de las 16:00 UTC) = con thinking
  minimal, mismas fallas × corridas 1–10 × niveles **0 y 2** (200 casos).
- Presupuesto medido hoy (`/v1/usage`): ~0,003–0,004 USD por caso con thinking (k=5) → 300 casos superarían el tope
  diario de 1 USD. Sin thinking ~0,0002 por caso. **Corrección de Diego: no se recorta B, se reparte en dos días**
  (el tope se reinicia a diario y la entrega es el dom 18): jue 15 niveles 0 y 2 (200 casos), vie 16 nivel 1
  (100 casos), sáb 17 margen para reintentos.

## 2026-10-14 (tarde) — 429 por exceso de concurrencia; reanudación
- Con 6 procesos a la vez (3 thinking + 3 Rieth) se superaron los límites de Token Factory: **161 casos ERROR_LLM**
  (429), dos tipos: `rate_limit_exceeded` "maximum 20 requests per minute for this OneClick user" y
  `token_rate_limit_exceeded` "Model API rate limit exceeded". No hubo salidas degeneradas. Fallo propio: el cliente
  solo esperaba 1/2/4 s. Arreglo (`f6d0ae2`): ante 429 espera 10/20/40/60/60/60 s (o `Retry-After`).
- Los registros ERROR_LLM se movieron a `errores_429.jsonl` en cada carpeta (conservados) y los casos se reanudan con
  `--continuar` y menos concurrencia: 1 proceso para Rieth (n0→n1→n2 en serie) + 3 para thinking.

## 2026-10-14 (noche) — RESULTADOS: Rieth sin thinking (300) y Braatz con thinking (45), pineados
- Ambas terminaron con 0 ERROR_LLM y 0 INVALIDO tras la reanudación. Análisis exploratorio (aún NO en claims.json):
- **Rieth sin thinking** (10 fallas × 10 corridas por nivel): top-1 45/46/44 de 100; top-3 74/67/69.
  Pareado n0→n2 (mismo caso): top-1 2 vs 1 discordantes (sin cambio); top-3 7 vs 2, McNemar p=0,18, caída 5 pp,
  IC95 bootstrap por falla [−4, 17]. n0→n1 top-3: 8 vs 1, p=0,039, caída 7 pp, IC [0, 18].
  **La caída se concentra en IDV8** (top-3 10→5→5); el resto es casi idéntico entre niveles. Las corridas de una
  misma falla se comportan casi igual (10/10 o 0/10: IDV10 0/10 en todo nivel) → el tamaño efectivo es ~10 fallas,
  no 100 casos; por eso el IC se calcula por clusters de falla.
- **Braatz con thinking minimal** (12 evaluables por nivel): top-1 5/5/5; top-3 8/9/7 (sin thinking: 3/4/4 y 7/6/6).
  Tokens de razonamiento (mediana por caso, k=5): 16.750 → 21.215 → 22.528; segundos 451 → 694 → 702.
  ⇒ El disfraz no baja el acierto con thinking, pero **sube el esfuerzo de razonamiento ~30 %**.
- Lectura provisional: Gemma no "recita" TEP en general; la memoria de TEP solo pesa en IDV8 (variación de
  composición A/B/C), que pierde la mitad de los aciertos top-3 al quitar los nombres.

## 2026-10-14 (noche) — Verificación del "giro": qué sobrevive dentro de cada falla
- **NO sobrevive: "la compuerta sabe cuándo confiar".** En Rieth (300) VERIFICADO da top-3 85 % vs PARCIAL 60 %,
  pero es confusión por falla: las fallas fáciles (IDV1) salen siempre VERIFICADO y aciertan; las difíciles (10, 13)
  salen PARCIAL y fallan. Dentro de falla: top-3 V−P permutación estratificada p=0,09 (OR Mantel-Haenszel 3,6, lo
  arrastran IDV14 y 12); top-1 sin relación (p=1). Con thinking, "acuerdo=1 → 71 % vs 16 %" tampoco: en las 3
  fallas con acuerdo mixto, 0/5 vs 0/4. ⇒ No usar el estado de la compuerta ni el acuerdo como confianza por caso.
- Anecdótico: BLOQUEADO 0/7 aciertos; dentro de IDV5, 0/6 bloqueados vs 16/24 parciales (Fisher p=0,005). Una falla.
- **SÍ sobrevive: razonar inventa más evidencia.** Braatz, mismos 36 casos (falla×nivel) con y sin thinking:
  rechazo medio por caso 22 % → 36 %; thinking peor en 24, mejor en 2, igual en 10; Wilcoxon p=0,00015.
  Afirmaciones 143 → 182; rechazadas 35 → 68. A la vez top-1 sube de 11/36 a 15/36. ⇒ el thinking acierta algo más
  pero cita casi el doble de evidencia que los datos no respaldan: la compuerta importa más con modelos que razonan.
- Pitch revisado: no "sabe cuándo confiar", sino "no deja que el modelo invente evidencia" + "el disfraz cuesta
  esfuerzo, no acierto (salvo IDV8)" + réplica 8/11 vs GPT-4o 7/11.

## 2026-10-14 (noche) — Rieth con thinking adelantado a hoy
- Diego: el presupuesto del período (hasta 16:00 UTC del 15) se pierde si no se usa. Gastado 0,161, restante 0,839.
  Precios de `/v1/models`: Gemma-4-31B-IT 3,5e-8 prompt / 7e-8 completion por token → ~0,002 USD por caso con thinking.
- Lanzado a las ~20:40 UTC: `data/runs/tf_rieth_k5_think_n{0,2}_{a,b,c}` (grupos de fallas a=1,2,5,6 b=7,8,10
  c=12,13,14; corridas 1–10; mismos parámetros que el piloto: minimal, k=5, T=0,7, max_tokens 8000). 6 procesos.
  Las 3 carpetas de cada nivel forman una campaña (verify_claims acepta `fuente` como lista). Nivel 1 después.

## 2026-10-15 — Knowledge Library de Evolus (2.º building block) cargada por API
- Biblioteca RAG creada en la UI (memoryId `e8fe0150-34c8-f111-bf5b-000d3aae6dc8`; la lista de bibliotecas por API da
  401 con la API key, el id se sacó de la URL de la UI). Formatos aceptados (GET /memories/document-formats):
  .txt .md .csv .json .xml .html .htm .pdf .docx, máx. 50 MB.
- `scripts/evolus_biblioteca.py --subir` subió los 3 documentos de `knowledge/` (multipart) → indexados
  (ingestionStatus 2): tep_process_description 4 chunks, alarm_response_procedure 3, inspection_guide 3.
  Evidencia: `data/runs/evolus/biblioteca_20261015T011352Z` (pineada).
- Pendiente: vincular la biblioteca al agente en la UI y repetir la corrida del agente para ver si la orden de trabajo
  deja de ser superficial (antes: "Inspect IDV(6)…").

## 2026-10-15 (~01:30 UTC) — Rieth con thinking detenido; Gemma 500; biblioteca sin probar
- Con 6 procesos thinking volvieron los 429 ("maximum 20 requests per minute") pese a las esperas largas: 64 ERROR_LLM
  apartados en `errores_429.jsonl` de cada carpeta `tf_rieth_k5_think_*`. Válidos: **95/200**. Procesos detenidos.
- Después Gemma-4-31B-IT directo → **500** (DeepSeek-V4-Flash y Qwen3.8-27B → 200): caída del despliegue de Gemma.
- Biblioteca vinculada al agente en la UI; la prueba del agente dio 422 "Your model 'gemma-4-31b-it' could not answer:
  The model endpoint returned an error / is limiting the requests" → es Gemma, no la biblioteca. Pendiente probarla.
- Presupuesto del período: gastado 0,414, restante 0,586 (reinicio 16:00 UTC del 15).
- Reanudar: cuando Gemma dé 200, probar primero el agente; luego Rieth thinking con **2 procesos** (n0 y n2, grupos en serie).
- Guías actualizadas: AGENTS.md (Token Factory, límites, reglas), docs/PROYECTO.md (§0 estado y pitch, plan, riesgos),
  docs/CHECKLIST.md, docs/ANTECEDENTES.md (Evolus con Token Factory, competidores).

## 2026-10-15 (16:22 UTC) — Gemma-4-31B-IT retirado del catálogo de Token Factory
- **Esquema externo:** chequeo de salud (`data/dev/tf_salud_idv6_d`, IDV6 n0, k=1) → **400**
  `"Requested model Gemma-4-31B-IT not supported"` (ya no es el 500 `no_available_workers` de ayer).
- `GET /v1/models` (200) lista 11 modelos y **ninguno es Gemma**: DeepSeek-V4.1-Flash, DeepSeek-V4-Flash,
  DeepSeek-V4-Flash-Vision-Exp, GLM-5.3-Flash, MiMo-V2.6-Flash, MinerU2.5-Pro, MiniCPM5-2B, MiniCPM-V-4.7-1B,
  MiniCPM-V-4.7-35B-A3B, Qwen3.8-27B, Qwen3.8-Flash-Next. `/v1/usage`: período desde 16:00 UTC, gastado 0.
- Consecuencias: Rieth con thinking queda en 95/200 válidos (n0 59, n2 36; n1 sin empezar). El agente de Evolus
  (conexión `amd` → Gemma) tampoco puede responder. Todo lo ya pineado sigue valiendo (corrió en Gemma sobre AMD).
- La corrida `data/runs/evolus/agente_2026-10-15_biblioteca` (01:16 UTC) dio 422 en los dos casos → no se pinea.

## 2026-10-15 — Discord y página del evento: premio de Google confirmado; los dos premios de socio piden Developer Cloud
- Discord, Zofia [lablab], 14 oct 6:41: Google DeepMind se suma como socio; **premio de Google ($5k) para equipos que
  usen Gemma** "running on AMD GPUs in the cloud using AMD Developer Cloud and ROCm". Cierra la pregunta abierta
  (el supuesto de trabajo era correcto). La página no dice si Gemma vía Token Factory cuenta.
- Página del evento (consultada hoy): AMD obligatorio ("a meaningful part of its workload on AMD infrastructure");
  Token Factory aparece en el FAQ. **Track Evolus "Business Agents on AMD":** "your own open model served on AMD
  Developer Cloud through a vLLM endpoint", ≥2 bloques, manejado por API, app containerizada, repo público, README.
  Criterios generales: Application of Technology, Presentation, Business Value, Originality.
- Discord, Yuvi [GDev], 15 oct 8:02: **"AMD GPU credits and tokens are being distributed on a rolling basis within
  48 hours"** de completar las tres inscripciones (lablab, AMD, equipo). Contradice a Maharshi (13 oct: sin crédito
  de GPU en el ACT III). Si no llegan en 48 h, contactar a los organizadores.
- Con Gemma fuera de Token Factory, un vLLM propio en Developer Cloud (`deploy/` ya preparado) cumpliría a la vez
  Google (Gemma + ROCm) y Evolus (vLLM propio). Pendiente: que Diego confirme si recibió crédito de GPU.

## 2026-10-15 — "Razonar inventa más evidencia" comprobado dentro de cada falla
- Reproducido con datos pineados (combinada sin thinking vs `tf_gemma31b_k5_think_n{0,1,2}`, 36 pares falla×nivel):
  rechazo medio por caso 22 % → 36 %, peor 24 / mejor 2 / igual 10, Wilcoxon p=0,00015; afirmaciones 143 → 182,
  rechazadas 35 → 68; top-1 11 → 15.
- **Agregado por falla (12 clusters, media de los 3 niveles): peor en 9, mejor en 1 (IDV11, 0,23→0,22), igual en 2
  (IDV7, 12); Wilcoxon p=0,0039; signo p=0,021.** Sobrevive al control por falla → en claims.json (`think_rechazo_*`, `think_afirmaciones`, `think_top1_pares`) y en el README.

## 2026-10-15 (~17:00 UTC) — Segundo modelo: Qwen3.8-27B en Token Factory (decisión de Diego)
- Motivo: Gemma fuera del catálogo y presupuesto del día sin usar; la única forma de saber si la sonda distingue
  modelos (¿Qwen recita donde Gemma razona?) es medirlo. Brazo aparte; no se mezcla con las campañas de Gemma.
  Si Gemma vuelve, Gemma tiene prioridad (máx. 2 procesos en total).
- **Esquema externo (Qwen3.8-27B, verificado):** piensa POR DEFECTO (350 tokens de razonamiento en un prompt corto);
  `chat_template_kwargs.enable_thinking=false` lo apaga (0 reasoning_tokens, 4 s). Con T=0 se queda razonando hasta
  max_tokens sin responder → T=0,7 como con Gemma. `n=2` → 400 (mismo mensaje que Gemma) → k llamadas separadas.
  Precio 3,5e-8 / 7e-8 por token (igual que Gemma). `json_object` OK.
- Config: `AMD_TF_MODEL=Qwen3.8-27B`, `AMD_TF_EXTRA_BODY={"response_format":{"type":"json_object"},
  "chat_template_kwargs":{"enable_thinking":false}}` (por entorno; `.env` sin tocar). Humo dev `data/dev/qwen_salud_idv6`
  (IDV1/6 × n0/n2, k=1): 4/4 JSON válidos, ~12 s por llamada. No reportable.
- Lanzadas (mismos parámetros que `tf_gemma31b_k5_v2` y `tf_replica_fe_k5`): `data/runs/tf_qwen27b_k5_v2`
  (fallas 1–15 × niveles 0/1/2, k=5, T=0,7, ampliado, t2, sin esquema, max_tokens 1500) y `data/runs/tf_replica_fe_qwen27b_k5`.
- **Réplica con Qwen abortada y relanzada:** con max_tokens 1500 las 5 muestras de IDV1 se cortaron a mitad de frase
  (7.500 = 5×1.500 tokens de completion; ~6.000 caracteres de prosa cada una). Gemma usó ~700 por muestra y nunca llegó
  al tope. Carpeta borrada (1 caso). Relanzada como `tf_replica_fe_qwen27b_k5` con **max_tokens 4000** (desviación
  declarada: el tope solo debe evitar truncar; no favorece a Qwen frente a Gemma, que no truncó con 1500).
  La campaña Braatz de Qwen no trunca (JSON de 700–3.300 caracteres) → sigue con 1500.
- Con max_tokens 4000 siguen truncadas 4/10 muestras (IDV1 3/5, IDV2 1/5; hasta 15.500 caracteres: Qwen sin thinking
  razona dentro del texto). FaultExplainer no ponía tope (API de OpenAI por defecto) → se relanza con **max_tokens 8000**
  (2 casos perdidos, carpeta borrada). Al analizar, contar las muestras que aún terminen sin conclusión.
- **Esquema externo (Qwen3.8-27B, thinking):** `reasoning_effort=minimal` → 400 "Unexpected reasoning effort minimal.
  Supported types are xhigh (default), medium, and low." ⇒ por defecto Qwen piensa en **xhigh**. Se usa `low` (el más
  bajo disponible; desviación declarada frente a `minimal` de Gemma).
- Piloto dev `data/dev/qwen_think_piloto_low` (IDV1/6 × n0/n2, k=1, max_tokens 8000): 4/4 top-1, 4 PARCIAL;
  reasoning 1.158–1.972 tokens y 50–75 s por llamada (Gemma minimal: 1.380–3.320 y 46–130 s). A diferencia de Gemma,
  el disfraz casi no sube el razonamiento de Qwen (IDV1 1.964→1.972; IDV6 1.158→1.581). ~0,001 USD por caso (k=5).
  Gastado hoy 0,018 USD.
- Lanzada `data/runs/tf_qwen27b_k5_think_n0` (mismos parámetros que `tf_gemma31b_k5_think_n0` salvo `--razonamiento low`);
  n2 y n1 cuando termine la réplica (máx. 2 procesos).

## 2026-10-15 (~20:00 UTC) — Réplica FaultExplainer con Qwen: NO puntuable automáticamente
- `data/runs/tf_replica_fe_qwen27b_k5` (max_tokens 8000) terminó: 11 detectadas, la puntuación automática da 5/11
  (Gemma 8/11), **pero no es válida**: `extraer_idv` toma los 3 primeros IDV por orden de aparición, lo que solo funciona
  con respuestas breves (Gemma: 2/11 casos a revisión). Qwen escribe 12.000–31.000 caracteres repasando y descartando
  causas: 10/11 casos marcados `requiere_revision_alias`; ej. IDV13 muestra con "The root cause is IDV(6)" → extraído
  [6,1,2]; otra termina "I will focus on IDV(4)" → [7,6,3]. Varias muestras siguen cortadas a 8000 tokens (IDV11).
- **Decisión propuesta:** no citar la réplica de Qwen. Puntuarla exigiría leer a mano 55 textos largos (FaultExplainer
  puntuó a mano). La comparación válida entre modelos es la del contrato JSON + compuerta (`tf_qwen27b_k5_v2`), que
  justamente existe para que la evaluación no dependa de interpretar prosa.
- **Resuelto con un anotador LLM** (`eval/extraer_causas_llm.py`, DeepSeek-V4-Flash, T=0, sin thinking por defecto;
  modelo distinto de los evaluados; mismo anotador para ambas réplicas; escribe `extraccion_llm.jsonl` sin tocar
  `registros.jsonl`). Esquema externo: DeepSeek rechaza `thinking` en /chat/completions ("use reasoning_effort").
  · Validación con Gemma (`tf_replica_fe_k5`): **mismo resultado por mayoría en las 11 fallas (8/11)**; a nivel de
    muestra 42/52 listas idénticas a `extraer_idv` donde este no era ambiguo — las 10 diferencias son el anotador más
    estricto (Gemma propone 1 causa y menciona otras al razonar; la regex las contaba).
  · Qwen (`tf_replica_fe_qwen27b_k5`): **5/11** (aciertos 1, 5, 6, 7, 12; fallos 2, 8, 10, 11, 13, 14), idéntico
    por falla a la regex; 1 muestra sin conclusión (IDV11, 0/5: no puede cambiar el voto).
  ⇒ La réplica de Qwen SÍ es citable con el anotador: Qwen 5/11 vs Gemma 8/11, GPT-4o 7/11, o1-preview 9/11.
  Contraste: con nuestro contrato JSON + compuerta Qwen acierta MÁS que Gemma (top-3 n0 9 vs 7 de 12); en prosa libre,
  menos. El formato estructurado le favorece. Coste del anotador: céntimos.

## 2026-10-15 (~23:30 UTC) — Qwen con thinking completo; segundo modelo en claims y README
- `tf_qwen27b_k5_think_n{0,1,2}` (low, k=5, max_tokens 8000): 0 ERROR, 0 INVALIDO; top-1 4/4/5, top-3 7/6/5 de 12;
  razonamiento mediano 11.544 / 13.560 / 12.955 tokens; ~470–590 s por caso.
- Dentro de cada falla: el thinking baja el acierto de Qwen (top-1 19→13 de 36; peor en 4 fallas, mejor en 0, signo
  p=0,125; top-3 26→18, 5/0, p=0,062: dirección consistente, no significativa con 12 fallas; lo arrastran IDV11 y 14).
  Rechazo 31 %→36 %: casos 16/5/15 p=0,009; **por falla 7/2/3 p=0,074 (no significativo)**. Mismo sentido que Gemma, más débil.
- Esfuerzo y disfraz: Gemma razona más disfrazada en **12/12 fallas** (Wilcoxon p<0,001); Qwen en 8/12 (p=0,13). La
  "subida de esfuerzo con el disfraz" es de Gemma, no general.
- 22 claims nuevos (`qwen_*`, `replica_anotador_*`) y sección "Second model" en el README: 62/62 marcadores OK.
  Valores cotejados con el análisis independiente previo antes de fijarlos.

## 2026-10-16 (00:30 UTC) — Discord: AMD revisa Gemma 4; sin créditos de GPU para el hackathon
- Maharshi [AMD], 15 oct 13:11 (pegado por Diego): "folks with gemma4 issues, the team is currently reviewing and will
  get back. for hackathon no cloud credits needed only apikey from notebooks.amd.com/tokenfactory".
  ⇒ (1) Gemma puede volver (sin fecha). (2) **No hay créditos de GPU**: el camino del vLLM propio queda descartado; la
  posición oficial de AMD es que Token Factory basta como componente AMD. Cita útil para el README/entrega, sobre todo
  para el track de Evolus (las bases dicen "vLLM endpoint on AMD Developer Cloud").
- Gemma sigue fuera de `/v1/models` (00:23 UTC). El sondeo de 8 h no lo vio volver.

## 2026-10-16 (~00:50 UTC) — Agente de Evolus con Qwen: la biblioteca no se consultaba (causa: instrucciones v1)
- Diego duplicó el agente: «TEP Shift Copilot (copia)» (`…:57f05ba1-…`), conexión `amd` → Qwen3.8-27B, Reasoning
  "Model default", biblioteca «TEP process & procedures» vinculada. El original (Gemma, `…:384fa28a-…`) queda intacto.
- Corrida `data/runs/evolus/agente_2026-10-16_biblioteca_qwen` (IDV6 n0/n2 + IDV1 n0, mensajes de tf_gemma31b_k5_v2):
  3/3 respuestas, 0 órdenes de control, 154/80/76 s; `/v1/usage` antes/después grabado: 3 peticiones, +7.869 reasoning
  de +9.127 completion ⇒ con "Model default" **Qwen piensa** (no hay opción Off en la UI). Pero solo ~1.200 tokens de
  prompt por petición y ninguna búsqueda ⇒ **no consultó la biblioteca** (inspección genérica, no sabe qué es IDV(6)).
- Sonda dev (`data/dev/evolus_biblioteca_sonda`): pidiendo explícitamente la biblioteca → 2 peticiones, +7.912 tokens de
  prompt, respuesta correcta citando `inspection_guide_by_disturbance.md` y `tep_process_description.md`. La biblioteca
  funciona; el agente no la busca por iniciativa propia.
- Causa: la regla 2 de las instrucciones v1 ("Use only the data in the message… do not invent… equipment names").
  **Instrucciones v2** (`evolus/agente_instrucciones.md`): buscar en la biblioteca cada causa aprobada antes de redactar,
  inspección tomada de la guía con el documento citado, "no library entry for this code" para códigos disfrazados.
  Pendiente: Diego pega v2 en la copia → repetir la corrida.
- **Corrida con instrucciones v2 → `data/runs/evolus/agente_2026-10-16_biblioteca_qwen_v2` (pineada; la v1 queda
  pineada como comparación):** 3/3, **0 órdenes de control**, 106/167/121 s; `/v1/usage`: 6 peticiones (búsqueda +
  respuesta por caso), +58.091 tokens de prompt (los fragmentos de la biblioteca) frente a +3.620 con v1.
  IDV6 n0: inspección por causa tomada de `inspection_guide_by_disturbance.md` (stream 1: válvulas de aislamiento,
  transmisor de flujo, válvula de alimentación…) y cita los dos documentos. IDV1 n0: menciona que XMEAS(1) fue rechazada
  por la compuerta y no la usa. **IDV6 n2 (disfrazado): "no library entry for this code" para C26/C89/C16, sin adivinar**
  → el disfraz se mantiene también en la capa de documentación.
- Bloques de Evolus visibles por API: agente + Knowledge Library (2). Falta el workflow (3.º).
- **3.er bloque de Evolus = AI Tool «translate»** (no hay "Workflows" en la UI; "Automations" sin API verificada).
  `scripts/evolus_traducir.py` traduce al italiano los documentos de `agente_2026-10-16_biblioteca_qwen_v2` (sin el
  preámbulo, desde "## Work order") → `data/runs/evolus/traduccion_it_2026-10-16` (pineada): 3/3, ninguno truncado,
  27 créditos en total; conserva Markdown y tags. La demo la muestra en un desplegable bajo la orden de trabajo.
- README "Evolus integration" reescrito: 3 bloques (agente, biblioteca, AI Tool) con 3 claims nuevos; cita a Maharshi
  sobre Token Factory. 65/65 marcadores OK.

## 2026-10-16 (~01:30 UTC) — Datos Braatz al repo (opción A, decisión de Diego)
- Problema: la demo (Live replay y Control room) calcula T² y alarmas desde `data/raw/braatz/`, ignorado por git → en un
  clon o en Streamlit Cloud el replay no funcionaría (regla 4). Se versiona `data/raw/braatz/` (46 archivos, 26 MB, ya
  pineados en SHA256SUMS; licencia NCSA/UIUC que permite redistribuir conservando el aviso, LICENSE incluido).
  Rieth (579 MB) y los CSV de FaultExplainer siguen fuera. AGENTS.md regla 2 actualizada.
- Corridas incompletas fuera del repo por `.gitignore`: Rieth thinking (95/200) y las corridas de Evolus con 422.

## 2026-10-16 (~01:50 UTC) — Agente original (Gemma) con instrucciones v2: sin modelo; se queda Qwen
- Diego pegó las instrucciones v2 también en el agente original. Sonda dev (`data/dev/evolus_gemma_sonda`): **422**
  `own_models.request_rejected` "Requested model Gemma-4-31B-IT not supported" (Gemma sigue fuera de Token Factory).
- Decisión de Diego: no conectar Gemma vía API de Google (no es hardware AMD y allí Gemma piensa a la fuerza);
  la evidencia de Evolus es la corrida con Qwen sobre Token Factory. Si Gemma vuelve, repetir 6:0, 6:2, 1:0 (≈0,003 USD).

## 2026-10-16 (~16:58 UTC) — Gemma-4-31B-IT de vuelta en Token Factory
- `GET /models` vuelve a listar `Gemma-4-31B-IT` (junto a Qwen3.8-27B, DeepSeek-V4.x, GLM-5.3-Flash, etc.).
- Llamada mínima ("Reply with exactly: OK"): 200 en 2,2 s, `finish_reason: stop`. La respuesta reporta
  `"model": "self-dploy/Gemma-4-31B-IT"` (antes no llevaba prefijo); se sigue pidiendo como `Gemma-4-31B-IT`.
- `scripts/probar_token_factory.py` (IDV1, gemela nivel 2): 10,6 s, 2.120 + 221 tokens, `reasoning_tokens: 0`,
  JSON válido (causas C89/C16/C78), sin la salida degenerada del 13-oct. Gasto del periodo: 0,00009 USD.
- Pendiente (decisión de Diego): repetir en Evolus el agente original con instrucciones v2 sobre Gemma (6:0, 6:2, 1:0).
- **Corrida Evolus con Gemma → `data/runs/evolus/agente_2026-10-16_biblioteca_gemma_v2` (pineada):** agente original
  (`…:384fa28a-…`, conexión `amd` → Gemma-4-31B-IT), instrucciones v2 (mismo SHA 8035598c… que la de Qwen), casos
  6:0, 6:2, 1:0 de tf_gemma31b_k5_v2. 3/3, **0 órdenes de control**, 32/19/29 s (Qwen: 106/167/121 s).
  `/v1/usage`: 6 peticiones, 0 errores, +55.847 prompt (consulta la biblioteca), +1.172 completion, **0 reasoning**,
  0,0019 USD. IDV6 n0 e IDV1 n0: inspección por causa citando `inspection_guide_by_disturbance.md`; IDV1 n0 menciona
  XMEAS(1) rechazada por la compuerta. IDV6 n2 (disfrazado): "no library entry for this code" para C26/C89/C16.
- **Defecto:** el "Shift handover" de 6:0 y 6:2 sale **en italiano** pese a "Write exactly two sections, in English"
  (1:0 en inglés; Qwen v2: 3/3 en inglés). Causa no verificada: lo que recupera la biblioteca no queda en
  `intercambios.jsonl` (solo se ve la respuesta final).
- **Causa del italiano (verificada, `data/dev/evolus_italiano/`):**
  1. Config de los dos agentes por `GET /agents`: idéntica salvo `modelKey`; `language: null` en ambos; prompts iguales
     entre sí (difieren del archivo solo en espacios que añade la UI); la biblioteca tiene solo los 3 .md en inglés del 15-oct.
  2. Preguntado en la misma conversación, el agente dice "Nothing did. I failed to follow the instruction…"
     (autoinforme, no prueba nada).
  3. Gemma **directo en Token Factory** con el mismo system prompt y los mensajes de 6:0 y 6:2, 5 veces cada uno:
     **0/10 en italiano** ⇒ el italiano entra por la capa de Evolus.
  4. Pedido el texto literal de la regla de idioma, **Gemma y Qwen, en conversaciones nuevas, citan la misma frase palabra
     por palabra**: "Language: by default, respond in Italian. If the user writes in a different language, respond in
     the user's language instead. If your instructions define a language policy, that policy takes precedence."
     ⇒ Evolus inyecta un system prompt propio con italiano por defecto (con `language: null`). Nuestro mensaje
     de usuario está en inglés y el prompt dice "in English", así que lo correcto era inglés: Qwen lo respeta 3/3 y
     Gemma solo en 1/3 (mezcla la regla oculta en la sección en prosa).
  - Arreglo propuesto: fijar el idioma del agente en English en la UI de Evolus y repetir 6:0, 6:2, 1:0 en carpeta
    nueva; la corrida en italiano queda pineada como evidencia del defecto.

## 2026-10-16 (~18:00 UTC) — Instrucciones v3 (Language policy) y corridas Gemma/Qwen v3
- El chatbot de ayuda de Evolus confirma que no hay ajuste de idioma por agente en la UI (el campo `language` de la API
  no se expone): el idioma se fija en las instrucciones. (Su afirmación de que Gemma está "Italian-tuned" es falsa:
  Gemma directo en Token Factory dio 0/10 en italiano.)
- v3 = v2 + primera línea "Language policy: write everything in English, including the shift handover, whatever
  default language the platform sets. Never write in Italian or any other language." (SHA ecd3c396…). Diego la pegó en
  los dos agentes; `GET /agents`: ambos prompts = v3 (ignorando espacios de la UI).
- **Gemma v3 → `data/runs/evolus/agente_2026-10-16_biblioteca_gemma_v3` (pineada):** 3/3 en inglés, 0 órdenes de
  control, 70/29/26 s; `/v1/usage` 6 peticiones, 0 errores, +56.033 prompt, +1.106 completion, 0 reasoning, 0,0019 USD.
  6:0 y 1:0 citan `inspection_guide_by_disturbance.md`; 1:0 menciona XMEAS(1) rechazada; 6:2: "no library entry" ×3,
  sin "IDV" en el texto.
- **Qwen v3 → `data/runs/evolus/agente_2026-10-16_biblioteca_qwen_v3` (pineada):** 3/3 en inglés, 0 órdenes,
  126/64/93 s; 6 peticiones, 0 errores, +58.249 prompt, +4.819 completion (2.880 reasoning), 0,0025 USD. 6:2: "no library
  entry" ×3 (dice que buscó en los dos documentos), sin "IDV".
- Las corridas v2 (Gemma en italiano, Qwen) quedan pineadas como historial; la comparación limpia Gemma vs Qwen es v3.

## 2026-10-16 (~17:30 UTC) — Rieth con thinking: el Gemma nuevo ignora reasoning_effort
- Reanudado con `--continuar` (mismos argumentos del 14-oct, 2 procesos). Los 2 primeros casos de hoy (n0_a 5:5,
  n2_a 2:2) salieron con **`reasoning_tokens: 0`** (14-oct: 6.000–25.000 por caso con k=5). Procesos detenidos
  enseguida; esos 2 registros, apartados a `sin_thinking_2026-10-16.jsonl` en sus carpetas. La campaña vuelve a 95/200,
  todos con razonamiento > 0.
- **Esquema externo:** el despliegue que volvió responde `"model": "self-dploy/Gemma-4-31B-IT"`. Sonda
  (`data/dev/gemma_thinking_sonda_2026-10-16.log`): `reasoning_effort` minimal/low/high → 0 tokens de razonamiento;
  `"thinking": {"type": "enabled"}` → 400 "\"thinking\" is not supported on /v1/chat/completions and was not applied.
  Use \"reasoning_effort\"…" (aunque reasoning_effort no tiene efecto); **`chat_template_kwargs: {"enable_thinking": true}`
  sí razona**.
- Caso real Rieth falla 2, corrida 1, nivel 2: 14-oct (reasoning_effort minimal, k=5) 15.065 razonamiento ≈ 3.000 por
  llamada, VERIFICADO; hoy (enable_thinking, k=2) 5.566 ≈ 2.800 por llamada, VERIFICADO, 396 s. Volumen parecido, pero
  es otro despliegue y otro mando: terminar los 105 casos así mezcla dos configuraciones (decide Diego).
- **Decisión de Diego: repetir los 200 casos con la configuración nueva** (no mezclar despliegues). Commit 2f6daa9
  (`--thinking-plantilla`). Lanzado ~17:50 UTC: `data/runs/tf_rieth_k5_thinkpl_n{0,2}` (1 proceso por nivel; fallas
  1,2,5,6,7,8,10,12,13,14; corridas 1–10; k=5, T=0,7, ampliado, t2, sin esquema, max_tokens 8000,
  `--thinking-plantilla`). Driver: aparta ERROR_LLM y reanuda con `--continuar`. Estimado ~28 h (≈200 s por llamada).
  Logs en `data/dev/rieth_thinkpl_n{0,2}.log`. La campaña vieja `tf_rieth_k5_think_*` (95/200) no se reporta.
- **También (Diego): brazo sin thinking en el despliegue nuevo** para que la comparación con/sin thinking sea del mismo
  despliegue: `data/runs/tf_rieth_k5_sd_n{0,2}` (mismos argumentos que `tf_rieth_k5_n{0,2}`: max_tokens 1500, sin
  razonamiento), 1 proceso, n0→n2, encolado hasta que termine un nivel con thinking (máx. 2 procesos). Log:
  `data/dev/rieth_sd.log`. ≈3,5 h.
- **Pausa por reinicio de la PC (17-oct ~01:25 UTC):** procesos detenidos a mano con thinkpl n0 65/100 y n2 40/100
  (JSON válidos; los 2 casos en curso se pierden y se repiten). Sin thinking aún sin empezar. 0 ERROR_LLM, 0,235 USD.
  Relanzar (los drivers usan `--continuar` solos si existe el manifiesto):
  `data/dev/drivers/rieth_thinkpl.sh 0 > data/dev/rieth_thinkpl_n0.log 2>&1 &`,
  `data/dev/drivers/rieth_thinkpl.sh 2 > data/dev/rieth_thinkpl_n2.log 2>&1 &`,
  `data/dev/drivers/rieth_sd_cola.sh > data/dev/rieth_sd.log 2>&1 &`. Comprobar `reasoning_tokens > 0` en el 1.er caso nuevo.
- **Relanzado 17-oct 14:25 UTC** tras el reinicio (pausa de ~13 h): thinkpl n0 desde 65/100, n2 desde 40/100, cola sin
  thinking esperando. Drivers en `data/dev/drivers/`.
- 17-oct ~15:05 UTC: n0 falla 10 corrida 6 → ERROR_LLM `ReadTimeout … (read timeout=600.0)` (una llamada con thinking
  superó 10 min). El driver lo aparta y lo reintenta al final de la pasada. `AMD_TF_TIMEOUT` en `.env`: 600 → **1200 s**
  (solo el tiempo de espera del cliente; no cambia la petición). Rige desde la siguiente pasada.
- 17-oct 15:44–16:15 UTC: caída de Gemma en Token Factory. Error exacto: `status=500 … Error from provider self-dploy: 503 Service Unavailable … "code":"no_available_workers","message":"No available workers (all circuits open or unhealthy)"`.
  Más ReadTimeouts de 600 s en las fallas 10 y 12 (n0) y la falla 7 (n2). A las 17:56 UTC hay 7 ERROR_LLM en n0 y 2 en n2; el driver los aparta y los reintenta al final de la pasada.
  Desde el 16:27 UTC el ritmo es ~15 min/caso por nivel (antes del reinicio era ~8). Válidos a las 17:56: n0 71/100 y n2 44/100.
- 17-oct ~21:00–21:35 UTC: la conexión a internet de la PC tuvo problemas (lo dijo Diego). Una llamada de prueba de 5 tokens tardó 14,4 s a las 21:07; tras arreglarla, a las 21:45, tardó 1,5–1,7 s.
  No hubo ERROR_LLM nuevos en ese tramo. Los casos de esas horas tardaron 1.600–3.000 s (antes ~600–850 s), pero no se puede separar cuánto fue la red y cuánto el servidor.
- 17-oct ~21:55 UTC: la demo pasa a reproducir el agente Evolus con Gemma (`agente_2026-10-16_biblioteca_gemma_v3`, antes `..._qwen_v2`).
  La traducción vieja (`traduccion_it_2026-10-16`) era del documento de Qwen, así que se regeneró sobre los documentos de Gemma v3: `traduccion_it_2026-10-17_gemma_v3`.
  Son 3/3 traducciones sin truncar, por 15,3 créditos de Evolus. Quedan pineadas, con el claim `evolus_traducciones_gemma_v3`. La traducción vieja se conserva como registro.
- 17-oct 22:01–~22:40 UTC: segunda caída de Gemma en Token Factory, con el mismo error que a las 15:44: `status=500 … self-dploy: 503 … "code":"no_available_workers"`.
  n0 tiene 5 ERROR_LLM nuevos, en la falla 14, corridas 1–5. n2 no tuvo ninguno. A las 22:43 UTC una llamada de prueba ya responde 200 en 6 s.
  Recuento: n0 83/100 válidos con 12 ERROR_LLM pendientes de reintento; n2 59/100.
- 17-oct ~23:25 UTC — CAMBIO DE PRIORIDADES (decisión de Diego). Desde la caída de las 22:01 el servidor genera a ~5,4 tok/s (medido a las 23:22 UTC: 171 tokens en 31,6 s); durante el día los casos iban a 10–40 tok/s.
  Con ese ritmo n0 y n2 con thinking no terminaban antes de la entrega, y el brazo sin thinking ni empezaba.
  Se paró n2 con thinking. Los ERROR_LLM pendientes se apartaron a `errores_429.jsonl`: 12 de n0 y 3 de n2.
  Estado al parar: n0 83/100 (fallas 10, 12 y 14 incompletas); n2 59/100 (completas 1, 2, 5, 6 y 8; la 7 con 8/10; la 10 con 1/10).
  Hueco A: n0 con thinking hasta 100/100, `AMD_TF_TIMEOUT=3600` por entorno.
  Hueco B, en este orden:
    1. `tf_rieth_k5_sd_n0`, completo.
    2. `tf_rieth_k5_sd_n2`, solo fallas 1, 2, 5, 6, 7 y 8.
    3. Reintento de n2 con thinking en la falla 7, corridas 2 y 3.
  Drivers en `data/dev/drivers/rieth_correr.sh` y `rieth_hueco_b.sh`; logs en `data/dev/rieth_a_n0.log` y `rieth_b.log`.
  n2 con thinking queda sin las fallas 10, 12, 13 y 14: se reportará como parcial (6 fallas). Ojo: `manifiesto.json` de n2 guardará los argumentos de la última pasada (solo `--fallas 7`); `inicio_original` se conserva.
- 18-oct ~00:00 UTC — DIAGNÓSTICO CORREGIDO. Llamada aparte con thinking en streaming: primer token a los 81,5 s y luego ~42 tok/s.
  El servidor no genera lento: está saturado y encola cada petición más de un minuto. Los "5,4 tok/s" de las 23:22 mezclaban la espera en cola con la generación.
  La llamada en curso de n0 con thinking (falla 10, corrida 6) llevaba 38 min abierta, cuando un caso completo de la falla 10 (5 llamadas) tardaba entre 8 y 25 min: se dio por colgada.
  Se paró y se relanzó con `--continuar` y `AMD_TF_TIMEOUT=1800`. El archivo quedó íntegro (83 líneas, 0 ERROR_LLM).
- 18-oct ~00:07 UTC — VIGILANTE AUTÓNOMO: `data/dev/drivers/vigilante.py` corre en segundo plano y escribe en `data/dev/vigilante.log`.
  Además de lo de antes (ERROR_LLM, casos, drivers caídos), mira por socket cuánto lleva abierta la llamada en curso de cada eval.correr. El umbral es 15 min con thinking y 5 min sin thinking.
  Al superarlo lanza una sonda en streaming de 5 tokens:
    - Si el primer token llega en menos de 60 s, la llamada está COLGADA: mata ese eval.correr por PID (máximo 3 veces por hora y campaña).
    - Si no, lo anota como servidor saturado y no toca nada.
  `rieth_correr.sh` ahora solo termina si eval.correr sale con rc=0 y sin ERROR_LLM; si lo matan, reanuda con `--continuar` a los 20 s (hasta 12 pasadas).
  Huecos A y B relanzados a las 00:06 UTC con `AMD_TF_TIMEOUT=1800`, sin perder casos.
- 18-oct ~00:24 UTC: la falla 10, corrida 6 de n0 con thinking se colgó dos veces seguidas. El vigilante la mató a las 00:21 UTC y el caso volvió a empezar en el acto: matar el proceso no avanza.
  Cambio: n0 con thinking pasa a `AMD_TF_TIMEOUT=900`. Una llamada colgada falla a los 15 min, queda como ERROR_LLM y el proceso sigue con el siguiente caso; los errores se reintentan al final de la pasada.
  El umbral del vigilante para thinking sube a 20 min, para que el timeout actúe primero.
  Hipótesis, sin comprobar: con el servidor saturado, las peticiones largas (~10k de prompt + hasta 8k de razonamiento) se pausan y reinician sin terminar, o la pasarela corta conexiones que pasan muchos minutos sin enviar datos (no usamos streaming).
- 18-oct ~03:25 UTC — Reparto de la falla 14 de n0 con thinking entre los dos huecos (lo pidió Diego):
  - Hueco A (`tf_rieth_k5_thinkpl_n0`): falla 12, corridas 1-2, y falla 14, corridas 1-5. `parar_a_tras_f14c5.sh` detiene su driver y su eval.correr en cuanto escribe la falla 14, corrida 5.
  - Hueco B: cuando termina `rieth_hueco_b.sh` (falta la falla 7, corrida 3 de n2), `rieth_hueco_b_f14.sh` corre la falla 14, corridas 6-10, en la carpeta aparte `tf_rieth_k5_thinkpl_n0_f14b` (dos procesos no escriben el mismo registros.jsonl). Mismos parámetros y timeout de 900 s.
  - Al terminar, los registros de `_f14b` se añaden al registros.jsonl de `tf_rieth_k5_thinkpl_n0`, verificando que no haya pares (falla, corrida) duplicados. La carpeta `_f14b` se conserva con su manifiesto como procedencia.
- 18-oct 03:33 UTC: la falla 7, corrida 3 de n2 con thinking se colgó dos veces (02:44 y 03:31 UTC) y bloqueaba el hueco B. Se abandona; detenidos rieth_hueco_b.sh, su driver y su eval.correr. n2 con thinking queda en 60 casos, con la falla 7 en 9/10. El hueco B pasa a la falla 14 de n0.
- 18-oct ~04:55 UTC: `reparto_f14.py` sustituye a `parar_a_tras_f14c5.sh` (Diego pidió pasar a B corridas de A cuando B termine).
  - A sigue la falla 14 en orden ascendente.
  - B, al terminar la 6-10, toma de una en una la corrida pendiente más alta de 1-5 que A no está haciendo. Lo hace en `_f14b`, con `--corridas N --continuar`, timeout de 900 s y hasta 4 intentos por corrida.
  - A se detiene en cuanto su siguiente corrida ya es de B.
  - El manifiesto de `_f14b` refleja los argumentos de la última invocación y conserva `inicio_original`.
- 18-oct ~05:00 UTC: deck con slide nueva `models` ("Two models, one gate", entre `reasons` y `thinking`, 13 slides; artifact v11). Compara Gemma y Qwen solo con claims existentes: qwen_vs_gemma_rechazo_* (22% / 31%, 9/2/1 fallas, p=0.04), think_rechazo_medias, qwen_think_rechazo_medias y evolus_v3_*. La frase sobre Qwen pasa de la nota de `reasons` a la narración de `models`.
- 18-oct ~05:20 UTC — Pitch v2, tras revisar con exa la rúbrica de lablab y guías de jueces:
  - Rúbrica de lablab (1-5): Presentation, Business value, Application of technology, Originality. El 5 en Presentation exige mercado, ingresos, planes futuros y análisis competitivo.
  - Slides nuevas `method` ("A controlled experiment") y `business` (coste ASM ≥ $10B al año en petroquímica de EE. UU. + coste por incidente estimado + modelo por consola + competencia). `close` añade NEXT. El deck pasa a 15 slides (artifact v13).
  - Narración reordenada: gancho → producto en una frase → demo → ¿razona o recita? → método → resultados → dos modelos → thinking → anticipación/benchmark → negocio → Evolus → auditoría → cierre.
  - Un subagente revisa guion y slides; el video se regenera solo tras la aprobación de Diego.
- 18-oct ~05:40 UTC — Pitch v3 tras la revisión del subagente (dos pasadas): fuera las frases sin respaldo ("in every training set" → "public since 1993"; "proves" → "is tested against reciting"; "Every team will show you…" → "Plenty of AI can name a fault…"; "every number" → "every result", porque 275 y $10B son citas externas). `models` en paralelo, con cifras de Braatz (rechazo 22/31%, top-1·top-3 3·7 frente a 7·9, FaultExplainer 8/11 frente a 5/11, "p = 0.04, borderline"). `reasons` muestra los dos niveles (7 pp IC [0, 18]; 5 pp [−4, 17]). `business` nombra al comprador, sin precio inventado. El video (4:22, voz edge-tts) usa cover, problem, invariant, demo, twin, method, reasons, models, thinking, business y close; early, benchmark, evolus y audit quedan solo en el PDF. Artifact v15.
- 18-oct 05:56 UTC — El contador de lablab marcaba "in 4 hours": el cierre real es ~10:00 UTC (05:00 Ecuador), no 15:00 UTC como decía arriba. Entrega enviada a las ~06:10 UTC con el video v3 y el PDF v15 (slide de thinking con cifras de Braatz, ya verificadas). La réplica de thinking en Rieth (n0, falla 14 pendiente) queda como trabajo posterior a la entrega.
