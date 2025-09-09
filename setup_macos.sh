#!/usr/bin/env bash
set -euo pipefail

# Move to script directory
cd "$(dirname "$0")"

echo "[1/4] Locating Python and creating virtual environment (if needed)"
# Prefer python3, fallback to python
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
    elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: No 'python3' or 'python' executable found in PATH." >&2
    echo "Install Python 3 and try again." >&2
    exit 1
fi

# Create venv if missing or if activate script is missing
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    echo "(Re)creating virtual environment using '$PYTHON' ..."
    rm -rf venv
    "$PYTHON" -m venv venv
fi

echo "[2/4] Activating venv and upgrading pip"
if [ ! -f "venv/bin/activate" ]; then
    echo "Error: venv/bin/activate not found after creation. Python used: $PYTHON" >&2
    echo "Please ensure Python has the venv module: '$PYTHON -m ensurepip --upgrade' then retry." >&2
    exit 1
fi

source venv/bin/activate
python -m pip install --upgrade pip

echo "[3/4] Installing Python dependencies"
pip install \
sounddevice \
vosk \
PySide6 \
playsound \
pynput

MODEL_DIR="vosk-model-small-en-in-0.4"
MODEL_ZIP="${MODEL_DIR}.zip"
MODEL_URL="https://alphacephei.com/vosk/models/${MODEL_ZIP}"

echo "[4/4] Ensuring Vosk model '${MODEL_DIR}' is present"
if [ ! -d "${MODEL_DIR}" ]; then
    echo "Downloading ${MODEL_ZIP} ..."
    curl -L -o "${MODEL_ZIP}" "${MODEL_URL}"
    echo "Unzipping ${MODEL_ZIP} ..."
    unzip -q "${MODEL_ZIP}"
    rm -f "${MODEL_ZIP}"
else
    echo "Model directory '${MODEL_DIR}' already exists; skipping download."
fi

echo "Setup complete. To run the app:"
echo "  source venv/bin/activate && python main.py"


