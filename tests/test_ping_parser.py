from __future__ import annotations

from exporters.traffic_exporter.ping import parse_ping_metrics


def test_parse_ping_metrics_extracts_loss_and_average_rtt() -> None:
    stdout = """
10 packets transmitted, 10 received, 0% packet loss, time 9015ms
rtt min/avg/max/mdev = 0.111/0.222/0.333/0.044 ms
"""

    metrics = parse_ping_metrics(stdout)

    assert metrics["packet_loss_percent"] == 0.0
    assert metrics["rtt_ms"] == 0.222


def test_parse_ping_metrics_extracts_packet_loss_without_rtt() -> None:
    stdout = "5 packets transmitted, 0 received, 100% packet loss, time 4095ms"

    metrics = parse_ping_metrics(stdout)

    assert metrics["packet_loss_percent"] == 100.0
    assert "rtt_ms" not in metrics