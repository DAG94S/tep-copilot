# Campaña en AMD Developer Cloud (1×MI300X) — checklist

Presupuesto: **≤3 GPU-h** (MI300X ≈ $1,99/h según `STATE.md` → **≈ $6**; con holgura a 5 h ≈ $10). El droplet cobra aunque esté apagado: **se destruye al terminar**.
Scripts: `deploy/levantar_vllm.sh`, `deploy/campana.sh`, `deploy/traer_resultados.sh`. Verificaciones web hechas el 2026-10-12.

## Lo verificado (con fuente)

| Qué | Resultado | Fuente |
|---|---|---|
| Imagen | `vllm/vllm-openai-rocm:v0.31.0` **existe** (subida 2026-10-04). Digest del manifiesto: `sha256:749f6f3f944f12af49966ac523c1f8573e4b229594b541954bd5f879b4496b1f` (coincide con `latest`) | `https://hub.docker.com/v2/repositories/vllm/vllm-openai-rocm/tags?page_size=50` |
| Modelo principal | `google/gemma-4-31B-it` — Apache-2.0, **no gated** | `https://huggingface.co/api/models/google/gemma-4-31B-it` |
| Modelo secundario | `google/gemma-4-26B-A4B-it` — Apache-2.0, **no gated** | `https://huggingface.co/api/models/google/gemma-4-26B-A4B-it` |
| Apagar thinking | kwarg **`enable_thinking`** del chat template. En el `chat_template.jinja` el valor por defecto ya es `false` (`enable_thinking \| default(false)`); con `false` el template añade `<\|channel>thought\n<channel\|>` vacío. La model card usa `enable_thinking=False` | `https://huggingface.co/google/gemma-4-31B-it/raw/main/chat_template.jinja` y `.../README.md` |
| Flag atención | `--attention-backend` existe en v0.31.0; `TRITON_ATTN` es un backend listado (fp16/bf16, ROCm incluido) | `https://docs.vllm.ai/en/v0.31.0/cli/serve/` y `.../design/attention_backends/` |
| Flag cuantización | `--quantization` / `-q` existe (`fp8`) | `https://docs.vllm.ai/en/v0.31.0/cli/serve/` |
| Thinking en servidor | `--default-chat-template-kwargs '{"enable_thinking": false}'` existe | misma página de `serve` |
| Receta ROCm Gemma 4 | `docker run --device=/dev/kfd --device=/dev/dri --group-add=video --ipc=host --shm-size 16G ... vllm/vllm-openai-rocm:<tag> --model <MODELO> --host 0.0.0.0 --port 8000` (entrypoint = servidor; sin `vllm serve`) | `https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html` |

Nota: la receta recomienda `--reasoning-parser gemma4` solo para el modo thinking. Con thinking apagado **no se usa**; así todo el texto llega en `content`.

## Cómo pasar el kwarg de thinking (pendiente de integrar en Python)

`llm.cliente.ClienteLLM` acepta `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` (hay test), pero **`desde_env` no lo lee de `.env` y `eval.correr` no lo pasa**: hoy la campaña no lo envía por petición. **Pendiente para Diego:** p. ej. en `desde_env`, leer `{prefijo}_EXTRA_BODY` (JSON) y pasarlo como `extra_body`; o fijarlo en `correr.py` para `AMD_VLLM`.
Mientras tanto la campaña **sí corre sin thinking** por dos vías independientes: (1) el default del template es `false`; (2) `levantar_vllm.sh` lanza vLLM con `--default-chat-template-kwargs '{"enable_thinking": false}'`. Verificarlo con la evidencia 6 (abajo): ningún `<thought>` en las salidas y `completion_tokens` bajos. Si quieres que quede registrado en el manifiesto, hace falta el cambio de Python.

## Checklist (tiempos estimados)

Costes: el reloj de la GPU corre desde crear el droplet. Meta de campaña activa ≈ 2,5 h.

1. **Antes de crear nada (0 GPU-h, ~20 min).** `pytest` en verde, `git status` limpio, commit/push del repo (el droplet clonará de ahí). Tener a mano: clave API de vLLM nueva (`openssl rand -hex 24`), clave SSH, `.env` local. Confirmar crédito o tarjeta (corte plan B: 13 oct).
2. **Crear el droplet (~5–10 min, ya cobra).** Imagen con Docker+ROCm, 1×MI300X. Anotar IP, región, fecha/hora de creación. Capturar la pantalla de la consola con el plan y precio/hora. **Evidencia 1.**
3. **Preparar el droplet (~10 min).** `ssh`, `git clone` del repo, `python3 -m venv .venv && pip install -r requirements.txt`. Comprobar `rocm-smi` y `docker ps`. Abrir el puerto 8000 solo si no usas túnel (preferible `ssh -L 8000:127.0.0.1:8000`; con túnel no hace falta abrirlo).
4. **Datos (~10–15 min).** Los datos que usa la campaña (d00–d21) pesan 26 MB: `python3 scripts/descargar_datos.py` y `python3 scripts/verify_claims.py` (SHA256SUMS). *No* hace falta Rieth/Faulty_Testing para esta campaña salvo que se decida lo contrario.
5. **Levantar vLLM (~15–25 min: descarga ~62 GB + carga + compilación).** `AMD_VLLM_API_KEY=... bash deploy/levantar_vllm.sh`. Deja en `logs/<fecha>/`: `entorno.txt`, `rocm_smi_inicial.txt`, `imagen_digest.txt`, `docker_image_inspect.json`, `lanzamiento.txt`, `vllm.log`, `tiempo_arranque_s.txt`. **Evidencia 2.** Descargar el modelo es el paso más largo y no aporta datos: mientras tanto avanza el paso 4.
   - Si falla con fp8: `QUANT=none bash deploy/levantar_vllm.sh` (anota el error exacto en `STATE.md`, regla 6). Si falla con el backend: `ATTN_BACKEND=auto`.
