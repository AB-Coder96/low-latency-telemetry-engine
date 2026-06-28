from __future__ import annotations

import re


def parse_ping_metrics(stdout: str) -> dict[str, float]:
    metrics: dict[str, float] = {}

    loss_match = re.search(r"(\d+(?:\.\d+)?)% packet loss", stdout)
    rtt_match = re.search(
        r"rtt min/avg/max/(?:mdev|stddev) = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms",
        stdout,
    )

    if loss_match:
        metrics["packet_loss_percent"] = float(loss_match.group(1))

    if rtt_match:
        metrics["rtt_ms"] = float(rtt_match.group(1))

    return metrics