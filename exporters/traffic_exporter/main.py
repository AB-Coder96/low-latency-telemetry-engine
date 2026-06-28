# exporters/traffic_exporter/main.py

#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from typing import Any

from prometheus_client import Gauge, start_http_server


NODE_NAME = os.getenv("NODE_NAME", "unknown-node")
NODE_ROLE = os.getenv("NODE_ROLE", "unknown-role")
PEER_HOST = os.getenv("PEER_HOST", "")
EXPORTER_HOST = os.getenv("EXPORTER_HOST", "0.0.0.0")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9201"))
IPERF3_PORT = int(os.getenv("IPERF3_PORT", "5201"))
PING_COUNT = int(os.getenv("PING_COUNT", "5"))
PING_TIMEOUT_SECONDS = int(os.getenv("PING_TIMEOUT_SECONDS", "2"))
IPERF3_DURATION_SECONDS = int(os.getenv("IPERF3_DURATION_SECONDS", "5"))
IPERF3_UDP_BANDWIDTH = os.getenv("IPERF3_UDP_BANDWIDTH", "1M")
UPDATE_INTERVAL_SECONDS = int(os.getenv("TRAFFIC_EXPORTER_UPDATE_INTERVAL_SECONDS", "30"))


def peer_device_name() -> str:
    if NODE_ROLE == "sender":
        return "ec2-b-rx"
    if NODE_ROLE == "receiver":
        return "ec2-a-tx"
    return "unknown-peer"


def flow_name() -> str:
    if NODE_ROLE == "sender":
        return f"{NODE_NAME}-to-{peer_device_name()}"
    if NODE_ROLE == "receiver":
        return f"{peer_device_name()}-to-{NODE_NAME}"
    return "unknown-flow"


LABELS = ["device", "role", "peer", "flow"]

traffic_exporter_up = Gauge(
    "traffic_exporter_up",
    "Traffic exporter health status.",
    LABELS,
)

flow_rtt_ms = Gauge(
    "flow_rtt_ms",
    "ICMP round-trip latency in milliseconds.",
    LABELS,
)

flow_ping_packet_loss_percent = Gauge(
    "flow_ping_packet_loss_percent",
    "ICMP packet loss percentage.",
    LABELS,
)

flow_tcp_throughput_mbps = Gauge(
    "flow_tcp_throughput_mbps",
    "iperf3 TCP throughput in megabits per second.",
    LABELS,
)

flow_udp_throughput_mbps = Gauge(
    "flow_udp_throughput_mbps",
    "iperf3 UDP throughput in megabits per second.",
    LABELS,
)

flow_udp_jitter_ms = Gauge(
    "flow_udp_jitter_ms",
    "iperf3 UDP jitter in milliseconds.",
    LABELS,
)

flow_udp_loss_percent = Gauge(
    "flow_udp_loss_percent",
    "iperf3 UDP loss percentage.",
    LABELS,
)

flow_test_success = Gauge(
    "flow_test_success",
    "Traffic test success status: 1 success, 0 failure.",
    ["device", "role", "peer", "flow", "test"],
)

traffic_exporter_last_update_timestamp_seconds = Gauge(
    "traffic_exporter_last_update_timestamp_seconds",
    "Unix timestamp for the last traffic exporter update.",
    LABELS,
)


def labels() -> dict[str, str]:
    return {
        "device": NODE_NAME,
        "role": NODE_ROLE,
        "peer": PEER_HOST or "unset",
        "flow": flow_name(),
    }


def run_command(command: list[str], timeout: int) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "command timed out"


