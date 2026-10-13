# Réplica de FaultExplainer: protocolo exacto

Fuente: Khan et al. (2025), arXiv 2412.14492 ("el paper"), y el repo `li-group/FaultExplainer` (MIT) fijado en el commit
`2fcfee975a687c350f10909eeccd1ecdd60340be`, copiado en `third_party/faultexplainer/` (ver `PROCEDENCIA.md`).
Rutas `archivo:línea` son relativas a `third_party/faultexplainer/`. Lo que no está en código ni paper se marca **NO ENCONTRADO**.
Los CSV de datos no se versionan; los inspeccioné en un directorio temporal (500 filas por corrida, ver 1).

## 0. Hallazgo previo: el repo contiene dos rutas de ejecución que no coinciden del todo
- **App en vivo** (`frontend/src/App.tsx` + `backend/app.py`): reproduce una corrida CSV fila a fila y, a la 6.ª alarma consecutiva
  (ver 5), manda las 6 variables de mayor contribución a `/explain`.
- **Script de evaluación** (`backend/test_explain.py`): es el que produjo las tablas del paper (itera fallas 3 a 15, ambos prompts,
  ambos modelos). Sus parámetros son los que cuentan para la réplica.
- `backend/results.txt` está **vacío (0 bytes)**: las salidas de los LLM NO están en el repo (el paper dice que van en el material suplementario; **NO ENCONTRADO** aquí).

## 1. Datos
- Paper §5.1 (p.12): series de "operación normal y las 15 fallas conocidas" de Rieth et al. (2017), "41 medidas y 12 manipuladas,
  cada serie con 500 pasos de tiempo". La normal entrena el PCA.
- Código: `backend/model.py:250` entrena con `./backend/data/fault0.csv`; evaluación con `frontend/public/fault{i}.csv`
  (`test_explain.py:35`). Cada CSV que inspeccioné tiene 500 filas, columna `time` de 0,05 a 25,0 h (paso 0,05 h = 3 min) y 52 columnas de variables.
  (`frontend/src/App.tsx:504` también asume 3 min por 0,05 h.) Las 500 filas/25 h coinciden con el tamaño de las corridas de **entrenamiento** de Rieth, pero eso es una inferencia mía.
- **NO ENCONTRADO:** qué `simulationRun` (semilla) de Rieth se usó; el paso en que arranca la falla (el código no lo usa; solo exige 6 alarmas consecutivas, `test_explain.py:44-46`); el script que convirtió el RData de Rieth a esos CSV.
- Existen `fault16..20.csv` en el repo pero ningún código los usa (el catálogo de causas es de 15; `prompts.py:198-212`).
- Observación: `fault0.csv` es a la vez entrenamiento y fuente de la "media normal" (`features_mean_std.csv`, 52 filas); ver 3.

## 2. Variables
- 52 columnas (41 XMEAS + 11 XMV; el paper dice "12 manipuladas" en §5.1, pero `prompts.py:94-107` lista 11 y `features_mean_std.csv` tiene 52 variables).
  Nombres en texto libre (p. ej. `A Feed`, `Reactor Pressure`, `A feed load`), no códigos XMEAS/XMV (`backend/stats/features_mean_std.csv`).
- Todas entran al PCA: `model.fit(training_data)` sin selección (`model.py:250-254`, `model.py:23-26`).
  El filtro `importanceFilter` de la app (`App.tsx:195`) lista las columnas `t2_*` elegibles para el top-k.

## 3. Normalización, PCA, umbral
- `StandardScaler()` de sklearn (`model.py:11`): media y desviación **poblacional (ddof=0)** de `fault0.csv`; se guardan en `backend/stats/features_mean_std.csv` (`model.py:26`, `:36-43`).
- `PCA(n_components=0.9)` (`model.py:9,12`): 90% de varianza acumulada (paper §5.1). Número de componentes `a`: **NO ENCONTRADO** en repo/paper (se calcula al ejecutar).
- T² = z·P·diag(1/λ)·Pᵀ·zᵀ con `λ = pca.explained_variance_` (ddof=1 de sklearn) (`model.py:32`, `:65`).
- Umbral: `(a(n−1)(n+1))/(n(n−a)) · F⁻¹(1−α; a, n−a)`, con `alpha=0.01`, `n = pca.n_samples_` (`model.py:9`, `:45-54`); paper Ec. 2 y §5.1.

