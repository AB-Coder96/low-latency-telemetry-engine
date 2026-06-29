# Low-Latency Telemetry Engine

A reproducible Grafana + Prometheus observability lab for low-latency network telemetry across two EC2 Linux nodes.

This project monitors real EC2 host metrics, TCP/UDP throughput, RTT latency, UDP jitter/loss, and replayed hardware-style telemetry for PTP offset, switch queue pressure, packet drops, microbursts, and FPGA/NIC pipeline behavior.

## Live Grafana Dashboards

Grafana is deployed behind an HTTPS Nginx reverse proxy:

```text
https://obs.zetaslate.com
```

Key dashboards:

- [PTP / Switch / FPGA Telemetry](https://obs.zetaslate.com/d/hardware-telemetry/ptp-switch-fpga-telemetry?orgId=1&from=now-30m&to=now&timezone=browser&refresh=10s)
- [Incident Replay](https://obs.zetaslate.com/d/incident-replay/incident-replay?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s)


---

## Architecture

The MVP uses four EC2 roles:

```text
main-nginx EC2
  Public HTTPS reverse proxy
  Routes obs.zetaslate.com to Grafana over the private VPC

ec2-obs
  Observability node
  Runs Grafana, Prometheus, and the hardware telemetry replay exporter

ec2-a-tx
  Traffic sender node
  Runs node_exporter and the custom traffic exporter
  Sends TCP/UDP iperf3 traffic to ec2-b-rx

ec2-b-rx
  Traffic receiver node
  Runs node_exporter, the custom traffic exporter, and iperf3 server
```

Prometheus scrape flow:

```text
Prometheus on ec2-obs
  -> ec2-a-tx:9100 node_exporter
  -> ec2-b-rx:9100 node_exporter
  -> ec2-a-tx:9201 traffic_exporter
  -> ec2-b-rx:9201 traffic_exporter
  -> hardware-telemetry-replay:9202
```

Traffic flow:

```text
ec2-a-tx -> TCP/UDP iperf3 tests -> ec2-b-rx
```

Public access flow:

```text
Browser
  -> https://obs.zetaslate.com
  -> Nginx reverse proxy
  -> Grafana on ec2-obs:3000
```

---

## What This Measures

### Live EC2 node metrics

Collected through Prometheus node_exporter:

```text
CPU usage
Memory usage
Disk usage
Network receive/transmit throughput
Node uptime
Host availability
```

### Live traffic metrics

Collected through the custom Python traffic exporter:

```text
traffic_exporter_up
flow_rtt_ms
flow_ping_packet_loss_percent
flow_tcp_throughput_mbps
flow_udp_throughput_mbps
flow_udp_jitter_ms
flow_udp_loss_percent
flow_test_success
traffic_exporter_last_update_timestamp_seconds
```

### Replayed hardware-style telemetry

Collected through the hardware telemetry replay exporter:

```text
ptp_offset_ns
ptp_lock_state
switch_queue_depth_packets
switch_packet_drops_total
packet_microburst_active
fpga_pipeline_latency_ns
nic_rx_packets_total
nic_tx_packets_total
```

The replay exporter makes the Grafana dashboards behave like a low-latency hardware observability platform without requiring physical PTP clocks, switches, or FPGA/NIC hardware.

---

## Repository Layout

```text
.
├── deploy/
├── docs/
├── exporters/
│   ├── hardware_telemetry_replay/
│   └── traffic_exporter/
├── infra/
├── node-setup/
├── obs-stack/
│   ├── docker-compose.yml
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       └── datasources/
│   └── prometheus/
├── scripts/
├── tests/
├── Makefile
├── README.md
└── requirements-dev.txt
```

---

## Exporters

### Traffic Exporter

Path:

```text
exporters/traffic_exporter/
```

The traffic exporter runs on both traffic nodes.

It performs:

```text
ping test
iperf3 TCP throughput test
iperf3 UDP throughput / jitter / loss test
```

Default port:

```text
9201
```

Example metric:

```text
traffic_exporter_up{device="ec2-a-tx",flow="ec2-a-tx-to-ec2-b-rx",peer="ec2-b-rx",role="sender"} 1
```

### Hardware Telemetry Replay Exporter

Path:

```text
exporters/hardware_telemetry_replay/
```

The replay exporter runs as part of the Docker Compose observability stack.

Default port:

```text
9202
```

It emits simulated/replayed low-latency hardware telemetry for dashboards and incident playback.

---

## Local Development

Create a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

Install test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Run validation:

```bash
python3 scripts/render_prometheus_config.py
python3 scripts/validate_stack.py
```

---

## Observability Stack Deployment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
nano .env
```

Important values:

```env
GRAFANA_DOMAIN=obs.zetaslate.com
GRAFANA_ROOT_URL=https://obs.zetaslate.com/

EC2_A_PRIVATE_IP=<ec2-a-tx-private-ip>
EC2_B_PRIVATE_IP=<ec2-b-rx-private-ip>

NODE_EXPORTER_PORT=9100
TRAFFIC_EXPORTER_PORT=9201
HARDWARE_REPLAY_EXPORTER_PORT=9202

PROMETHEUS_RETENTION_TIME=6h
PROMETHEUS_RETENTION_SIZE=512MB
```

Render Prometheus config:

```bash
python3 scripts/render_prometheus_config.py
```

Start the stack:

```bash
cd obs-stack
docker compose --env-file ../.env up -d --build
```

Check containers:

```bash
docker compose --env-file ../.env ps
```

Check Prometheus:

```bash
curl "http://localhost:9090/api/v1/query?query=up"
```

Check Grafana:

```bash
curl -I http://localhost:3000/login
```

---

## Traffic Node Deployment

Both traffic nodes need:

```text
prometheus-node-exporter
iperf3
chrony
python3
python3-venv
python3-pip
python-is-python3
git
curl
iputils-ping
```

Install packages:

```bash
sudo apt update
sudo apt install -y prometheus-node-exporter iperf3 chrony python3 python3-venv python3-pip python-is-python3 git curl htop iputils-ping
```

Enable node_exporter:

```bash
sudo systemctl enable prometheus-node-exporter
sudo systemctl start prometheus-node-exporter
```

Enable chrony:

```bash
sudo systemctl enable chrony
sudo systemctl start chrony
```

Clone the repo:

```bash
cd ~
git clone git@github.com:<your-user>/low-latency-telemetry-engine.git
cd low-latency-telemetry-engine
```

Create Python environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r exporters/traffic_exporter/requirements.txt
```

---

## TX Node Environment

File:

```text
/etc/traffic-exporter.env
```

Example for `ec2-a-tx`:

```env
NODE_NAME=ec2-a-tx
NODE_ROLE=sender
PEER_HOST=<ec2-b-rx-private-ip>
EXPORTER_HOST=0.0.0.0
EXPORTER_PORT=9201
IPERF3_PORT=5201
PING_COUNT=5
PING_TIMEOUT_SECONDS=2
IPERF3_DURATION_SECONDS=5
IPERF3_UDP_BANDWIDTH=1M
TRAFFIC_EXPORTER_UPDATE_INTERVAL_SECONDS=30
```

---

## RX Node Environment

File:

```text
/etc/traffic-exporter.env
```

Example for `ec2-b-rx`:

```env
NODE_NAME=ec2-b-rx
NODE_ROLE=receiver
PEER_HOST=<ec2-a-tx-private-ip>
EXPORTER_HOST=0.0.0.0
EXPORTER_PORT=9201
IPERF3_PORT=5201
PING_COUNT=5
PING_TIMEOUT_SECONDS=2
IPERF3_DURATION_SECONDS=5
IPERF3_UDP_BANDWIDTH=1M
TRAFFIC_EXPORTER_UPDATE_INTERVAL_SECONDS=30
```

---

## systemd Services

### Traffic Exporter

File:

```text
/etc/systemd/system/traffic-exporter.service
```

```ini
[Unit]
Description=Traffic Exporter
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/low-latency-telemetry-engine
EnvironmentFile=/etc/traffic-exporter.env
ExecStart=/home/ubuntu/low-latency-telemetry-engine/.venv/bin/python /home/ubuntu/low-latency-telemetry-engine/exporters/traffic_exporter/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable traffic-exporter
sudo systemctl start traffic-exporter
```

Verify:

```bash
systemctl status traffic-exporter --no-pager
curl localhost:9201/metrics | grep traffic_exporter_up
```

### RX iperf3 Server

File:

```text
/etc/systemd/system/iperf3-server.service
```

```ini
[Unit]
Description=iperf3 Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/iperf3 -s -p 5201
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start on RX:

```bash
sudo systemctl daemon-reload
sudo systemctl enable iperf3-server
sudo systemctl start iperf3-server
```

Verify:

```bash
systemctl status iperf3-server --no-pager
```

---

## End-to-End Validation

From `ec2-a-tx`, test RX traffic:

```bash
iperf3 -c <ec2-b-rx-private-ip> -p 5201 -t 10
iperf3 -c <ec2-b-rx-private-ip> -p 5201 -u -b 1M -t 10
ping -c 5 <ec2-b-rx-private-ip>
```

Check TX metrics:

```bash
curl localhost:9201/metrics | grep -E 'traffic_exporter_up|flow_tcp_throughput_mbps|flow_udp_throughput_mbps|flow_udp_jitter_ms|flow_udp_loss_percent|flow_rtt_ms|flow_ping_packet_loss_percent|flow_test_success'
```

Check RX metrics:

```bash
curl localhost:9201/metrics | grep traffic_exporter_up
```

From `ec2-obs`, check Prometheus target health:

```bash
curl "http://localhost:9090/api/v1/query?query=up"
```

Expected healthy targets:

```text
prometheus
ec2-a-tx-node
ec2-b-rx-node
ec2-a-tx-traffic
ec2-b-rx-traffic
hardware-telemetry-replay
```

---

## Nginx Reverse Proxy

Grafana is exposed through an existing Nginx reverse proxy.

Expected Nginx virtual host behavior:

```text
http://obs.zetaslate.com  -> redirects to HTTPS
https://obs.zetaslate.com -> proxies to Grafana on ec2-obs:3000
```

Example Nginx server config:

```nginx
server {
  listen 80;
  server_name obs.zetaslate.com;

  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl;
  server_name obs.zetaslate.com;

  ssl_certificate /etc/letsencrypt/live/obs.zetaslate.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/obs.zetaslate.com/privkey.pem;

  location / {
    proxy_pass http://<ec2-obs-private-ip>:3000;

    proxy_http_version 1.1;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;

    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
  }
}
```

---

## Security Group Requirements

### ec2-obs

Inbound:

```text
22/tcp from admin source
3000/tcp from Nginx proxy security group
```

Outbound:

```text
9100/tcp to ec2-a-tx and ec2-b-rx
9201/tcp to ec2-a-tx and ec2-b-rx
80/443 to internet
```

### ec2-a-tx

Inbound:

```text
22/tcp from admin source
9100/tcp from ec2-obs
9201/tcp from ec2-obs
ICMP from ec2-b-rx if bidirectional ping is needed
```

Outbound:

```text
5201/tcp to ec2-b-rx
5201/udp to ec2-b-rx
80/443 to internet
```

### ec2-b-rx

Inbound:

```text
22/tcp from admin source
9100/tcp from ec2-obs
9201/tcp from ec2-obs
5201/tcp from ec2-a-tx
5201/udp from ec2-a-tx
ICMP from ec2-a-tx if ping metrics are desired
```

Outbound:

```text
80/443 to internet
```

---

## Dashboards

### Platform Overview

Shows high-level service health:

```text
Prometheus target status
Node availability
Traffic exporter health
Replay exporter health
```

### Two-Node Traffic Lab

Shows real TX/RX traffic metrics:

```text
TCP throughput
UDP throughput
UDP jitter
UDP loss
RTT latency
Ping packet loss
Traffic test success
```

### PTP / Switch / FPGA Telemetry

Live dashboard:

```text
https://obs.zetaslate.com/d/hardware-telemetry/ptp-switch-fpga-telemetry?orgId=1&from=now-30m&to=now&timezone=browser&refresh=10s
```

Shows replayed hardware-style telemetry:

```text
PTP offset
PTP lock state
Switch queue depth
Switch packet drops
Packet microburst state
FPGA/NIC pipeline latency
NIC packet counters
```

### Incident Replay

Live dashboard:

```text
https://obs.zetaslate.com/d/incident-replay/incident-replay?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s
```

Shows short-window event behavior for:

```text
microbursts
queue spikes
packet drops
PTP drift
pipeline latency jumps
```

---

## MVP Status

Completed:

```text
Grafana deployed
Prometheus deployed
Nginx HTTPS reverse proxy configured
Hardware telemetry replay exporter running
PTP / switch / FPGA telemetry dashboard provisioned
Incident replay dashboard provisioned
Two-node traffic exporter implemented
TX node deployed
RX node deployed
node_exporter running on traffic nodes
iperf3 traffic path configured
Prometheus scraping observability and traffic metrics
```

Final verification checklist:

```text
https://obs.zetaslate.com loads Grafana over HTTPS
Prometheus target health shows all expected targets up
traffic_exporter_up is 1 for TX and RX
node_exporter is up for TX and RX
TCP throughput appears in Grafana
UDP throughput appears in Grafana
UDP jitter appears in Grafana
UDP loss appears in Grafana
RTT appears in Grafana if ICMP is allowed
hardware replay metrics appear in Grafana
incident replay dashboard shows changing replay data
```

---

## Known Deployment Lessons

Issues encountered and fixed during deployment:

```text
Nginx vhost config must match the container include path
Certbot script requires EMAIL to be set
Do not run Windows .bat scripts inside Linux EC2 hosts
hardware_telemetry_replay requires prometheus-client in requirements.txt
systemd services cannot have duplicate ExecStart lines
traffic exporter requires iperf3 installed on the host
use python3-venv instead of version-specific python3.12-venv on newer Ubuntu images
```

These fixes are reflected in the deployment notes and should be kept in the repo scripts/docs where possible.

---


