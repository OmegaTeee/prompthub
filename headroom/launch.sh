#!/bin/sh

SCRIPT_DIR="$(CDPATH=cd -- "$(dirname -- "$0")" && pwd)"
. "${SCRIPT_DIR}/.venv/bin/activate"

# Where Headroom stores state
export HEADROOM_HOME="${SCRIPT_DIR}"

# Headroom proxy listener
export HEADROOM_HOST="127.0.0.1"
export HEADROOM_PORT="8787"
export HEADROOM_PROXY_URL="http://${HEADROOM_HOST}:${HEADROOM_PORT}"

# Headroom behavior
export HEADROOM_BUDGET="100.0"
export HEADROOM_MODE="${HEADROOM_MODE:-token}"
export HEADROOM_OUTPUT_SHAPER="1"
export HEADROOM_CODE_AWARE_ENABLED="1"
export HEADROOM_VERBOSITY_LEVEL="2"
export HEADROOM_TELEMETRY="${HEADROOM_TELEMETRY:-off}"

# Upstream LLM: LM Studio OpenAI-compatible server
export HEADROOM_BACKEND="openai"
export HEADROOM_OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1"
export HEADROOM_OPENAI_API_KEY="${PH_API_TOKEN:-lm-studio}"

# For your current Headroom build:
export OPENAI_TARGET_API_URL="http://127.0.0.1:1234/v1"
export OPENAI_BASE_URL="${HEADROOM_PROXY_URL}/v1"
export ANTHROPIC_BASE_URL="${HEADROOM_PROXY_URL}/v1"

# Run proxy
exec headroom proxy --port "${HEADROOM_PORT}" --budget "${HEADROOM_BUDGET}"