## 4. Contribuciones
- Fórmula de Kourti–MacGregor: `c_ji = (t_i/λ_i)·p_ji·z_j`, con `t = zᵀP` (`model.py:154-165`; paper Ec. 3).
  **Se trunca a 0 cada término c_ji antes de sumar sobre componentes** (`model.py:161`, `np.maximum(c_ji, 0)`), luego `C_j = Σ_i max(c_ji,0)` (`model.py:164`).
- **En un único punto**, no promedio de ventana: `test_explain.py:56` toma la fila `first_anomaly_index` y ordena sus contribuciones `t2_*` de mayor a menor; top 6 con `topkfeatures=6` (`config.json:4`, `test_explain.py:59`, `App.tsx:284`). Paper §5.1: "las seis con mayor contribución en el último paso de tiempo".

## 5. Regla de alarma
- `anomaly = T² > umbral` por fila (`model.py:70`).
- Evaluación: `window_size = 6`; `first_anomaly_index = idxmax(rolling(6).sum() == 6)` (`test_explain.py:44-46`). Es el índice de la **6.ª alarma de una racha de 6**.
  Config: `fault_trigger_consecutive_step: 6` (`config.json:3`); paper §5.1 (6 consecutivas, falsa alarma 0,01⁶ = 1e-12).
- Si no hay racha: escribe "PCA is not able to identify Fault i" y sigue (`test_explain.py:67-69`).
- Nota: no se verifica que la racha sea posterior al inicio de falla (NO ENCONTRADO el inicio); `rolling` recorre toda la serie desde el paso 0.
- App en vivo: `postFaultThreshold = 6-1` fijo (`App.tsx:283`; la lectura de `config.json` está comentada, `:277-282`); el backend Python tiene otro `post_fault_threshold = 20` (`model.py:19-21`, `:89`) que no gobierna la evaluación. `analysis.py:79` usa `window_size = 20` (script exploratorio).

## 6. Qué recibe el LLM (datos numéricos)
- `test_explain.py:62-65`: se pasa la lista de valores de cada una de las 6 variables hasta `first_anomaly_index`, pero `generate_feature_comparison` **solo usa el último valor** (`values[-1]`, `app.py:188`). No hay ventana ni desviaciones.
- Por variable se imprime (`app.py:200-205`): `Feature: <nombre>\n  - Faulty Data: Value = {x:.3f},  - Normal Conditions: Mean = {m:.3f},  - Percentage Changes: Value Change = {pct:.2f}%, `
  con `pct = (valor − media_normal)/media_normal·100` (`app.py:197`). La media sale de `stats/features_mean_std.csv`. **La desviación estándar NO se envía** (`app.py:194` solo lee `mean`; `fault_std` en `:177` no se usa). Sin z-score ni valor de contribución.
- Emparejamiento del nombre con `str.contains(feature, case=False)` sobre la tabla y toma el primer resultado (`app.py:191-194`).
  Dependiente del orden del CSV para `A Feed`/`D Feed`/`E Feed`/`A and C Feed`, que también aparecen dentro de `A feed load`… (medido: esos 4 nombres coinciden con 2 filas; la primera es la medida).
- Encabezado: `"The top feature changes are\n" + ...` (`app.py:213`).

## 7. Prompt (texto exacto en `backend/prompts.py`)
- Un solo mensaje de rol `user` (no hay rol `system`): `SYSTEM_MESSAGE + PROMPT_SELECT + "\n" + comparación` (`app.py:221-229`; `test_explain.py:83-90`, con un sufijo extra de formato LaTeX en `:78-81`, `:88`).
- `SYSTEM_MESSAGE` (`prompts.py:113-120`): "You are a helpful AI chatbot trained to assist with monitoring the Tennessee Eastman process…" + `INTRO_MESSAGE` (`:1-110`): descripción de reacciones, 5 unidades, corrientes 1 a 12, lista de 41 variables medidas con unidades (`:52-92`) y 11 manipuladas (`:97-107`), con nombres reales de TEP.
- Prompt "root causes included" = `EXPLAIN_ROOT` (`prompts.py:163-213`). Pide: comparar con operación normal, "From the list of 16 predefined root causes … identify the three most likely causes" (`:178`; **la lista trae 15, no 16**), explicar propagación, decir cuántas de las 6 variables explica cada causa, párrafo coherente sin viñetas, "Ensure Deterministic Responses".
- Prompt "general reasoning" = `EXPLAIN_PROMPT` (`prompts.py:123-161`): sin catálogo, "Identify up to THREE root causes" (`:142`).
- Mapeo con el paper: §4.2 y §5.1 llaman "Root Causes-Included Prompt" al primero y "General Reasoning Prompt" al segundo (el paper §4.2 los nombra en orden confuso; el código es inequívoco).
- Salida: **texto libre en prosa**; no hay esquema JSON. Los números de causa del catálogo se leen del texto (cómo se extrajeron para Tabla 1: **NO ENCONTRADO**).

