# MVP EC2 Plan — Grafana Low-Latency Observability Lab

This README describes the minimum viable deployment for the first resume project:

**Grafana Observability Platform for packet latency/jitter, host metrics, traffic replay, PTP-style clock health, and simulated switch/FPGA telemetry.**

The goal is to prove the architecture with low cost and low effort, not to build a production observability system.

---

## 1. MVP Claim

This MVP monitors:

- two real Linux EC2 nodes
- real TCP/UDP traffic between them
- real throughput, RTT latency, UDP jitter, and UDP loss
- real Linux host metrics from all lab nodes
- real NIC byte/packet/drop/error counters exposed by Linux
- real Prometheus scrape health
- simulated PTP/PHC, switch, and FPGA/NIC telemetry for hardware-ready dashboard panels
- incident replay through synthetic metric spikes

This MVP does **not** claim real hardware PTP packet timestamping, real Arista switch telemetry, ClickHouse packet forensics, or ELK log search.

Those are optional future extensions.

---

## 2. Host Layout

| Host | Instance Type | Public IP? | Role | Installed Components |
|---|---:|---:|---|---|
| `ec2-web-proxy` | Existing `t4g.nano` | Yes | Existing public web server and Nginx reverse proxy | Existing Django, Postgres, Nginx. Add one Grafana reverse-proxy config only. |
| `ec2-obs` | `t4g.small` | Yes for easiest setup | Observability server | Docker, Docker Compose, Grafana, Prometheus, demo exporters, optional node_exporter |
| `ec2-a-tx` | `t4g.nano` | Yes for easiest setup | Traffic sender | node_exporter, iperf3 client, traffic_exporter, chrony |
| `ec2-b-rx` | `t4g.nano` | Yes for easiest setup | Traffic receiver | node_exporter, iperf3 server, traffic_exporter, chrony |

Recommended for a one-month proof:

```text
ec2-obs      = t4g.small
ec2-a-tx     = t4g.nano
ec2-b-rx     = t4g.nano
```

After screenshots, demo video, and documentation are done, stop or terminate `ec2-a-tx` and `ec2-b-rx` to reduce cost.

---

## 3. Why Public IPs Are Used in This MVP

The lowest-effort setup gives the three new EC2s public IPv4 addresses so they can:

- install packages with `apt`
- pull Docker images
- receive SSH from your trusted IP

Security groups still block direct public access to Grafana, Prometheus, node_exporter, and exporter ports.

Cheaper private-only nodes are possible, but then you need NAT Gateway, SSM/VPC endpoints, or extra bastion/proxy work. That adds effort and can cost more than the small test nodes.

---

## 4. Network Diagram

```text
Internet
  ↓
grafana.yourdomain.com
  ↓
existing ec2-web-proxy Nginx
  ↓ private VPC traffic
ec2-obs:3000
  ↓
Grafana
  ↓
Prometheus
  ↓
ec2-a-tx exporters
ec2-b-rx exporters
```

Traffic lab:

```text
ec2-a-tx  ───── TCP/UDP iperf3 traffic ─────>  ec2-b-rx

Prometheus scrapes:
  ec2-a-tx:9100
  ec2-b-rx:9100
  ec2-a-tx:9201
  ec2-b-rx:9201
```

---

## 5. What Is Real vs Simulated

### Real

| Data | Source |
|---|---|
| CPU, memory, disk, load | node_exporter |
| RX/TX bytes and packets | node_exporter Linux network counters |
| NIC drops and errors | node_exporter Linux network counters |
| TCP throughput | iperf3 |
| UDP throughput | iperf3 |
| UDP jitter | iperf3 UDP test |
| UDP packet loss | iperf3 UDP test |
| RTT latency | ping or custom traffic_exporter |
| Prometheus target health | Prometheus |
| Grafana availability | Grafana service |
| Clock sync offset | chrony tracking metrics or parsed `chronyc tracking` |

### Simulated / Replay

| Data | Reason |
|---|---|
| PTP nanosecond offset | Real hardware timestamping is not available on cheap T-family EC2s |
| PHC hardware state | Requires supported Nitro/ENA PHC instances |
| Switch queue drops | AWS VPC does not expose physical switch queue counters |
| sFlow/gNMI switch telemetry | Simulated exporter until real switch exists |
| FPGA/NIC pipeline latency | Simulated exporter until real FPGA/NIC exists |
| Microburst event labels | Simulated/replayed for dashboard proof |

---

## 6. Minimum Services

### On `ec2-obs`

Run with Docker Compose:

```text
grafana
prometheus
demo_hardware_exporter
```

Optional if memory is stable:

```text
node_exporter
cadvisor
```

Do not run in the MVP:

```text
ClickHouse
OpenSearch
Elasticsearch
Loki
containerlab
full packet capture
```

### On `ec2-a-tx`

Run directly on host:

```text
prometheus-node-exporter
iperf3 client job
traffic_exporter
chrony
```

### On `ec2-b-rx`

