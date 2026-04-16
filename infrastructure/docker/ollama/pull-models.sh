#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

models=(
  "qwen2.5:7b"
  "qwen2.5:14b"
  "deepseek-r1:14b"
  "meditron:7b"
  "nomic-embed-text"
)

for model in "${models[@]}"; do
  docker compose exec -T ollama ollama pull "${model}" || true
done
