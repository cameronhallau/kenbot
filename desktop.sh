#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${HOME}/Documents/kenbot"
PYTHON_BIN="${REPO_DIR}/.venv/bin/python"
URL="http://127.0.0.1:5000"
LOG_FILE="/tmp/kenhallbot-5000.log"

kill_port_listener() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return
  fi
  local pids
  pids="$(lsof -tiTCP:${port} -sTCP:LISTEN || true)"
  if [[ -n "${pids}" ]]; then
    kill ${pids}
  fi
}

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Could not find ${REPO_DIR}"
  exit 1
fi

cd "${REPO_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing virtual environment at ${PYTHON_BIN}"
  exit 1
fi

kill_port_listener 9000
kill_port_listener 5000

nohup "${PYTHON_BIN}" -m kenhallbot.gui >"${LOG_FILE}" 2>&1 &

for _ in {1..20}; do
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if command -v open >/dev/null 2>&1; then
  open "${URL}" >/dev/null 2>&1 &
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 &
elif command -v sensible-browser >/dev/null 2>&1; then
  sensible-browser "${URL}" >/dev/null 2>&1 &
fi

echo "Repository: ${REPO_DIR}"
echo "Python: ${PYTHON_BIN}"
echo "kenbot is starting at ${URL}"
echo "Logs: ${LOG_FILE}"