Run directly on host:

```text
prometheus-node-exporter
iperf3 server
traffic_exporter
chrony
```

Direct host installs are preferred on the nano instances because Docker can be heavy on 512 MiB RAM.

---

## 7. Security Groups

### `sg-web-proxy`

Attach to existing public Nginx EC2.

Inbound:

| Port | Source | Purpose |
|---:|---|---|
| `80/tcp` | `0.0.0.0/0` | HTTP |
| `443/tcp` | `0.0.0.0/0` | HTTPS |
| `22/tcp` | Your IP only | SSH |

Outbound:

| Port | Destination | Purpose |
|---:|---|---|
| `3000/tcp` | `ec2-obs` private IP | Reverse proxy to Grafana |

### `sg-obs`

Attach to `ec2-obs`.

Inbound:

| Port | Source | Purpose |
|---:|---|---|
| `22/tcp` | Your IP only | SSH |
| `3000/tcp` | `ec2-web-proxy` private IP or `sg-web-proxy` | Grafana through Nginx only |

Outbound:

| Port | Destination | Purpose |
|---:|---|---|
| `9100/tcp` | `ec2-a-tx`, `ec2-b-rx` | node_exporter scrape |
| `9201/tcp` | `ec2-a-tx`, `ec2-b-rx` | traffic_exporter scrape |
| `443/tcp` | `0.0.0.0/0` | package/image downloads |
| `80/tcp` | `0.0.0.0/0` | package downloads if needed |

Do not expose Prometheus publicly.

### `sg-lab-node`

Attach to `ec2-a-tx` and `ec2-b-rx`.

Inbound:

| Port | Source | Purpose |
|---:|---|---|
| `22/tcp` | Your IP only | SSH |
| `9100/tcp` | `ec2-obs` private IP or `sg-obs` | node_exporter |
| `9201/tcp` | `ec2-obs` private IP or `sg-obs` | traffic_exporter |
| `5201/tcp` | `ec2-a-tx` private IP or `sg-lab-node` | iperf3 TCP |
| `5201/udp` | `ec2-a-tx` private IP or `sg-lab-node` | iperf3 UDP |

Outbound:

| Port | Destination | Purpose |
|---:|---|---|
| `80/tcp` | `0.0.0.0/0` | package downloads |
| `443/tcp` | `0.0.0.0/0` | package downloads |
| `5201/tcp` | `ec2-b-rx` | iperf3 TCP test |
| `5201/udp` | `ec2-b-rx` | iperf3 UDP test |

---

## 8. EC2 Creation Instructions

Create all new EC2s in the same AWS Region, VPC, and preferably the same Availability Zone.

### 8.1 Create `ec2-obs`

Recommended settings:

```text
Name: ec2-obs
AMI: Ubuntu Server 24.04 LTS ARM64
Instance type: t4g.small
Storage: 12–16 GB gp3
Public IPv4: Enabled for easiest setup
Security group: sg-obs
```

After launch:

```bash
ssh ubuntu@EC2_OBS_PUBLIC_IP
```

Install base tools:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git curl htop
sudo usermod -aG docker ubuntu
```

Reconnect:

```bash
exit
ssh ubuntu@EC2_OBS_PUBLIC_IP
```

Verify:

```bash
docker version
docker compose version
```

---

### 8.2 Create `ec2-a-tx`

Recommended settings:

```text
Name: ec2-a-tx
AMI: Ubuntu Server 24.04 LTS ARM64
Instance type: t4g.nano
Storage: 8 GB gp3
Public IPv4: Enabled for easiest setup
Security group: sg-lab-node
```

Install base tools:

```bash
ssh ubuntu@EC2_A_PUBLIC_IP

sudo apt update
sudo apt install -y prometheus-node-exporter iperf3 chrony python3 python3-venv git curl htop
sudo systemctl enable --now prometheus-node-exporter
sudo systemctl enable --now chrony
```

Check node_exporter:

```bash
curl http://127.0.0.1:9100/metrics | head
```

---

### 8.3 Create `ec2-b-rx`

Recommended settings:

```text
Name: ec2-b-rx
AMI: Ubuntu Server 24.04 LTS ARM64
Instance type: t4g.nano
Storage: 8 GB gp3
Public IPv4: Enabled for easiest setup
Security group: sg-lab-node
```

Install base tools:

```bash
ssh ubuntu@EC2_B_PUBLIC_IP

