# Grafana Network Observability Platform

A reproducible Grafana + Prometheus observability platform for Linux host telemetry, traffic-flow measurements, packet-performance indicators, clock-synchronization health, and hardware-style network telemetry.

The project is built as a showcase and reference implementation for low-latency network observability workflows. It combines real Linux and traffic metrics with replay-driven hardware-style telemetry so the same dashboard model can support small cloud labs, larger Linux fleets, packet-capture nodes, switches, PTP clocks, and FPGA/NIC telemetry sources.

---

## Project Summary

This platform demonstrates:

- Linux host monitoring across multiple nodes
- network interface byte, packet, error, and drop counters
- TCP/UDP traffic generation and measurement
- throughput, RTT latency, UDP jitter, and UDP loss dashboards
- packet-flow indicators such as sequence gaps and burst events
- clock synchronization and PTP-style health panels
- switch-style queue, buffer, and interface telemetry panels
- FPGA/NIC-style packet pipeline telemetry panels
- incident replay through controlled metric spikes
- Grafana dashboard provisioning
- Prometheus scrape configuration
- Docker Compose runtime for the observability stack
- CI validation for exporters, configuration, and dashboards

---

## Current Showcase Hardware and Network Layout

The current reference deployment uses one existing public web node, one observability node, and two traffic nodes.

| Host | Instance Type | OS | Network Role | Project Role | Main Services |
|---|---:|---|---|---|---|
| `ec2-web-proxy` | existing `t4g.nano` | existing Linux install | Public internet entry point | Reverse proxy for public Grafana access | Nginx, existing Django app, existing Postgres |
| `ec2-obs` | `t4g.small` | Ubuntu Server 24.04 LTS ARM64 | Observability node | Metrics collection and visualization | Docker, Docker Compose, Grafana, Prometheus, demo hardware exporter |
| `ec2-a-tx` | `t4g.nano` | Ubuntu Server 24.04 LTS ARM64 | Traffic node A | Sender and monitored Linux host | node_exporter, iperf3 client, traffic exporter, chrony |
| `ec2-b-rx` | `t4g.nano` | Ubuntu Server 24.04 LTS ARM64 | Traffic node B | Receiver and monitored Linux host | node_exporter, iperf3 server, traffic exporter, chrony |

Public access is provided through the existing Nginx node:

```text
Internet
  ↓
grafana.example.com
  ↓
ec2-web-proxy / Nginx / HTTPS
  ↓
ec2-obs:3000
  ↓
Grafana
```

Traffic measurements are generated between the two traffic nodes:

```text
ec2-a-tx  ───── TCP/UDP traffic tests ─────>  ec2-b-rx
```

Prometheus scrapes the observability and traffic-node exporters:

```text
ec2-obs / Prometheus
  ├── ec2-a-tx:9100     node_exporter
  ├── ec2-b-rx:9100     node_exporter
  ├── ec2-a-tx:9201     traffic_exporter
  ├── ec2-b-rx:9201     traffic_exporter
  └── demo_hardware_exporter:9202
```

---

## Real and Replayed Telemetry

The project separates real telemetry from replayed hardware-style telemetry.

### Real Telemetry

| Area | Source | Example Metrics |
|---|---|---|
| Host health | `node_exporter` | CPU, memory, disk, load average |
| Network interfaces | Linux kernel counters through `node_exporter` | RX/TX bytes, RX/TX packets, drops, errors |
| TCP/UDP traffic | `iperf3` and `traffic_exporter` | TCP throughput, UDP throughput, UDP jitter, UDP loss |
| Latency | active probes from traffic nodes | RTT latency, service probe latency |
| Clock sync | `chrony` parsed metrics | clock offset, frequency, skew |
| Service health | Prometheus and exporters | target up/down, scrape duration, exporter uptime |

### Replayed or Simulated Telemetry

| Area | Source | Example Metrics |
|---|---|---|
| PTP / PHC | `demo_hardware_exporter` | offset, path delay, sync state, frequency adjustment |
| Packet behavior | replay scenarios | sequence gaps, drops, jitter bursts, microburst indicators |
| Switch telemetry | replay scenarios | queue drops, buffer utilization, interface counters |
| FPGA / NIC telemetry | replay scenarios | pipeline latency, packet arrival rate, DMA queue depth |
| Incidents | replay mode | clock spike, jitter burst, loss burst, queue-drop burst |

Replayed metrics are labeled with `source="simulated"` so dashboards can distinguish demo hardware telemetry from live measurements.

---

## Technology Stack

