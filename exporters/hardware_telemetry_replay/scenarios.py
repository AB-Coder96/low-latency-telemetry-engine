from __future__ import annotations

import math
import time
from typing import Any


def _pulse(now: float, period_seconds: int, width_seconds: int) -> bool:
    return int(now) % period_seconds < width_seconds


def sample_metrics(scenario: str) -> dict[str, dict[str, Any]]:
    now = time.time()
    incident_active = scenario == "incident" and _pulse(now, 90, 20)

    wave = math.sin(now / 8.0)

    ptp_offset = 65 + (wave * 18)
    ptp_path_delay = 420 + (wave * 35)

    switch_drops = int((now // 10) % 100)
    switch_buffer = 32 + (wave * 8)

    fpga_latency = 780 + (wave * 55)
    fpga_rx = int(now * 150) % 10_000_000
    fpga_drops = int((now // 15) % 50)
    sequence_gaps = int((now // 30) % 20)

    if incident_active:
        ptp_offset += 950
        ptp_path_delay += 350
        switch_drops += 500
        switch_buffer = 91
        fpga_latency += 2_500
        fpga_drops += 120
        sequence_gaps += 80

    return {
        "ptp": {
            "device": "ptp-clock-0",
            "device_type": "ptp_clock",
            "ptp_offset_ns": max(ptp_offset, 0),
            "ptp_path_delay_ns": max(ptp_path_delay, 0),
            "ptp_sync_state": 0 if incident_active else 1,
        },
        "switch": {
            "device": "leaf-switch-0",
            "device_type": "switch",
            "switch_queue_drops_total": switch_drops,
            "switch_buffer_utilization_percent": min(max(switch_buffer, 0), 100),
            "packet_microburst_active": 1 if incident_active else 0,
        },
        "fpga": {
            "device": "fpga-nic-0",
            "device_type": "fpga_nic",
            "fpga_pipeline_latency_ns": max(fpga_latency, 0),
            "fpga_packet_rx_total": fpga_rx,
            "fpga_packet_drop_total": fpga_drops,
            "packet_sequence_gap_total": sequence_gaps,
        },
    }