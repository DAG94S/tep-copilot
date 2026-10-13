#!/usr/bin/env bash
# Campaña de evaluación contra el endpoint vLLM ya levantado (deploy/levantar_vllm.sh).
# Ejecutar donde esté el repo con el entorno Python (droplet o local con túnel SSH al puerto 8000):
#   AMD_VLLM_ENDPOINT=http://127.0.0.1:8000/v1 AMD_VLLM_API_KEY=... AMD_VLLM_MODEL=google/gemma-4-31B-it bash deploy/campana.sh
set -euo pipefail

# ---------------------------------------------------------------- variables
: "${AMD_VLLM_ENDPOINT:?Define AMD_VLLM_ENDPOINT (p. ej. http://127.0.0.1:8000/v1)}"
: "${AMD_VLLM_API_KEY:?Define AMD_VLLM_API_KEY}"
export AMD_VLLM_MODEL="${AMD_VLLM_MODEL:-google/gemma-4-31B-it}"
export AMD_VLLM_ENDPOINT AMD_VLLM_API_KEY
PY="${PY:-python3}"
LOG_DIR="${LOG_DIR:-$(cat logs/.ultimo 2>/dev/null || echo "logs/$(date +%Y-%m-%d)")}"
mkdir -p "$LOG_DIR"
ETIQ="${ETIQ:-$(date +%Y%m%d_%H%M)}"

# Campaña principal (el plan: niveles 0,1,2 · fallas 1-15 · k=5 · T=0.7 · semilla 0 · calibración ampliada)
CAMP1="${CAMP1:-amd_${ETIQ}_principal}"
FALLAS="${FALLAS:-1-15}"; NIVELES="${NIVELES:-0,1,2}"; K="${K:-5}"; TEMP="${TEMP:-0.7}"; SEMILLA="${SEMILLA:-0}"
CALIB="${CALIB:-ampliado}"; ESTAD="${ESTAD:-t2}"; MAX_TOKENS="${MAX_TOKENS:-800}"
# Réplica FaultExplainer: d00 / t2, k=1, temperatura 0, sin SPE (calibración de su protocolo). Poner CAMP2= para omitirla.
CAMP2="${CAMP2-amd_${ETIQ}_replica_d00}"
# Benchmark de rendimiento
BENCH_N="${BENCH_N:-64}"; BENCH_CONC="${BENCH_CONC:-1,4,8,16}"

T0=$(date +%s)
BASE="${AMD_VLLM_ENDPOINT%/}"
ROCM_PID=""
cleanup() { [[ -n "$ROCM_PID" ]] && kill "$ROCM_PID" 2>/dev/null || true; }
trap cleanup EXIT

# ---------------------------------------------------------------- (iv) rocm-smi periódico en segundo plano
if command -v rocm-smi >/dev/null; then
  ( while true; do echo "== $(date -u +%FT%TZ)"; rocm-smi --showuse --showmemuse --showpower --showtemp 2>&1; sleep 30; done ) \
    >> "$LOG_DIR/rocm_smi.log" 2>&1 &
  ROCM_PID=$!
else
  echo "AVISO: rocm-smi no está disponible aquí (¿corres desde local?). No habrá rocm_smi.log." >&2
fi

# ---------------------------------------------------------------- (i) humo
echo ">> humo: GET /v1/models"
curl -fsS -H "Authorization: Bearer $AMD_VLLM_API_KEY" "$BASE/models" | tee "$LOG_DIR/models.json"; echo
echo ">> humo: chat mínimo (comprueba que NO hay bloque de pensamiento)"
curl -fsS -H "Authorization: Bearer $AMD_VLLM_API_KEY" -H 'Content-Type: application/json' "$BASE/chat/completions" \
  -d "{\"model\":\"$AMD_VLLM_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Responde solo: ok\"}],\"max_tokens\":32,\"temperature\":0,
       \"chat_template_kwargs\":{\"enable_thinking\":false}}" | tee "$LOG_DIR/humo_chat.json"; echo

