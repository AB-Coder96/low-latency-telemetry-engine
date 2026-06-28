from __future__ import annotations

from exporters.traffic_exporter.iperf import (
    bits_to_mbps,
    extract_tcp_throughput_mbps,
    extract_udp_metrics,
    parse_json,
)


def test_parse_json_returns_dict_for_valid_json() -> None:
    payload = parse_json('{"end": {"sum": {"bits_per_second": 1000000}}}')

    assert payload is not None
    assert payload["end"]["sum"]["bits_per_second"] == 1_000_000


def test_parse_json_returns_none_for_invalid_json() -> None:
    assert parse_json("not-json") is None


def test_parse_json_returns_none_for_json_list() -> None:
    assert parse_json("[]") is None


def test_bits_to_mbps_converts_bits_per_second_to_megabits() -> None:
    assert bits_to_mbps(1_000_000) == 1.0
    assert bits_to_mbps(10_500_000) == 10.5
    assert bits_to_mbps(0) == 0.0


def test_extract_tcp_throughput_mbps_uses_sum_sent() -> None:
    payload = {
        "end": {
            "sum_sent": {
                "bits_per_second": 42_000_000,
            }
        }
    }

    assert extract_tcp_throughput_mbps(payload) == 42.0


def test_extract_udp_metrics_uses_sum_values() -> None:
    payload = {
        "end": {
            "sum": {
                "bits_per_second": 1_500_000,
                "jitter_ms": 0.42,
                "lost_percent": 2.5,
            }
        }
    }

    metrics = extract_udp_metrics(payload)

    assert metrics["throughput_mbps"] == 1.5
    assert metrics["jitter_ms"] == 0.42
    assert metrics["loss_percent"] == 2.5