sudo apt update
sudo apt install -y prometheus-node-exporter iperf3 chrony python3 python3-venv git curl htop
sudo systemctl enable --now prometheus-node-exporter
sudo systemctl enable --now chrony
```

Create an iperf3 server service:

```bash
sudo tee /etc/systemd/system/iperf3-server.service >/dev/null <<'EOF'
[Unit]
Description=iperf3 server for Grafana traffic lab
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/iperf3 -s -p 5201
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now iperf3-server
```

Check:

```bash
sudo systemctl status iperf3-server --no-pager
```

---

## 9. Prove Real Traffic

From `ec2-a-tx`, run TCP test:

```bash
iperf3 -c EC2_B_PRIVATE_IP -p 5201 -t 10
```

Run UDP jitter/loss test:

```bash
iperf3 -c EC2_B_PRIVATE_IP -p 5201 -u -b 1M -t 10
```

Run ping latency test:

```bash
ping -c 10 EC2_B_PRIVATE_IP
```

These are the real numbers your traffic exporter should later expose to Prometheus.

---

## 10. Prometheus Scrape Targets

Prometheus on `ec2-obs` should scrape:

```yaml
scrape_configs:
  - job_name: "node"
    static_configs:
      - targets:
          - "EC2_OBS_PRIVATE_IP:9100"
        labels:
          device: "ec2-obs"
          role: "observability"
          device_type: "linux_host"

      - targets:
          - "EC2_A_PRIVATE_IP:9100"
        labels:
          device: "ec2-a-tx"
          role: "sender"
          device_type: "linux_host"

      - targets:
          - "EC2_B_PRIVATE_IP:9100"
        labels:
          device: "ec2-b-rx"
          role: "receiver"
          device_type: "linux_host"

  - job_name: "traffic"
    static_configs:
      - targets:
          - "EC2_A_PRIVATE_IP:9201"
        labels:
          device: "ec2-a-tx"
          role: "sender"
          flow: "ec2-a-to-ec2-b"

      - targets:
          - "EC2_B_PRIVATE_IP:9201"
        labels:
          device: "ec2-b-rx"
          role: "receiver"
          flow: "ec2-a-to-ec2-b"

  - job_name: "demo-hardware"
    static_configs:
      - targets:
          - "demo_hardware_exporter:9202"
        labels:
          source: "simulated"
```

---

## 11. Dashboard Panels

Build these Grafana dashboards first.

### Platform Overview

- Prometheus targets up/down
- Grafana up
- exporter up
- OBS CPU/RAM/disk
- scrape duration and scrape failures

### Two-Node Traffic Lab

- `ec2-a-tx` CPU/RAM/network
- `ec2-b-rx` CPU/RAM/network
- TCP throughput
- UDP throughput
- UDP jitter
- UDP loss percentage
- RTT latency
- TX packets vs RX packets
- NIC drops/errors

### Packet Latency and Jitter

- `flow_rtt_ms`
- `flow_udp_jitter_ms`
- `flow_udp_loss_percent`
- `flow_throughput_mbps`
- `packet_sequence_gap_total`

### PTP Clock Health

Real:

- chrony offset
- chrony frequency/skew if exported

Simulated:

- `ptp_offset_ns`
- `ptp_path_delay_ns`
- `ptp_sync_state`

### Switch and FPGA Telemetry

Simulated:

- `switch_queue_drops_total`
- `switch_buffer_utilization_percent`
- `fpga_pipeline_latency_ns`
- `fpga_packet_rx_total`
- `fpga_packet_drop_total`

### Incident Replay

- jitter burst
- packet loss burst
- PTP offset spike
- queue drop burst
- FPGA pipeline delay spike

---

## 12. Nginx Reverse Proxy

On the existing public EC2:

```bash
sudo nano /etc/nginx/sites-available/grafana
```

Add:

```nginx
server {
    listen 80;
    server_name grafana.yourdomain.com;

    location / {
        proxy_pass http://EC2_OBS_PRIVATE_IP:3000;

        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/grafana /etc/nginx/sites-enabled/grafana
sudo nginx -t
sudo systemctl reload nginx
```

Point DNS:

```text
grafana.yourdomain.com → existing ec2-web-proxy public IP
```

Enable HTTPS:

```bash
sudo certbot --nginx -d grafana.yourdomain.com
```

Final URL:

```text
https://grafana.yourdomain.com
```

---

## 13. MVP Done Criteria

The MVP is done when you can show:

- Grafana public dashboard loads
- Prometheus scrapes OBS, TX, and RX nodes
- `ec2-a-tx` sends real traffic to `ec2-b-rx`
- dashboard shows real throughput
- dashboard shows real UDP jitter and loss
- dashboard shows real RTT latency
- dashboard shows Linux CPU/RAM/network for both nodes
- dashboard shows simulated PTP/switch/FPGA telemetry
- incident replay creates visible spikes
- README clearly says what is real and what is simulated

---

## 14. Resume-Safe Project Wording

Use wording like this after the MVP is built:

```text
Built a reproducible Grafana/Prometheus low-latency observability lab for two EC2 Linux nodes and replayed hardware telemetry. Implemented custom Python exporters for TCP/UDP throughput, RTT latency, UDP jitter/loss, sequence gaps, Linux NIC counters, simulated PTP/PHC health, switch queue drops, and FPGA/NIC pipeline metrics. Added incident replay, dashboard provisioning, Docker Compose, and GitHub Actions validation, with ClickHouse/OpenTelemetry/ELK documented as optional extension modules.
```

This wording is strong and honest.
