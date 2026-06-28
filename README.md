# README Host Layout

## Public Demo Infrastructure

This project uses one existing public EC2 instance as the reverse proxy and three private EC2 instances for the observability lab.

| Host | Public IP? | Minimum Size | Recommended Size | Main Role | Installed Services / Containers | Public Inbound | Private Inbound |
|---|---:|---:|---:|---|---|---|---|
| `ec2-web-proxy` | Yes | Existing `t4g.nano` | Keep existing | Public Nginx reverse proxy for Grafana subdomain; existing Django/Postgres host | Existing Nginx, Django backend, Postgres. Add only one Nginx reverse proxy server block for Grafana. | `80/tcp`, `443/tcp`, `22/tcp` from trusted IP only | Can connect to `ec2-obs:3000` |
| `ec2-obs` | No | `t4g.medium` | `t4g.large` | Central observability server | Docker, Docker Compose, Grafana, Prometheus, ClickHouse, OpenTelemetry Collector, node_exporter, cAdvisor, custom exporters | None | `3000/tcp` from `ec2-web-proxy`; `9090/tcp`, `8123/tcp`, exporter ports only inside VPC |
| `ec2-a-sender` | No | `t4g.micro` | `t4g.small` | Traffic sender and monitored Linux device | Docker, node_exporter, linux_perf_exporter, packet_exporter, iperf3 client, traffic generator | None | Exporter ports from `ec2-obs`; traffic test ports to/from `ec2-b-receiver` |
| `ec2-b-receiver` | No | `t4g.micro` | `t4g.small` | Traffic receiver and monitored Linux device | Docker, node_exporter, linux_perf_exporter, packet_exporter, iperf3 server, traffic receiver | None | Exporter ports from `ec2-obs`; iperf3/server test ports from `ec2-a-sender` |

## Network Flow

```text
Internet
  ↓
DNS: grafana.example.com
  ↓
ec2-web-proxy public IP
  ↓
Nginx reverse proxy
  ↓ private VPC traffic
ec2-obs:3000
  ↓
Grafana
```

Traffic lab:

```text
ec2-a-sender  ───── TCP/UDP test traffic ─────>  ec2-b-receiver
      ↑                                             ↑
      └──────────── Prometheus scrapes metrics ─────┘
```

## What Is Real in the Public Demo

Real telemetry:

- Host metrics from `ec2-obs`, `ec2-a-sender`, and `ec2-b-receiver`
- Real TCP/UDP traffic between `ec2-a-sender` and `ec2-b-receiver`
- Real Nginx reverse proxy traffic for the Grafana subdomain
- Real Docker/container health
- Real Prometheus scrape health
- Real ClickHouse service health

Synthetic or replayed telemetry:

- PTP clock offset events
- Switch queue/buffer telemetry
- FPGA/NIC pipeline telemetry
- Advanced packet arrival scenarios
- Incident replay events

## Security Model

Only `ec2-web-proxy` has a public IP address.

The observability and traffic EC2 instances are private-only. They should not expose Grafana, Prometheus, ClickHouse, or exporter ports directly to the internet.

Recommended public access:

```text
https://grafana.example.com
```

Recommended private access:

```text
ec2-web-proxy → ec2-obs:3000
ec2-obs → ec2-a-sender exporter ports
ec2-obs → ec2-b-receiver exporter ports
ec2-a-sender → ec2-b-receiver traffic test ports
```
