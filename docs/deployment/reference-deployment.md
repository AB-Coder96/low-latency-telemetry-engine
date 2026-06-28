# Reference Deployment

This project uses one observability node and two traffic nodes.

## Hosts

| Host | Role | Services |
|---|---|---|
| `ec2-web-proxy` | Public HTTPS reverse proxy | Nginx |
| `ec2-obs` | Observability node | Grafana, Prometheus, demo hardware exporter |
| `ec2-a-tx` | Sender traffic node | node_exporter, traffic_exporter, iperf3 client |
| `ec2-b-rx` | Receiver traffic node | node_exporter, traffic_exporter, iperf3 server |

## Network Flow

```text
Internet
  ↓
obs.example.com
  ↓
ec2-web-proxy / Nginx
  ↓
ec2-obs:3000
  ↓
Grafana
