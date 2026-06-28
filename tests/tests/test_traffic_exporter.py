from __future__ import annotations

from exporters.traffic_exporter.main import bits_to_mbps, parse_json


def test_bits_to_mbps_converts_bits_per_second_to_megabits() -> None:
    assert bits_to_mbps(1_000_000) == 1.0
    assert bits_to_mbps(10_500_000) == 10.5
    assert bits_to_mbps(0) == 0.0


def test_parse_json_returns_dict_for_valid_json() -> None:
    payload = parse_json('{"end": {"sum": {"bits_per_second": 1000000}}}')

    assert payload is not None
    assert payload["end"]["sum"]["bits_per_second"] == 1_000_000


def test_parse_json_returns_none_for_invalid_json() -> None:
    assert parse_json("not-json") is None


def test_parse_json_returns_none_for_empty_string() -> None:
    assert parse_json("") is None