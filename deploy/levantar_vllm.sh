#!/usr/bin/env bash
# Levanta Gemma 4 en vLLM-ROCm sobre la MI300X del droplet de AMD Developer Cloud.
# Ejecutar EN EL DROPLET, desde la raíz del repo:  AMD_VLLM_API_KEY=... bash deploy/levantar_vllm.sh
#
# Verificado el 2026-10-12 (ver docs/CAMPANA_AMD.md):
#  - Imagen: Docker Hub, API https://hub.docker.com/v2/repositories/vllm/vllm-openai-rocm/tags
#    El tag v0.31.0 EXISTE (actualizado 2026-10-04); digest del manifiesto multi-arquitectura abajo.
#  - Modelos: https://huggingface.co/api/models/google/gemma-4-31B-it  y  .../gemma-4-26B-A4B-it
#    ambos Apache-2.0 y NO gated (gated=False): no hace falta HF_TOKEN (se pasa solo si existe, por límites de descarga).
#  - Receta oficial AMD/Docker: https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html
#    (la imagen tiene como entrypoint el servidor OpenAI: se pasan los flags directamente, sin "vllm serve").
#  - Flags: https://docs.vllm.ai/en/v0.31.0/cli/serve/ (--attention-backend, --quantization/-q, --api-key,
#    --default-chat-template-kwargs existen en esa versión).
set -euo pipefail

# ---------------------------------------------------------------- variables
IMAGEN="${IMAGEN:-vllm/vllm-openai-rocm:v0.31.0@sha256:749f6f3f944f12af49966ac523c1f8573e4b229594b541954bd5f879b4496b1f}"
MODELO="${MODELO:-google/gemma-4-31B-it}"          # secundario: google/gemma-4-26B-A4B-it
PUERTO="${PUERTO:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"
# fp8 dinámico en línea para el 31B (plan). SIN VERIFICAR en ROCm+Gemma 4: si falla al cargar, relanzar con QUANT=none
# (el 31B en bf16 pesa ~62 GB y cabe de sobra en 192 GB; fp8 solo acelera/ahorra memoria).
QUANT="${QUANT:-fp8}"
# Backend de atención. El flag existe en v0.31.0 y TRITON_ATTN figura en la tabla de backends
# (https://docs.vllm.ai/en/v0.31.0/design/attention_backends/). Si es "auto", se deja la selección automática.
ATTN_BACKEND="${ATTN_BACKEND:-TRITON_ATTN}"
TIMEOUT_SALUD="${TIMEOUT_SALUD:-1500}"             # segundos esperando /health (descarga ~62 GB + carga + compilación)
NOMBRE="${NOMBRE:-vllm-gemma4}"
CACHE_HF="${CACHE_HF:-$HOME/.cache/huggingface}"
: "${AMD_VLLM_API_KEY:?Define AMD_VLLM_API_KEY (clave que protegerá el endpoint; no la commitees)}"
API_KEY="$AMD_VLLM_API_KEY"

FECHA="$(date +%Y-%m-%d)"
LOG_DIR="${LOG_DIR:-logs/$FECHA}"
mkdir -p "$LOG_DIR" "$CACHE_HF"
echo "$LOG_DIR" > logs/.ultimo        # lo lee deploy/campana.sh
T0=$(date +%s)

# ---------------------------------------------------------------- evidencia previa al arranque
{
  echo "== fecha UTC: $(date -u +%FT%TZ)"
  echo "== kernel: $(uname -a)"
  echo "== ROCm (/opt/rocm/.info/version): $(cat /opt/rocm/.info/version 2>/dev/null || echo 'no encontrado')"
  echo "== Docker: $(docker --version)"
} > "$LOG_DIR/entorno.txt"
rocm-smi --showproductname --showmeminfo vram > "$LOG_DIR/rocm_smi_inicial.txt" 2>&1 || echo "rocm-smi falló (ver archivo)" >&2
docker pull "$IMAGEN" 2>&1 | tee "$LOG_DIR/docker_pull.log"
docker image inspect "$IMAGEN" > "$LOG_DIR/docker_image_inspect.json"
docker image inspect "$IMAGEN" --format '{{json .RepoDigests}}' | tee "$LOG_DIR/imagen_digest.txt"