## 8. Catálogo de causas
15 entradas, texto exacto en `prompts.py:198-212` (también `analysis.py:9-26`): `IDV(1) A/C Feed Ratio, B Composition Constant (Stream 4) & Step` … `IDV(15) Condenser Cooling Water Valve & Sticking`.
Incluye IDV(1) a IDV(15) en orden natural y con el número IDV visible; el sufijo ("& Step", "& Random Variation", "& Slow Drift", "& Sticking") es parte del texto. Las IDV 16 a 20 no están.

## 9. Modelo y parámetros
- `config.json:2`: `"model": "gpt-4o"`; modelos permitidos `gpt-4o`, `o1-mini`, `o1-preview` (`app.py:28`). Paper §5.1: GPT-4o y o1-preview.
- Temperatura 0 salvo o1 (1) (`app.py:113`, `:141`). `seed=12345` en la evaluación (`test_explain.py:92,94`). En la app en vivo `/explain` NO pasa la semilla (la variable local `seed` de `app.py:231` no se usa; `ChatModelCompletion` usa `seed=0`, `app.py:110`).
- Para o1 se **descarta el rol system** (`app.py:116-117`; irrelevante, porque el prompt va todo en un solo `user`).
- `max_tokens`, `top_p`, versión exacta de gpt-4o / o1-preview: **NO ENCONTRADO** (`openai==1.34.0`, `requirements.txt`).
- Una sola muestra por (falla, prompt, modelo); sin voto ni repetición (`test_explain.py:75-96`).

## 10. Criterio de acierto y fallas evaluadas
- Paper §5.2.1 (p.13): el LLM da las tres causas más probables; es acierto si la verdadera **o su alias** aparece entre ellas. Alias definidos en Tabla 1 (p.14), p. ej. Falla 1 (alias 8), Falla 3 (alias 9), Falla 4 (alias 11, 14), Falla 5 (alias 12, 15). La lógica de puntuación **no está en el código** (NO ENCONTRADO): se hizo a mano.
- Fallas evaluadas: `range(3, 16)` en el script (`test_explain.py:32`), es decir 3 a 15, pero la Tabla 1 del paper cubre 1 a 15.
  **Inconsistencia:** el script no corre las fallas 1 y 2, que sí aparecen en el paper; no se sabe cómo se obtuvieron.
