# replace Makefile

.PHONY: help render-config up down restart logs validate test demo

help:
	@echo "Grafana Network Observability Platform"
	@echo ""
	@echo "Available targets:"
	@echo "  make render-config  Render generated configs"
	@echo "  make up             Start observability stack"
	@echo "  make down           Stop observability stack"
	@echo "  make restart        Restart observability stack"
	@echo "  make logs           Tail stack logs"
	@echo "  make validate       Validate configs"
	@echo "  make test           Run tests"
	@echo "  make demo           Trigger demo telemetry"

render-config:
	python3 scripts/render_prometheus_config.py

up: render-config
	cd obs-stack && docker compose --env-file ../.env up -d

down:
	cd obs-stack && docker compose --env-file ../.env down

restart: render-config
	cd obs-stack && docker compose --env-file ../.env restart

logs:
	cd obs-stack && docker compose --env-file ../.env logs -f

validate: render-config
	cd obs-stack && docker compose --env-file ../.env config >/dev/null
	@echo "docker compose config OK"

test:
	python3 -m pytest -q

demo:
	@echo "TODO: trigger demo telemetry"