# ---------------------------------------------------------------- arranque del contenedor
docker rm -f "$NOMBRE" >/dev/null 2>&1 || true

ARGS=(--model "$MODELO" --host 0.0.0.0 --port "$PUERTO"
      --api-key "$API_KEY"
      --max-model-len "$MAX_MODEL_LEN"
      --gpu-memory-utilization "$GPU_MEM_UTIL"
      # Thinking APAGADO también del lado servidor: el template de Gemma 4 ya lo trae apagado por defecto
      # (enable_thinking | default(false)), esto lo fija explícitamente aunque el cliente no mande nada.
      --default-chat-template-kwargs '{"enable_thinking": false}'
      # Sin --reasoning-parser: el contenido sale completo en "content" (llm/parseo.py descarta bloques de pensamiento si aparecen).
      )
[[ "$QUANT" != "none" ]] && ARGS+=(--quantization "$QUANT")
[[ "$ATTN_BACKEND" != "auto" ]] && ARGS+=(--attention-backend "$ATTN_BACKEND")

ENV_HF=()
[[ -n "${HF_TOKEN:-}" ]] && ENV_HF=(--env "HF_TOKEN=$HF_TOKEN")

# Registrar los flags con la clave enmascarada (el log irá como evidencia).
printf '%s\n' "imagen=$IMAGEN" "modelo=$MODELO" "quant=$QUANT" "attn=$ATTN_BACKEND" "max_model_len=$MAX_MODEL_LEN" \
  "args=${ARGS[*]//$API_KEY/***}" > "$LOG_DIR/lanzamiento.txt"

# Dispositivos ROCm según la receta oficial; --network=host evita el mapeo de puertos.
docker run -d --name "$NOMBRE" \
  --device /dev/kfd --device /dev/dri --group-add video \
  --cap-add SYS_PTRACE --security-opt seccomp=unconfined \
  --ipc=host --shm-size 16g --network=host \
  -v "$CACHE_HF:/root/.cache/huggingface" \
  "${ENV_HF[@]}" \
  "$IMAGEN" "${ARGS[@]}" > "$LOG_DIR/container_id.txt"

# Logs del servidor en segundo plano
nohup docker logs -f "$NOMBRE" > "$LOG_DIR/vllm.log" 2>&1 &
echo $! > "$LOG_DIR/docker_logs.pid"

# ---------------------------------------------------------------- espera a /health
echo "Esperando a http://127.0.0.1:$PUERTO/health (máx. ${TIMEOUT_SALUD}s)..."
while true; do
  if curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1; then
    break
  fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$NOMBRE" 2>/dev/null)" != "true" ]]; then
    echo "ERROR: el contenedor murió. Últimas líneas:" >&2; tail -n 40 "$LOG_DIR/vllm.log" >&2; exit 1
  fi
  if (( $(date +%s) - T0 > TIMEOUT_SALUD )); then
    echo "ERROR: /health no respondió en ${TIMEOUT_SALUD}s" >&2; tail -n 40 "$LOG_DIR/vllm.log" >&2; exit 1
  fi
  sleep 5
done
ARRANQUE=$(( $(date +%s) - T0 ))
echo "$ARRANQUE" > "$LOG_DIR/tiempo_arranque_s.txt"
rocm-smi --showmeminfo vram > "$LOG_DIR/rocm_smi_tras_carga.txt" 2>&1 || true
echo "Listo en ${ARRANQUE}s. Endpoint: http://<IP_DROPLET>:$PUERTO/v1  (modelo: $MODELO)"
echo "En local, .env:  AMD_VLLM_ENDPOINT=http://<IP>:$PUERTO/v1   AMD_VLLM_MODEL=$MODELO   AMD_VLLM_API_KEY=<la clave>"
