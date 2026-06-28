#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Validating Python syntax"

python -m py_compile \
  scripts/render_prometheus_config.py \
  exporters/traffic_exporter/main.py \
  exporters/traffic_exporter/iperf.py \
  exporters/traffic_exporter/ping.py \
  exporters/hardware_telemetry_replay/main.py \
  exporters/hardware_telemetry_replay/scenarios.py

echo "==> Running tests"

python -m pytest -q

echo "==> Rendering Prometheus config"

python scripts/render_prometheus_config.py

echo "==> Validating Grafana dashboard JSON"

for dashboard in obs-stack/grafana/dashboards/*.json; do
  python -m json.tool "$dashboard" >/dev/null
  echo "valid json: $dashboard"
done

echo "==> Checking Docker Compose config"

if command -v docker >/dev/null 2>&1; then
  if [ -f ".env" ]; then
    docker compose --env-file .env -f obs-stack/docker-compose.yml config >/dev/null
    echo "docker compose config ok"
  else
    echo "warning: .env missing, skipping docker compose config validation"
  fi
else
  echo "warning: docker not found, skipping docker compose config validation"
fi

echo "==> Stack validation complete"