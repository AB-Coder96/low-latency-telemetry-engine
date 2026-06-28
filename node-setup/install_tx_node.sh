# node-setup/install_tx_node.sh

#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/grafana-network-observability-platform}"
CONFIG_DIR="/etc/grafana-netobs"

if [[ $EUID -ne 0 ]]; then
  echo "run as root: sudo $0"
  exit 1
fi

apt-get update
apt-get install -y \
  prometheus-node-exporter \
  iperf3 \
  chrony \
  python3 \
  python3-venv \
  python3-pip \
  git \
  curl

systemctl enable --now prometheus-node-exporter
systemctl enable --now chrony

mkdir -p "${CONFIG_DIR}"

if [[ ! -f "${CONFIG_DIR}/traffic-exporter.env" ]]; then
  cp "${REPO_DIR}/node-setup/traffic-exporter.env.example" "${CONFIG_DIR}/traffic-exporter.env"
  sed -i 's/NODE_NAME=ec2-a-tx/NODE_NAME=ec2-a-tx/g' "${CONFIG_DIR}/traffic-exporter.env"
  sed -i 's/NODE_ROLE=sender/NODE_ROLE=sender/g' "${CONFIG_DIR}/traffic-exporter.env"
fi

cp "${REPO_DIR}/node-setup/traffic-exporter.service" /etc/systemd/system/traffic-exporter.service

systemctl daemon-reload
systemctl enable traffic-exporter

echo "TX node base setup complete."
echo "Edit ${CONFIG_DIR}/traffic-exporter.env and set PEER_HOST to ec2-b-rx private DNS/IP."
echo "Then run:"
echo "  sudo systemctl restart traffic-exporter"