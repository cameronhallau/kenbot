#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${HOME}/Documents/kenbot"
PYTHON_BIN="${REPO_DIR}/.venv/bin/python"
PIP_BIN="${REPO_DIR}/.venv/bin/pip"
LOG_FILE="/tmp/kenhallbot-5000.log"

kill_port_listener() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -tiTCP:${port} -sTCP:LISTEN || true)"
    if [[ -n "${pids}" ]]; then
      kill ${pids}
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null || true
  fi
}

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Could not find ${REPO_DIR}"
  exit 1
fi

cd "${REPO_DIR}"

if [[ ! -d .git ]]; then
  echo "${REPO_DIR} is not a git repository."
  exit 1
fi

echo "Stopping any process on port 9000"
kill_port_listener 9000

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
  echo "Could not determine the current git branch."
  exit 1
fi

echo "Updating repository on branch: $BRANCH"
git pull --rebase --autostash origin "$BRANCH"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment"
  python3 -m venv .venv
fi

echo "Installing latest editable build"
"${PYTHON_BIN}" -m pip install --upgrade pip
"${PIP_BIN}" install -e .

echo "Stopping any process on port 5000"
kill_port_listener 5000

echo "Starting kenbot GUI on http://127.0.0.1:5000"
nohup "${PYTHON_BIN}" -m kenhallbot.gui >"${LOG_FILE}" 2>&1 &

sleep 1

if lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Repository: ${REPO_DIR}"
  echo "Python: ${PYTHON_BIN}"
  echo "kenbot is running on http://127.0.0.1:5000"
  echo "Logs: ${LOG_FILE}"
else
  echo "kenbot did not start successfully."
  echo "Check logs: ${LOG_FILE}"
  exit 1
fi