| Layer | Technology | Function |
|---|---|---|
| Visualization | Grafana | Dashboards for host, flow, packet, clock, switch, FPGA/NIC, and incident views |
| Metrics database | Prometheus | Scraping, querying, alert-style evaluation, and short-retention time-series storage |
| Host metrics | node_exporter | Linux CPU, memory, disk, load, filesystem, and network interface counters |
| Traffic generation | iperf3 | TCP throughput, UDP throughput, UDP jitter, and UDP loss measurements |
| Traffic exporter | Python | Converts traffic tests and probes into Prometheus metrics |
| Hardware-style exporter | Python | Emits replayed PTP, switch, FPGA/NIC, and incident metrics |
| Clock sync | chrony | Clock tracking and synchronization metrics where available |
| Runtime | Docker Compose | Starts Grafana, Prometheus, and observability-node exporters |
| Reverse proxy | Nginx | Public HTTPS access to Grafana without exposing Grafana directly |
| Automation | shell scripts / Ansible | Repeatable node setup and service installation |
| CI/CD | GitHub Actions | Tests, linting, config validation, dashboard JSON validation, and manual deployment hooks |

---

## Metric Label Model

Dashboards use consistent labels so the same panels can work across demo nodes and future hardware integrations.

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

Examples:

```text
device="ec2-a-tx"
role="sender"
device_type="linux_host"

device="ec2-b-rx"
role="receiver"
device_type="linux_host"

flow="ec2-a-tx-to-ec2-b-rx"
src_device="ec2-a-tx"
dst_device="ec2-b-rx"

device="demo-switch-1"
device_type="switch"
source="simulated"

device="demo-ptp-clock"
device_type="ptp_clock"
source="simulated"

device="demo-fpga-nic"
device_type="fpga_nic"
source="simulated"
```

---

## Planned Dashboards

| Dashboard | Purpose |
|---|---|
| Platform Overview | Grafana, Prometheus, exporter health, scrape status, and observability-node status |
| Host Fleet Overview | CPU, memory, disk, load, network counters, errors, and drops by device |
| Two-Node Traffic Lab | Sender/receiver traffic flow, throughput, RTT, UDP jitter, UDP loss, and NIC counters |
| Packet Latency and Jitter | Packet-flow indicators, latency, jitter, loss, sequence gaps, and burst events |
| PTP Clock Health | Clock offset, sync state, path delay, frequency adjustment, and PTP-style health |
| Switch and FPGA Telemetry | Queue drops, buffer utilization, switch counters, and FPGA/NIC pipeline metrics |
| Incident Replay | Replay scenarios for packet loss, jitter spikes, PTP offset spikes, and queue drops |

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
- observability-node exporter services

### `exporters/traffic_exporter/`

Exposes traffic-flow metrics in Prometheus format.

Primary responsibilities:

- run or parse traffic tests
- expose RTT latency
- expose TCP throughput
- expose UDP throughput
- expose UDP jitter
- expose UDP loss percentage
- expose sequence-gap style counters when generated payloads are used

### `exporters/demo_hardware_exporter/`

Exposes hardware-style and replay-driven metrics in Prometheus format.

Primary responsibilities:

- emit PTP-style offset and sync metrics
- emit switch-style queue and buffer metrics
- emit FPGA/NIC-style pipeline metrics
- replay controlled incident scenarios
- label replayed data as simulated

### `node-setup/`

Contains setup scripts for traffic nodes.

Primary responsibilities:

- install node_exporter
- install iperf3
- install chrony
- configure traffic sender and receiver services
- configure exporter services

### `deploy/nginx/`

Contains reverse proxy examples for publishing Grafana through HTTPS.

Primary responsibilities:

- route public Grafana traffic through Nginx
- keep Grafana behind the reverse proxy
- include headers needed for Grafana and WebSocket support

### `.github/workflows/`

Contains CI/CD workflows.

Primary responsibilities:

- run Python tests
- validate Docker Compose configuration
- validate Prometheus configuration
- validate Grafana dashboard JSON
- validate shell scripts
- provide manual deployment workflows

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

| Command | Function |
|---|---|
| `make up` | Start the observability stack |
| `make down` | Stop the observability stack |
| `make validate` | Validate configuration files |
| `make test` | Run exporter and parser tests |
| `make demo` | Start or trigger replay-driven demo telemetry |

---

## Deployment Model

This project uses a single repository and separate runtime roles.

```text
single Git repository
  ├── observability-node deployment
  ├── traffic-node setup scripts
  ├── exporter source code
  ├── dashboard definitions
  └── CI/CD validation
```

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

## Operating System Choice

The current reference deployment uses **Ubuntu Server 24.04 LTS ARM64** for the new project nodes.

Ubuntu is used for the MVP because the setup is simple and consistent across the observability and traffic nodes:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin prometheus-node-exporter iperf3 chrony python3 python3-venv
```

Amazon Linux 2023 is also a good option for AWS-native experiments, especially when testing newer ENA, PHC, or EC2-specific networking features. For this showcase project, Ubuntu keeps package names, installation scripts, and CI assumptions straightforward.

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

These extensions are separate from the base stack so the core platform remains easy to run.

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
