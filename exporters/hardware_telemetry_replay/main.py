#!/usr/bin/env python3

from __future__ import annotations

import os
import time

from prometheus_client import Gauge, start_http_server

try:
    from exporters.hardware_telemetry_replay.scenarios import sample_metrics
except ModuleNotFoundError:
    from scenarios import sample_metrics


EXPORTER_HOST = os.getenv("EXPORTER_HOST", "0.0.0.0")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9202"))
SITE = os.getenv("SITE", "low-latency-lab")
SCENARIO = os.getenv("HARDWARE_REPLAY_SCENARIO", "incident")
UPDATE_INTERVAL_SECONDS = int(
    os.getenv("HARDWARE_REPLAY_UPDATE_INTERVAL_SECONDS", "5")
)

LABELS = ["site", "device", "device_type", "source", "scenario"]


ptp_offset_ns = Gauge(
    "ptp_offset_ns",
    "Simulated PTP clock offset in nanoseconds.",
    LABELS,
)

ptp_path_delay_ns = Gauge(
    "ptp_path_delay_ns",
    "Simulated PTP path delay in nanoseconds.",
    LABELS,
)

ptp_sync_state = Gauge(
    "ptp_sync_state",
    "Simulated PTP sync state. 1 means synced, 0 means unsynced.",
    LABELS,
)

switch_queue_drops_total = Gauge(
    "switch_queue_drops_total",
    "Replayed switch queue drop count.",
    LABELS,
)

switch_buffer_utilization_percent = Gauge(
    "switch_buffer_utilization_percent",
    "Replayed switch buffer utilization percentage.",
    LABELS,
)

fpga_pipeline_latency_ns = Gauge(
    "fpga_pipeline_latency_ns",
    "Replayed FPGA/NIC pipeline latency in nanoseconds.",
    LABELS,
)

fpga_packet_rx_total = Gauge(
    "fpga_packet_rx_total",
    "Replayed FPGA/NIC received packet count.",
    LABELS,
)

fpga_packet_drop_total = Gauge(
    "fpga_packet_drop_total",
    "Replayed FPGA/NIC dropped packet count.",
    LABELS,
)

packet_sequence_gap_total = Gauge(
    "packet_sequence_gap_total",
    "Replayed packet sequence gap count.",
    LABELS,
)

packet_microburst_active = Gauge(
    "packet_microburst_active",
    "Replayed microburst state. 1 means active, 0 means inactive.",
    LABELS,
)


def labels(device: str, device_type: str) -> dict[str, str]:
    return {
        "site": SITE,
        "device": device,
        "device_type": device_type,
        "source": "simulated",
        "scenario": SCENARIO,
    }


def publish_once() -> None:
    metrics = sample_metrics(SCENARIO)

    ptp = metrics["ptp"]
    ptp_labels = labels(ptp["device"], ptp["device_type"])
    ptp_offset_ns.labels(**ptp_labels).set(ptp["ptp_offset_ns"])
    ptp_path_delay_ns.labels(**ptp_labels).set(ptp["ptp_path_delay_ns"])
    ptp_sync_state.labels(**ptp_labels).set(ptp["ptp_sync_state"])

    switch = metrics["switch"]
    switch_labels = labels(switch["device"], switch["device_type"])
    switch_queue_drops_total.labels(**switch_labels).set(
        switch["switch_queue_drops_total"]
    )
    switch_buffer_utilization_percent.labels(**switch_labels).set(
        switch["switch_buffer_utilization_percent"]
    )
    packet_microburst_active.labels(**switch_labels).set(
        switch["packet_microburst_active"]
    )

    fpga = metrics["fpga"]
    fpga_labels = labels(fpga["device"], fpga["device_type"])
    fpga_pipeline_latency_ns.labels(**fpga_labels).set(
        fpga["fpga_pipeline_latency_ns"]
    )
    fpga_packet_rx_total.labels(**fpga_labels).set(fpga["fpga_packet_rx_total"])
    fpga_packet_drop_total.labels(**fpga_labels).set(fpga["fpga_packet_drop_total"])
    packet_sequence_gap_total.labels(**fpga_labels).set(
        fpga["packet_sequence_gap_total"]
    )


def main() -> None:
    start_http_server(EXPORTER_PORT, addr=EXPORTER_HOST)

    print(
        f"hardware_telemetry_replay listening on {EXPORTER_HOST}:{EXPORTER_PORT} "
        f"site={SITE} scenario={SCENARIO}",
        flush=True,
    )

    while True:
        publish_once()
        time.sleep(UPDATE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()