# Makefile

.PHONY: help up down restart logs validate test demo

help:
	@echo "Grafana Network Observability Platform"
	@echo ""
	@echo "Available targets:"
	@echo "  make up        Start observability stack"
	@echo "  make down      Stop observability stack"
	@echo "  make restart   Restart observability stack"
	@echo "  make logs      Tail stack logs"
	@echo "  make validate  Validate Docker Compose config"
	@echo "  make test      Run tests"
	@echo "  make demo      Trigger demo telemetry"

up:
	cd obs-stack && docker compose --env-file ../.env up -d

down:
	cd obs-stack && docker compose --env-file ../.env down

restart:
	cd obs-stack && docker compose --env-file ../.env restart

logs:
	cd obs-stack && docker compose --env-file ../.env logs -f

validate:
	cd obs-stack && docker compose --env-file ../.env config >/dev/null
	@echo "docker compose config OK"

test:
	@echo "TODO: run tests"

demo:
	@echo "TODO: trigger demo telemetry"