def run_ping() -> None:
    metric_labels = labels()

    if not PEER_HOST:
        flow_test_success.labels(**metric_labels, test="ping").set(0)
        return

    command = [
        "ping",
        "-c",
        str(PING_COUNT),
        "-W",
        str(PING_TIMEOUT_SECONDS),
        PEER_HOST,
    ]

    code, stdout, _stderr = run_command(
        command,
        timeout=(PING_COUNT * PING_TIMEOUT_SECONDS) + 5,
    )

    loss_match = re.search(r"(\d+(?:\.\d+)?)% packet loss", stdout)
    rtt_match = re.search(
        r"rtt min/avg/max/(?:mdev|stddev) = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms",
        stdout,
    )

    if loss_match:
        flow_ping_packet_loss_percent.labels(**metric_labels).set(float(loss_match.group(1)))

    if rtt_match:
        flow_rtt_ms.labels(**metric_labels).set(float(rtt_match.group(1)))

    flow_test_success.labels(**metric_labels, test="ping").set(1 if code == 0 else 0)


def parse_json(stdout: str) -> dict[str, Any] | None:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


def bits_to_mbps(bits_per_second: float) -> float:
    return bits_per_second / 1_000_000.0


def run_iperf_tcp() -> None:
    metric_labels = labels()

    if NODE_ROLE != "sender" or not PEER_HOST:
        return

    command = [
        "iperf3",
        "-c",
        PEER_HOST,
        "-p",
        str(IPERF3_PORT),
        "-t",
        str(IPERF3_DURATION_SECONDS),
        "--json",
    ]

    code, stdout, _stderr = run_command(
        command,
        timeout=IPERF3_DURATION_SECONDS + 10,
    )

    payload = parse_json(stdout)

    if code != 0 or not payload:
        flow_test_success.labels(**metric_labels, test="iperf_tcp").set(0)
        return

    end = payload.get("end", {})
    summary = (
        end.get("sum_sent")
        or end.get("sum_received")
        or end.get("sum")
        or {}
    )

    bps = float(summary.get("bits_per_second", 0.0))
    flow_tcp_throughput_mbps.labels(**metric_labels).set(bits_to_mbps(bps))
    flow_test_success.labels(**metric_labels, test="iperf_tcp").set(1)


def run_iperf_udp() -> None:
    metric_labels = labels()

    if NODE_ROLE != "sender" or not PEER_HOST:
        return

    command = [
        "iperf3",
        "-c",
        PEER_HOST,
        "-p",
        str(IPERF3_PORT),
        "-u",
        "-b",
        IPERF3_UDP_BANDWIDTH,
        "-t",
        str(IPERF3_DURATION_SECONDS),
        "--json",
    ]

    code, stdout, _stderr = run_command(
        command,
        timeout=IPERF3_DURATION_SECONDS + 10,
    )

    payload = parse_json(stdout)

    if code != 0 or not payload:
        flow_test_success.labels(**metric_labels, test="iperf_udp").set(0)
        return

    end = payload.get("end", {})
    summary = end.get("sum") or end.get("sum_received") or {}

    bps = float(summary.get("bits_per_second", 0.0))
    jitter_ms = float(summary.get("jitter_ms", 0.0))
    lost_percent = float(summary.get("lost_percent", 0.0))

    flow_udp_throughput_mbps.labels(**metric_labels).set(bits_to_mbps(bps))
    flow_udp_jitter_ms.labels(**metric_labels).set(jitter_ms)
    flow_udp_loss_percent.labels(**metric_labels).set(lost_percent)
    flow_test_success.labels(**metric_labels, test="iperf_udp").set(1)


def update_loop() -> None:
    metric_labels = labels()

    while True:
        traffic_exporter_up.labels(**metric_labels).set(1)

        run_ping()
        run_iperf_tcp()
        run_iperf_udp()

        traffic_exporter_last_update_timestamp_seconds.labels(**metric_labels).set(time.time())

        time.sleep(UPDATE_INTERVAL_SECONDS)


def main() -> None:
    start_http_server(EXPORTER_PORT, addr=EXPORTER_HOST)
    print(
        f"traffic_exporter listening on {EXPORTER_HOST}:{EXPORTER_PORT} "
        f"node={NODE_NAME} role={NODE_ROLE} peer={PEER_HOST}",
        flush=True,
    )
    update_loop()


if __name__ == "__main__":
    main()