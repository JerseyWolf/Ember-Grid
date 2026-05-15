"""metrics.py — DORA metrics calculator for Ember Grid ops

Usage (import):
    from dora.metrics import calculate_dora_metrics
    m = calculate_dora_metrics(days=30)

MOCK_MODE=true (default): generates realistic time-series data that shows
ops-knowledge-loop's intended impact (MTTR, change failure rate and lead
time all trending down; deployment frequency stable).
"""

from __future__ import annotations

import math
import os
import random
import sys
from datetime import datetime, timezone

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

DEFAULT_DAYS = 30
RANDOM_SEED = int(os.getenv("DORA_SEED", "42"))

BASELINES = {
    "mttr_hours": {"start": 3.8, "end": 2.1, "noise": 0.25, "direction": "down"},
    "change_failure_rate": {"start": 11.4, "end": 7.0, "noise": 1.0, "direction": "down"},
    "deployment_frequency": {"start": 4.2, "end": 4.2, "noise": 0.4, "direction": "flat"},
    "lead_time_hours": {"start": 17.6, "end": 12.0, "noise": 0.9, "direction": "down"},
}


def _linear_series(start: float, end: float, noise: float, days: int, rng: random.Random) -> list[float]:
    """Build a noisy linear progression from start to end across `days` samples."""
    if days < 2:
        return [round(start, 2)]
    series: list[float] = []
    for i in range(days):
        fraction = i / (days - 1)
        base = start + (end - start) * fraction
        jitter = rng.uniform(-noise, noise)
        value = max(0.0, base + jitter)
        series.append(round(value, 2))
    return series


def _trend(direction: str, last_week_avg: float, prev_week_avg: float) -> str:
    """Classify the metric trend label given the desired direction."""
    if math.isclose(prev_week_avg, 0.0):
        return "stable"
    delta_pct = (last_week_avg - prev_week_avg) / prev_week_avg * 100.0
    if direction == "flat" and abs(delta_pct) < 5.0:
        return "stable"
    if direction == "down":
        if delta_pct < -2.0:
            return "improving"
        if delta_pct > 2.0:
            return "degrading"
        return "stable"
    if direction == "up":
        if delta_pct > 2.0:
            return "improving"
        if delta_pct < -2.0:
            return "degrading"
        return "stable"
    return "stable"


def _week_delta_pct(series: list[float]) -> float:
    """Compute percentage change between the last 7 days and the prior 7."""
    if len(series) < 14:
        return 0.0
    last_week = sum(series[-7:]) / 7.0
    prev_week = sum(series[-14:-7]) / 7.0
    if math.isclose(prev_week, 0.0):
        return 0.0
    return round((last_week - prev_week) / prev_week * 100.0, 2)


def _summary(series: list[float]) -> float:
    """Return the recent-7-day mean as the headline value for a metric."""
    if not series:
        return 0.0
    tail = series[-7:] if len(series) >= 7 else series
    return round(sum(tail) / len(tail), 2)


def _fetch_real_metrics(days: int) -> dict:
    """Placeholder for the real BigQuery DORA join — not implemented in this demo."""
    raise NotImplementedError(
        "Real DORA pipeline not wired up in this demo. "
        "Use MOCK_MODE=true to compute the demonstration series."
    )


def calculate_dora_metrics(days: int = DEFAULT_DAYS) -> dict:
    """Calculate DORA metrics for Ember Grid operations over the last N days.

    MOCK_MODE=true: generates realistic time-series mock data.

    Returns dict with keys:
    - mttr_hours: float (mean, e.g. 3.8)
    - change_failure_rate: float (percentage, e.g. 11.4)
    - deployment_frequency: float (per day, e.g. 4.2)
    - lead_time_hours: float (e.g. 17.6)
    - trends: dict mapping each metric to "improving", "degrading", or "stable"
    - week_delta: dict mapping each metric to float (% change vs previous week)
    - daily_series: dict mapping each metric to list of 30 floats (time series)
    - generated_at: str (ISO timestamp)
    """
    if not MOCK_MODE:
        return _fetch_real_metrics(days)

    rng = random.Random(RANDOM_SEED)
    daily_series: dict[str, list[float]] = {}
    headline: dict[str, float] = {}
    trends: dict[str, str] = {}
    week_delta: dict[str, float] = {}

    for name, spec in BASELINES.items():
        series = _linear_series(spec["start"], spec["end"], spec["noise"], days, rng)
        daily_series[name] = series
        headline[name] = _summary(series)
        last_week_avg = sum(series[-7:]) / max(1, len(series[-7:]))
        prev_week_avg = sum(series[-14:-7]) / max(1, len(series[-14:-7])) if len(series) >= 14 else last_week_avg
        trends[name] = _trend(spec["direction"], last_week_avg, prev_week_avg)
        week_delta[name] = _week_delta_pct(series)

    return {
        "mttr_hours": headline["mttr_hours"],
        "change_failure_rate": headline["change_failure_rate"],
        "deployment_frequency": headline["deployment_frequency"],
        "lead_time_hours": headline["lead_time_hours"],
        "trends": trends,
        "week_delta": week_delta,
        "daily_series": daily_series,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    """CLI entry: pretty-print the DORA metrics summary."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    metrics = calculate_dora_metrics()
    table = Table(title="Ember Grid DORA metrics (last 30 days)", header_style="bold cyan")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_column("Unit")
    table.add_column("Trend")
    table.add_column("Δ vs prev week", justify="right")
    units = {
        "mttr_hours": "hours",
        "change_failure_rate": "%",
        "deployment_frequency": "/day",
        "lead_time_hours": "hours",
    }
    for key in ("mttr_hours", "change_failure_rate", "deployment_frequency", "lead_time_hours"):
        table.add_row(
            key,
            f"{metrics[key]:.2f}",
            units[key],
            metrics["trends"][key],
            f"{metrics['week_delta'][key]:+.1f}%",
        )
    console.print(table)
    console.print(f"[dim]generated_at:[/dim] {metrics['generated_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
