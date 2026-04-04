#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${HOME}/Documents/kenbot"
URL="http://127.0.0.1:5000"
LOG_FILE="/tmp/kenhallbot-5000.log"

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Could not find ${REPO_DIR}"
  exit 1
fi

cd "${REPO_DIR}"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing virtual environment at ${REPO_DIR}/.venv"
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  lsof -tiTCP:9000 -sTCP:LISTEN | xargs -r kill
fi

if command -v lsof >/dev/null 2>&1; then
  lsof -tiTCP:5000 -sTCP:LISTEN | xargs -r kill
fi

nohup ./.venv/bin/python -m kenhallbot.gui >"${LOG_FILE}" 2>&1 &

for _ in {1..20}; do
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 &
elif command -v sensible-browser >/dev/null 2>&1; then
  sensible-browser "${URL}" >/dev/null 2>&1 &
fi

echo "kenbot is starting at ${URL}"
echo "Logs: ${LOG_FILE}"
