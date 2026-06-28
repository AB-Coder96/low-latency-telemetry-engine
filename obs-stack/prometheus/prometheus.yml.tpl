# obs-stack/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - prometheus:9090
        labels:
          device: ec2-obs
          role: observability
          device_type: service

  - job_name: node
    static_configs:
      - targets:
          - "${EC2_A_PRIVATE_IP}:${NODE_EXPORTER_PORT}"
        labels:
          device: ec2-a-tx
          role: sender
          device_type: linux_host

      - targets:
          - "${EC2_B_PRIVATE_IP}:${NODE_EXPORTER_PORT}"
        labels:
          device: ec2-b-rx
          role: receiver
          device_type: linux_host

  - job_name: traffic
    static_configs:
      - targets:
          - "${EC2_A_PRIVATE_IP}:${TRAFFIC_EXPORTER_PORT}"
        labels:
          device: ec2-a-tx
          role: sender
          device_type: linux_host
          flow: ec2-a-tx-to-ec2-b-rx

      - targets:
          - "${EC2_B_PRIVATE_IP}:${TRAFFIC_EXPORTER_PORT}"
        labels:
          device: ec2-b-rx
          role: receiver
          device_type: linux_host
          flow: ec2-a-tx-to-ec2-b-rx

  - job_name: hardware-telemetry-replay
    static_configs:
      - targets:
          - "hardware-telemetry-replay:${HARDWARE_REPLAY_EXPORTER_PORT}"
        labels:
          device: hardware-telemetry-replay
          role: telemetry_replay
          device_type: simulated_hardware
          source: simulated