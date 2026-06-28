from __future__ import annotations

import json
from typing import Any


def parse_json(stdout: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def bits_to_mbps(bits_per_second: float | int) -> float:
    return float(bits_per_second) / 1_000_000.0


def extract_tcp_throughput_mbps(payload: dict[str, Any]) -> float:
    end = payload.get("end", {})
    summary = (
        end.get("sum_sent")
        or end.get("sum_received")
        or end.get("sum")
        or {}
    )

    return bits_to_mbps(float(summary.get("bits_per_second", 0.0)))


def extract_udp_metrics(payload: dict[str, Any]) -> dict[str, float]:
    end = payload.get("end", {})
    summary = end.get("sum") or end.get("sum_received") or {}

    return {
        "throughput_mbps": bits_to_mbps(float(summary.get("bits_per_second", 0.0))),
        "jitter_ms": float(summary.get("jitter_ms", 0.0)),
        "loss_percent": float(summary.get("lost_percent", 0.0)),
    }