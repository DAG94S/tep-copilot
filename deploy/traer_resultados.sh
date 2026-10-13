#!/usr/bin/env bash
# Trae de vuelta data/runs/ y logs/ del droplet. Ejecutar EN LOCAL, desde la raíz del repo:
#   bash deploy/traer_resultados.sh usuario@IP [ruta_remota_del_repo]
set -euo pipefail
HOST="${1:?Uso: $0 usuario@host [ruta_remota_del_repo]}"
REMOTO="${2:-~/tep-copilot}"
mkdir -p data/runs logs
if command -v rsync >/dev/null && ssh "$HOST" 'command -v rsync' >/dev/null 2>&1; then
  # Sin --delete: nunca borra nada local. -a conserva fechas; las corridas ya existentes no se pisan si son más nuevas.
  rsync -avz --update "$HOST:$REMOTO/data/runs/" data/runs/
  rsync -avz --update "$HOST:$REMOTO/logs/" logs/
else
  echo "rsync no disponible; usando scp" >&2
  scp -r "$HOST:$REMOTO/data/runs/." data/runs/
  scp -r "$HOST:$REMOTO/logs/." logs/
fi
echo "Traído. Verifica antes de destruir el droplet:"
ls -la logs/ data/runs/ | head -40
echo "Registra los SHA-256 de lo traído (regla 2 de AGENTS.md) y recuerda: DESTRUIR el droplet."
