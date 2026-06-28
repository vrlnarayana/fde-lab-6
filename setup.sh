#!/usr/bin/env bash
# Azure Labs 6-A/6-B — one-shot setup. Prefers uv; falls back to python3.12 venv.
set -euo pipefail
cd "$(dirname "$0")"

# Install dev tooling plus the real-provider SDKs (openai + azure-identity).
# The Azure/OpenAI providers import these lazily; without the extras, pointing
# DEFAULT_PROVIDER at a live provider raises ModuleNotFoundError at request time.
if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -e ".[dev,azure,openai]"
else
  python3.12 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -e ".[dev,azure,openai]"
fi

echo "Running tests..."
./.venv/bin/python -m pytest -q || test $? -eq 5
echo "Setup complete. Run ./run.sh to launch the API + Streamlit UI."
