#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${HOME}/Documents/kenbot"

if [[ ! -d "${REPO_DIR}" ]]; then
  echo "Could not find ${REPO_DIR}"
  exit 1
fi

cd "${REPO_DIR}"

if [[ ! -d .git ]]; then
  echo "${REPO_DIR} is not a git repository."
  exit 1
fi

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
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -e .

echo "Stopping any process on port 5000"
if command -v lsof >/dev/null 2>&1; then
  lsof -tiTCP:5000 -sTCP:LISTEN | xargs -r kill
else
  fuser -k 5000/tcp 2>/dev/null || true
fi

echo "Starting kenbot GUI on http://127.0.0.1:5000"
setsid ./.venv/bin/python -m kenhallbot.gui >/tmp/kenhallbot-5000.log 2>&1 < /dev/null &

sleep 1

if lsof -nP -iTCP:5000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "kenbot is running on http://127.0.0.1:5000"
  echo "Logs: /tmp/kenhallbot-5000.log"
else
  echo "kenbot did not start successfully."
  echo "Check logs: /tmp/kenhallbot-5000.log"
  exit 1
fi
