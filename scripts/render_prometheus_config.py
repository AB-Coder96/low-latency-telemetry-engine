# scripts/render_prometheus_config.py

#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}

    if not path.exists():
        raise FileNotFoundError(f"missing env file: {path}")

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def render(template: str, values: dict[str, str]) -> str:
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)

        if key in os.environ:
            return os.environ[key]

        if key in values:
            return values[key]

        missing.add(key)
        return match.group(0)

    rendered = VAR_PATTERN.sub(replace, template)

    if missing:
        missing_vars = ", ".join(sorted(missing))
        raise KeyError(f"missing required environment variables: {missing_vars}")

    return rendered


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    env_path = repo_root / ".env"
    template_path = repo_root / "obs-stack" / "prometheus" / "prometheus.yml.tpl"
    output_path = repo_root / "obs-stack" / "prometheus" / "prometheus.yml"

    env_values = load_env(env_path)
    template = template_path.read_text()
    output = render(template, env_values)

    output_path.write_text(output)
    print(f"rendered {output_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)