# ---------------------------------------------------------------- (ii) campañas
# PENDIENTE (Python, lo integra Diego): llm.cliente.desde_env NO lee extra_body de .env ni eval.correr lo pasa.
# Mitigación sin tocar Python: vLLM se lanzó con --default-chat-template-kwargs '{"enable_thinking": false}' y el
# template de Gemma 4 ya lo trae apagado por defecto, así que la campaña corre SIN thinking aunque el cliente no lo mande.
# Para dejarlo explícito en cada petición habría que hacer desde_env(..., extra_body={"chat_template_kwargs": {"enable_thinking": False}}).
echo ">> campaña principal: $CAMP1"
$PY -m eval.correr --campana "$CAMP1" --backend AMD_VLLM --fallas "$FALLAS" --niveles "$NIVELES" --k "$K" \
  --temperatura "$TEMP" --semilla "$SEMILLA" --calibracion "$CALIB" --estadistico "$ESTAD" --max-tokens "$MAX_TOKENS" \
  2>&1 | tee "$LOG_DIR/${CAMP1}.txt"

if [[ -n "$CAMP2" ]]; then
  echo ">> réplica d00/t2: $CAMP2"
  $PY -m eval.correr --campana "$CAMP2" --backend AMD_VLLM --fallas "$FALLAS" --niveles 0 --k 1 \
    --temperatura 0 --semilla "$SEMILLA" --calibracion d00 --estadistico t2 --max-tokens "$MAX_TOKENS" \
    2>&1 | tee "$LOG_DIR/${CAMP2}.txt"
fi

# ---------------------------------------------------------------- (iii) benchmark simple de rendimiento
echo ">> benchmark: $BENCH_N peticiones por nivel de concurrencia ($BENCH_CONC)"
BENCH_N="$BENCH_N" BENCH_CONC="$BENCH_CONC" BASE="$BASE" OUT="$LOG_DIR/bench.json" $PY - <<'PYEOF'
# Peticiones concurrentes con un prompt de ~2k tokens (similar al del caso real) y salida de 300 tokens.
import json, os, statistics, time
from concurrent.futures import ThreadPoolExecutor
import requests

base, modelo, clave = os.environ["BASE"], os.environ["AMD_VLLM_MODEL"], os.environ["AMD_VLLM_API_KEY"]
n = int(os.environ["BENCH_N"])
relleno = ("Variable X%d: valor medio %.2f, desviación %.2f. " * 1)
prompt = "Describe en detalle el estado del proceso.\n" + "".join(relleno % (i, i * 0.37, i * 0.05) for i in range(120))

def una(i):
    t0 = time.perf_counter()
    r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {clave}"}, timeout=600,
                      json={"model": modelo, "temperature": 0.7, "max_tokens": 300,
                            "messages": [{"role": "user", "content": f"[{i}] {prompt}"}]})
    r.raise_for_status()
    u = r.json()["usage"]
    return time.perf_counter() - t0, u["prompt_tokens"], u["completion_tokens"]

def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]

res = {"modelo": modelo, "n_por_nivel": n, "niveles": []}
for c in [int(x) for x in os.environ["BENCH_CONC"].split(",")]:
    t0 = time.perf_counter()
    with ThreadPoolExecutor(c) as ex:
        filas = list(ex.map(una, range(n)))
    dt = time.perf_counter() - t0
    lat = [f[0] for f in filas]
    res["niveles"].append({"concurrencia": c, "segundos_totales": round(dt, 2),
        "tok_s_salida": round(sum(f[2] for f in filas) / dt, 1), "tok_s_prompt": round(sum(f[1] for f in filas) / dt, 1),
        "lat_p50_s": round(statistics.median(lat), 2), "lat_p95_s": round(pct(lat, 0.95), 2),
        "prompt_tokens_medio": round(statistics.mean(f[1] for f in filas)), "salida_tokens_medio": round(statistics.mean(f[2] for f in filas))})
    print(res["niveles"][-1])
open(os.environ["OUT"], "w", encoding="utf-8").write(json.dumps(res, indent=2, ensure_ascii=False))
PYEOF

# ---------------------------------------------------------------- (v) cierre
cleanup; ROCM_PID=""
MIN=$(( ($(date +%s) - T0) / 60 ))
echo
printf '\033[1;31m%s\033[0m\n' "============================================================"
printf '\033[1;31m%s\033[0m\n' " CAMPAÑA TERMINADA en ${MIN} min. La GPU SIGUE COBRANDO."
printf '\033[1;31m%s\033[0m\n' " 1) bash deploy/traer_resultados.sh <usuario@IP>   (desde tu máquina)"
printf '\033[1;31m%s\033[0m\n' " 2) DESTRUIR el droplet en la consola de AMD Developer Cloud (apagar NO basta)."
printf '\033[1;31m%s\033[0m\n' "============================================================"