6. **Humo (~2 min).** Primera parte de `campana.sh` (`/v1/models` y un chat). Probar también sin clave → debe dar 401. **Evidencia 3.**
7. **Campaña principal (~60–90 min, estimado SIN medir).** 15 fallas × 3 niveles × k=5 = 225 llamadas × 5 muestras. Con Gemini el 31B tardó 67–109 s por llamada pensando; sin thinking y en MI300X debería bajar mucho, pero **no hay medición**. Si pasa de ~2 h, cortar y usar `--continuar` (la campaña es reanudable). Ojo: `ClienteLLM` tiene timeout de 120 s por petición; con n=5 podría quedarse justo bajo carga → vigilar `ERROR_LLM` en la tabla.
   Ejecutar: `AMD_VLLM_ENDPOINT=http://127.0.0.1:8000/v1 AMD_VLLM_API_KEY=... bash deploy/campana.sh` (usa tmux/`nohup`: una desconexión SSH no debe matar la campaña).
8. **Réplica d00/t2 (~10–15 min).** La corre el propio `campana.sh` (k=1, T=0, calibración d00, solo nivel 0). Se omite con `CAMP2=`.
9. **Benchmark (~10 min).** También dentro de `campana.sh`; escribe `logs/<fecha>/bench.json` (tok/s de salida y de prompt, latencia p50/p95 por concurrencia 1/4/8/16). `rocm_smi.log` se llena cada 30 s durante todo el script. **Evidencia 4.**
10. **Opcional con holgura (≤30 min):** repetir con `MODELO=google/gemma-4-26B-A4B-it` (relanzar el contenedor, `AMD_VLLM_MODEL` igual). Solo si el total acumulado va < 2,5 h.
11. **Traer resultados (~5 min).** Desde local: `bash deploy/traer_resultados.sh usuario@IP`. Comprobar que `data/runs/amd_*` tiene `registros.jsonl` y `manifiesto.json` y que `logs/<fecha>/` está completo. Registrar SHA-256.
12. **Apagar el contenedor y DESTRUIR el droplet (~2 min).** `docker stop vllm-gemma4`; luego **destruir** (no solo apagar) desde la consola de AMD. Capturar la confirmación y el panel de facturación. **Evidencia 5.** Anotar hora de destrucción y GPU-h totales en `STATE.md`.

Total objetivo: **≈ 2,5–3 h de GPU ≈ $5–6**; a mayor tiempo, $1,99 por hora adicional.

## Evidencias para los jueces

1. Captura de la consola de AMD con el droplet MI300X (plan y precio) y, al final, su destrucción/factura.
2. `rocm-smi --showproductname` (MI300X, 192 GB), versión de ROCm/kernel y el **digest** de la imagen (`logs/<fecha>/`).
3. `models.json` con el modelo servido y la prueba de que sin clave responde 401.
4. `bench.json` y `rocm_smi.log` (uso y VRAM durante la campaña).
5. `vllm.log` completo (arranque, carga del modelo, fp8, backend de atención elegido).
6. `data/runs/amd_*/registros.jsonl` + `manifiesto.json` (commit, argumentos, endpoint, modelo) con SHA-256 y verificación de ausencia de `<thought>`.
7. Tabla final de `eval.correr` (copiada de `logs/<fecha>/amd_*.txt`) y el comando exacto usado.

Todo número del README/deck sale de `data/runs/` vía script (regla 3).

## SIN VERIFICAR (no hay GPU para probarlo todavía)

- `--quantization fp8` con Gemma 4 31B **en ROCm/MI300X**: el flag existe, pero no se encontró página que confirme el soporte para este modelo en esta imagen (la página de FP8 de v0.31.0 redirige a LLM Compressor y no menciona ROCm). Fallback: `QUANT=none` (bf16 ≈ 62 GB, cabe en 192 GB). Si no hay diferencia práctica, la comparación de calidad fp8 vs bf16 no es objetivo de esta campaña.
- `--attention-backend TRITON_ATTN` **con Gemma 4 en ROCm**: el flag y el valor existen en v0.31.0, pero no está confirmado que sea el backend que la imagen elegiría ni el óptimo; la receta oficial no lo fija. Fallback: `ATTN_BACKEND=auto`.
- Que el entrypoint de la imagen `v0.31.0` acepte los flags tal como en la receta (que usa `latest`, hoy el mismo digest que v0.31.0, así que es consistente, pero no probado).
- Compatibilidad de `--default-chat-template-kwargs` pasando JSON con comillas simples vía bash array (sintaxis comprobada con `bash -n`, no ejecutada).
- Tiempos de descarga/arranque/campaña y latencias: **todos estimados**, hasta que `tiempo_arranque_s.txt` y `bench.json` den datos.
- Integración Python del `extra_body` (ver arriba): pendiente de Diego.
- Imagen de plantilla del droplet (si ya trae Docker+ROCm y qué versión de ROCm del host exige la imagen v0.31.0): depende del catálogo de AMD Developer Cloud, no consultable sin cuenta.
