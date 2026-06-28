# Grafana Network Observability Platform

A reproducible observability platform for low-latency network and host telemetry. The project demonstrates how Grafana and Prometheus can be used to monitor Linux hosts, traffic flows, packet-performance signals, clock-synchronization health, and hardware-style network telemetry through real exporters and replay-driven data sources.

The platform is designed as a showcase and reference implementation for network observability workflows. It separates live host/flow measurements from simulated or replayed hardware telemetry so the same dashboard model can support real devices later.

---

## What This Project Does

This project provides a dashboard-driven observability environment for:

- Linux host health
- network interface counters
- TCP/UDP traffic tests
- throughput, latency, jitter, and packet loss
- sequence-gap and packet-flow indicators
- clock synchronization and PTP-style telemetry
- switch-style queue and buffer telemetry
- FPGA/NIC-style packet pipeline telemetry
- incident replay and controlled telemetry spikes
- dashboard provisioning and reproducible deployment

The project is intentionally modular. Real telemetry sources can be used where available, while replayed or simulated telemetry can be used to demonstrate hardware-oriented panels without requiring specialized switches, FPGA NICs, or PTP-capable hardware.

---

## Reference Architecture

```text
                         Public User
                             |
                             v
                  Reverse Proxy / HTTPS Endpoint
                             |
                             v
                    Grafana Observability UI
                             |
                             v
                         Prometheus
                             |
        ------------------------------------------------
        |                      |                       |
        v                      v                       v
  Linux Host Metrics     Traffic Metrics       Hardware-Style Metrics
  node_exporter          traffic_exporter      demo_hardware_exporter
```

A typical lab deployment uses:

```text
observability-node
  Grafana
  Prometheus
  dashboard provisioning
  Prometheus configuration
  demo hardware telemetry exporter

traffic-node-a
  node_exporter
  traffic exporter
  traffic generator

traffic-node-b
  node_exporter
  traffic exporter
  traffic receiver
```

The traffic nodes are used to create measurable network flows, while the observability node collects, stores, and visualizes metrics.

---

## Technology Stack

| Layer | Technology | Function |
|---|---|---|
| Visualization | Grafana | Dashboards for host health, flow metrics, packet behavior, clock health, and replay events |
| Metrics database | Prometheus | Time-series collection, scraping, querying, and short-term metric retention |
| Host metrics | node_exporter | Linux CPU, memory, disk, load, filesystem, and network interface counters |
| Traffic measurements | iperf3 | TCP/UDP throughput tests, UDP jitter, and packet loss measurement |
| Custom telemetry | Python exporters | Prometheus-compatible exporters for traffic, replay, PTP-style, switch-style, and FPGA/NIC-style metrics |
| Clock health | chrony / parsed clock metrics | Clock sync offset and frequency/skew visibility where available |
| Reverse proxy | Nginx | Public HTTPS access to Grafana without exposing Grafana directly |
| Deployment | Docker Compose | Local and server runtime for Grafana, Prometheus, and exporters |
| Automation | Ansible / shell scripts | Repeatable host setup and node bootstrap |
| CI/CD | GitHub Actions | Test, lint, validate Prometheus config, validate dashboard JSON, and package deployment artifacts |

---

## Telemetry Sources

### Real Telemetry

The platform can collect real metrics from Linux hosts and traffic flows:

| Metric Area | Examples |
|---|---|
| Host health | CPU usage, memory usage, disk usage, load average |
| Network interfaces | RX/TX bytes, RX/TX packets, drops, errors |
| Traffic flow | TCP throughput, UDP throughput, UDP jitter, UDP packet loss |
| Latency | RTT latency from active probes |
| Service health | Prometheus target state, exporter uptime, Grafana availability |
| Clock sync | chrony tracking offset, skew, and frequency where configured |

### Replayed or Simulated Telemetry

The platform also includes replay-driven hardware-style telemetry:

| Metric Area | Examples |
|---|---|
| PTP / PHC | offset, path delay, sync state, frequency adjustment |
| Packet behavior | sequence gaps, packet drops, jitter bursts, microburst indicators |
| Switch telemetry | queue drops, buffer utilization, interface counters, error counters |
| FPGA / NIC telemetry | pipeline latency, packet arrival rate, DMA queue depth, packet drops |
| Incident replay | controlled spikes for jitter, packet loss, clock offset, and queue drops |

These simulated data sources are explicitly labeled in metrics and dashboards so readers can distinguish live measurements from replayed hardware-style signals.

---

## Dashboard Model

The dashboard design is based on consistent labels:

```text
device
device_type
role
flow
src_device
dst_device
interface
source
job
instance
```

Example labels:

```text
device="traffic-node-a"
role="sender"
device_type="linux_host"

device="traffic-node-b"
role="receiver"
device_type="linux_host"

flow="traffic-node-a-to-traffic-node-b"
src_device="traffic-node-a"
dst_device="traffic-node-b"

device="demo-switch-1"
device_type="switch"
source="simulated"

device="demo-ptp-clock"
device_type="ptp_clock"
source="simulated"
```

This label model allows the same dashboards to support small demo deployments, larger Linux fleets, packet capture hosts, switches, PTP clocks, and future hardware telemetry integrations.

---

## Planned Dashboards

