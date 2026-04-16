#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

docker compose up -d --build
echo "Waiting for services..."
sleep 5
echo "Pulling Ollama models..."
docker compose exec -T ollama ollama pull qwen2.5:7b || true
docker compose exec -T ollama ollama pull qwen2.5:14b || true
docker compose exec -T ollama ollama pull nomic-embed-text || true
echo "Done. Services running:"
docker compose ps