- PCA detecta 11 de 15 (§5.2.1). No detectadas (marcadas "\" en Tabla 1): **3, 4, 9, 15**. Detectadas: 1, 2, 5, 6, 7, 8, 10, 11, 12, 13, 14.
- Resultado reportado (§5.2.1): **GPT-4o 7/11, o1-preview 9/11**; ninguno acierta 5 ni 10.
- Aciertos por falla: las negritas de la Tabla 1 no sobreviven en el texto del PDF. **Derivación mía** (acierto = causa verdadera o alias en las 3 propuestas de Tabla 1): reproduce exactamente 7 y 9.
  - GPT-4o (7): fallas 2 (6,1,8: alias 8), 6, 7, 11 (4,5,6: alias 4), 12 (alias 5), 13, 14 (alias 4). Falla 1 (6,7,4), 5 y 8 y 10 fallan.
  - o1-preview (9): fallas 1 (6,1,7), 2, 6, 7, 8 (6,7,1: alias 1), 11, 12, 13, 14. Fallan 5 y 10.
  - Verificar contra las negritas del PDF original antes de citar por falla.
- General Reasoning (Tabla 2): ambos aciertan o relacionan 8 de 11; fallan en 10 y 13 (§5.3.1). Criterio "relacionado con la verdad": subjetivo, no automatizado.

## 11. Diferencias con nuestra implementación

Comparación con `core/pca_t2.py`, `llm/prompt.py`, `eval/pipeline.py` (solo lectura, sin cambios).

| Aspecto | FaultExplainer | Nuestro repo | Coincide | Para replicar fielmente |
|---|---|---|---|---|
| Datos | Rieth 2017, 500 pasos por corrida, `fault0` entrena (`model.py:250`) | Braatz d00 (500) para entrenar; evaluación en `d??_te` (960 muestras) (`eval/pipeline.py:48-50`) | No | Cargar Rieth (Harvard Dataverse) y reproducir su corrida de 500 pasos; `simulationRun` aún desconocido |
| Escalado | `StandardScaler` ddof=0 (`model.py:11`) | `std(ddof=1)` (`pca_t2.py:43`) | Casi | Cambiar a ddof=0 (efecto pequeño con n=500, pero medible) |
| % varianza, α | 0,90; 0,01 (`model.py:9`) | 0,90; 0,01 (`pca_t2.py:18-19`) | Sí | Nada. Ojo: sklearn y `searchsorted` pueden diferir en 1 componente en el borde |
| Umbral T² | fórmula F con `n_samples_` (`model.py:49-54`) | misma fórmula (`pca_t2.py:50`) | Sí | Nada |
| Alarmas consecutivas | 6, índice de la 6.ª (`test_explain.py:44-46`) | 6, índice al cumplirse la racha (`pca_t2.py:81-100`) | Sí | Nada; añadir la comprobación opcional de inicio de falla es extensión nuestra |
| Contribuciones | trunca cada c_ji a 0 antes de sumar (`model.py:161`) | suma sobre componentes y luego trunca (`pca_t2.py:107-108`) | **No** | Truncar por término `max(c_ji,0)` y luego sumar |
| Dónde se calculan | un punto: fila de la 6.ª alarma (`test_explain.py:56`) | **media de la ventana de 6** (`pipeline.py:60-61`) | **No** | Usar solo la fila `i` |
| Valor mostrado | solo el último valor, % de cambio vs media (`app.py:188,197`) | media de la ventana, z, contribución (`pipeline.py:65-66`, `prompt.py:39-44`) | **No** | Imprimir valor, media normal y % de cambio; no z ni contribución |
| Descripción y nombres | planta real con nombres TEP (`prompts.py:1-110`) | vista disfrazada con tags neutros (`prompt.py:37-38`; el nivel 0 de la gemela se acerca) | Parcial | Para el brazo réplica usar `prompts.py` tal cual |
| Prompt | un `user`, prosa, formato libre (`app.py:223-229`) | `system` + `user`, salida JSON con esquema (`prompt.py:7-20`) | **No** | Usar `SYSTEM_MESSAGE + EXPLAIN_ROOT + comparación` en un único `user` |
| Catálogo | 15 causas con "IDV(n)" y texto original (`prompts.py:198-212`) | catálogo barajado con códigos (`prompt.py:45-46`; nivel 0 sin barajar) | Parcial | Texto exacto de FaultExplainer, sin códigos |
| Salida y puntuación | texto libre; top-3 y alias a mano (paper §5.2.1) | JSON y compuerta; `acierto_top1/top3` por IDV (`pipeline.py:133`) | **No** | Parsear los números IDV del texto (o `idv` regex) y definir alias de Tabla 1 como regla explícita |
| Modelo | gpt-4o / o1-preview, T=0, seed 12345 (`app.py:113`, `test_explain.py:92`) | Gemma 4 (vLLM) | No (inevitable) | Declarar que la réplica es del protocolo, no del modelo; fijar T=0 |
| Muestras | 1 por caso | `k` muestras con voto (`pipeline.py:105`) | Parcial | k=1 |
| Fallas | 1 a 15 (paper); script 3 a 15 (`test_explain.py:32`) | 1 a 21 | Parcial | Reportar sobre las 11 detectadas por T² (1,2,5,6,7,8,10,11,12,13,14) |
| Estadístico | solo T² | T² por defecto, SPE como extensión (`pca_t2.py:81-92`) | Sí con `estadistico="t2"` | Mantener T² |

## 12. Fuentes
- Khan A., Nahar R., Chen H., Flores G.E., Li C. (2025). FaultExplainer. *Computers & Chemical Engineering*; arXiv 2412.14492 (§4.1 Ec. 2 y 3, §4.2, §5.1, §5.2.1, Tabla 1, §5.3.1, Tabla 2).
- Repo `li-group/FaultExplainer` @ `2fcfee975a687c350f10909eeccd1ecdd60340be`, MIT.
- Rieth C.A., Amsel B.D., Tran R., Cook M.B. (2017). Additional Tennessee Eastman Process Simulation Data for Anomaly Detection Evaluation. Harvard Dataverse.