| Dashboard | Purpose |
|---|---|
| Platform Overview | Grafana, Prometheus, exporter health, scrape status, and observability-node health |
| Host Fleet Overview | CPU, memory, disk, load, network counters, drops, and errors by device |
| Two-Node Traffic Lab | Sender/receiver traffic flow, throughput, RTT, UDP jitter, UDP loss, and NIC counters |
| Packet Latency and Jitter | Packet-flow indicators, latency distribution, jitter, loss, sequence gaps, and bursts |
| PTP Clock Health | Clock offset, sync state, path delay, frequency adjustment, and clock health indicators |
| Switch and FPGA Telemetry | Queue drops, buffer utilization, interface counters, FPGA/NIC pipeline metrics |
| Incident Replay | Controlled replay scenarios for packet loss, jitter spikes, PTP offset spikes, and queue drops |

---

## Repository Layout

```text
.
├── README.md
├── Makefile
├── .env.example
├── deploy/
│   ├── ansible/
│   └── nginx/
├── docs/
│   └── screenshots/
├── exporters/
│   ├── traffic_exporter/
│   └── demo_hardware_exporter/
├── infra/
│   └── ec2-notes/
├── node-setup/
├── obs-stack/
│   ├── docker-compose.yml
│   ├── prometheus/
│   └── grafana/
│       ├── provisioning/
│       │   ├── dashboards/
│       │   └── datasources/
│       └── dashboards/
├── scripts/
├── tests/
└── .github/
    └── workflows/
```

---

## Component Responsibilities

### `obs-stack/`

Contains the runtime observability stack:

- Grafana service definition
- Prometheus service definition
- Prometheus scrape configuration
- Grafana datasource provisioning
- Grafana dashboard provisioning
- exporter service definitions used by the observability node

### `exporters/traffic_exporter/`

Exposes traffic-flow metrics in Prometheus format.

Primary responsibilities:

- run or parse active traffic tests
- expose RTT latency
- expose TCP throughput
- expose UDP throughput
- expose UDP jitter
- expose UDP loss percentage
- expose sequence-gap style counters when using generated traffic payloads

### `exporters/demo_hardware_exporter/`

Exposes hardware-style and replay-driven metrics in Prometheus format.

Primary responsibilities:

- emit PTP-style offset and sync metrics
- emit switch-style queue and buffer metrics
- emit FPGA/NIC-style pipeline metrics
- replay controlled incident scenarios
- label all replayed data clearly as simulated

### `node-setup/`

Contains setup scripts for traffic nodes.

Primary responsibilities:

- install node_exporter
- install iperf3
- install chrony
- configure traffic sender or receiver services
- configure exporter services

### `deploy/nginx/`

Contains reverse proxy examples for publishing Grafana through HTTPS.

Primary responsibilities:

- route public Grafana traffic through Nginx
- keep Grafana behind the reverse proxy
- document required headers for Grafana WebSocket support

### `.github/workflows/`

Contains CI/CD workflows.

Primary responsibilities:

- run Python tests
- validate Docker Compose configuration
- validate Prometheus configuration
- validate Grafana dashboard JSON
- validate shell scripts
- optionally run manual deployment workflows

---

## Runtime Commands

The project targets these commands:

```bash
make up
make down
make validate
make test
make demo
```

Expected behavior:

| Command | Function |
|---|---|
| `make up` | Start the observability stack |
| `make down` | Stop the observability stack |
| `make validate` | Validate configuration files |
| `make test` | Run exporter and parser tests |
| `make demo` | Start or trigger replay-driven demo telemetry |

---

## Deployment Model

The project uses a single repository and separate runtime roles.

```text
single Git repository
  |
  |-- observability node deployment
  |-- traffic node setup scripts
  |-- exporter source code
  |-- dashboard definitions
  |-- CI/CD validation
```

Each host does not need its own repository. The repository contains all application code, configuration, scripts, dashboards, and deployment logic.

Recommended workflow:

```text
push / pull request
  -> run CI validation
  -> test exporters
  -> validate Prometheus config
  -> validate Grafana dashboards

manual deployment
  -> update observability node
  -> restart services
  -> verify Prometheus targets
  -> verify Grafana dashboards
```

Manual deployment is preferred for the showcase environment so a bad commit does not automatically break the public dashboard.

---

## Real vs Hardware-Ready Scope

This project distinguishes between:

```text
real telemetry
  Linux host metrics
  network interface counters
  traffic throughput
  UDP jitter/loss
  RTT latency
  Prometheus target health

hardware-ready telemetry
  PTP/PHC state
  switch queue and buffer counters
  FPGA/NIC packet pipeline counters
  nanosecond packet timestamp metrics
```

Hardware-ready telemetry is represented through replayed or simulated exporters unless real hardware or supported cloud features are connected.

This keeps the project reproducible while preserving the same metric names, labels, and dashboards that real integrations would use.

---

## Extension Points

The project can be extended with:

- ClickHouse for raw packet-event history
- OpenTelemetry Collector for metric/log/trace routing
- Loki or ELK/OpenSearch for log search
- AWS VPC Traffic Mirroring for packet-capture workflows
- gNMI or sFlow collectors for real switch telemetry
- linuxptp exporters for real PTP/PHC environments
- eBPF or AF_XDP exporters for deeper Linux packet-path metrics
- containerlab and FRRouting for topology simulation
- Ansible/AWX for fleet deployment

These extensions are intentionally separate from the base stack so the core platform remains easy to run.

---

## Project Status

This repository is under active development.

Initial implementation goals:

- repository structure
- lightweight Grafana/Prometheus stack
- node setup scripts
- traffic exporter
- demo hardware exporter
- dashboard provisioning
- validation scripts
- CI workflows
- public dashboard documentation
