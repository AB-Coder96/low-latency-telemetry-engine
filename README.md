# Low-Latency Telemetry Engine

A reproducible Grafana/Prometheus observability lab for low-latency network telemetry across EC2 Linux nodes.

The platform tracks real TCP/UDP throughput, RTT latency, UDP jitter/loss, Linux host metrics, and replayed hardware-style telemetry for PTP, switch, and FPGA/NIC behavior. It is designed to look and operate like a realistic low-latency observability environment, not a toy dashboard.

[Live Grafana Demo](https://obs.zetaslate.com)

![Low-Latency Telemetry Engine dashboard preview](docs/screenshots/thumbnail.png)

---

## Dashboards

---

### Platform Overview

Prometheus scrape health, target status, exporter health, replay state, and traffic test success.

[Open Platform Overview](https://obs.zetaslate.com/d/platform-overview/platform-overview?orgId=1&from=now-30m&to=now&timezone=browser&refresh=10s)

![Platform Overview](docs/screenshots/platform-overview.png)

### Two-Node Traffic Lab

Real TX → RX TCP throughput, UDP throughput, UDP jitter, UDP loss, RTT, and ping loss.

[Open Two-Node Traffic Lab](https://obs.zetaslate.com/d/two-node-traffic-lab/two-node-traffic-lab?orgId=1&from=now-30m&to=now&timezone=browser&refresh=10s)

![Two-Node Traffic Lab](docs/screenshots/two-node-traffic-lab.png)

### PTP / Switch / FPGA Telemetry

Replayed hardware-style telemetry for PTP offset, switch buffer utilization, queue drops, sequence gaps, packet counters, microbursts, and FPGA/NIC latency.

[Open PTP / Switch / FPGA Telemetry](https://obs.zetaslate.com/d/hardware-telemetry/ptp-switch-fpga-telemetry?orgId=1&from=now-30m&to=now&timezone=browser&refresh=10s)

![PTP / Switch / FPGA Telemetry](docs/screenshots/hardware-telemetry.png)

### Incident Replay

Simulated incident timeline showing how PTP offset, microbursts, drops, sequence gaps, and FPGA/NIC latency move together.

[Open Incident Replay](https://obs.zetaslate.com/d/incident-replay/incident-replay?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s)

![Incident Replay](docs/screenshots/incident-replay.png)

---

## What This Project Demonstrates

This project demonstrates a practical observability workflow for low-latency systems:

- Real EC2-to-EC2 TCP throughput testing with `iperf3`
- Real EC2-to-EC2 UDP throughput testing with `iperf3`
- UDP jitter and packet-loss measurement
- RTT latency and ICMP packet-loss measurement
- Linux host metrics through `node_exporter`
- Custom Python Prometheus exporters
- Replayed hardware-style telemetry for PTP, switch, and FPGA/NIC behavior
- Grafana dashboards provisioned as code
- Prometheus scrape configuration generated from environment variables
- Public HTTPS Grafana access through an Nginx reverse proxy

---

## Architecture

```text
Browser
  → https://obs.zetaslate.com
  → Nginx reverse proxy
  → Grafana on ec2-obs
  → Prometheus
  → EC2 traffic nodes and telemetry exporters
```

Traffic flow:

```text
ec2-a-tx
  → TCP/UDP iperf3 traffic
  → ec2-b-rx
```

Prometheus scrape flow:

```text
Prometheus on ec2-obs
  → ec2-a-tx:9100 node_exporter
  → ec2-b-rx:9100 node_exporter
  → ec2-a-tx:9201 traffic_exporter
  → ec2-b-rx:9201 traffic_exporter
  → hardware-telemetry-replay:9202
```

---

## EC2 Nodes

| Node | Role | Main services |
|---|---|---|
| `ec2-obs` | Observability node | Prometheus, Grafana, hardware telemetry replay exporter |
| `ec2-a-tx` | Traffic sender | `node_exporter`, custom traffic exporter, `iperf3` client tests |
| `ec2-b-rx` | Traffic receiver | `node_exporter`, custom traffic exporter, `iperf3` server |
| `main-nginx` | Public reverse proxy | Dockerized Nginx, Certbot TLS, private proxy to Grafana, Postgres and Django for zetaslate.com

---

## Metrics Collected

| Metric | Meaning |
|---|---|
| `traffic_exporter_up` | Custom traffic exporter health |
| `flow_test_success` | Success status for ping, TCP, and UDP tests |
| `flow_tcp_throughput_mbps` | TCP throughput from TX to RX |
| `flow_udp_throughput_mbps` | UDP throughput from TX to RX |
| `flow_udp_jitter_ms` | UDP jitter from the iperf3 UDP test |
| `flow_udp_loss_percent` | UDP packet loss percentage |
| `flow_rtt_ms` | ICMP round-trip latency |
| `flow_ping_packet_loss_percent` | ICMP packet loss percentage |
| `ptp_offset_ns` | Replayed PTP clock offset |
| `switch_queue_drops_total` | Replayed switch queue drops |
| `packet_microburst_active` | Replayed microburst state |
| `fpga_pipeline_latency_ns` | Replayed FPGA/NIC pipeline latency |

---

## Dashboards

### Platform Overview

The Platform Overview dashboard shows whether the observability platform is healthy. It tracks Prometheus target health, exporter status, and traffic test success.

### Two-Node Traffic Lab

The Two-Node Traffic Lab dashboard shows live TX → RX network behavior, including TCP throughput, UDP throughput, UDP jitter, UDP loss, RTT latency, and ping loss.

### PTP / Switch / FPGA Telemetry

The hardware telemetry dashboard replays hardware-style metrics that are commonly important in low-latency systems, including PTP offset, switch microbursts, queue drops, and FPGA/NIC pipeline latency.

### Incident Replay

The Incident Replay dashboard shows a simulated incident timeline where latency, PTP offset, switch drops, microbursts, and FPGA/NIC pipeline latency move together.

---

## Deployment Summary

The MVP runs across EC2 Linux nodes:

1. `ec2-obs` runs Prometheus, Grafana, and the hardware telemetry replay exporter.
2. `ec2-a-tx` runs `node_exporter` and the custom traffic exporter.
3. `ec2-b-rx` runs `node_exporter`, the custom traffic exporter, and an `iperf3` server.
4. Prometheus scrapes all exporters.
5. Grafana visualizes platform health, traffic metrics, and replayed hardware telemetry.
6. At `main-nginx` Nginx exposes Grafana publicly over HTTPS at `https://obs.zetaslate.com`.

---
