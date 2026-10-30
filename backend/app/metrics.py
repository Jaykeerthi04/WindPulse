"""Pure forecast selection and accuracy calculations."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt
from typing import Any, Iterable


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def select_available_forecasts(rows: Iterable[dict[str, Any]], cutoff: datetime) -> dict[str, dict[str, Any]]:
    """Return one forecast per delivery time: latest publication <= cutoff.

    Grouping by startTime first prevents a later revision from leaking into a
    historical backtest merely because it has the same delivery period.
    """
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        published = parse_time(row["publishTime"])
        target = row["startTime"]
        if published > cutoff:
            continue
        if target not in best or published > parse_time(best[target]["publishTime"]):
            best[target] = row
    return best


def combine_actuals(rows: Iterable[dict[str, Any]]) -> dict[str, float]:
    """Sum onshore and offshore wind entries into a GB wind actual per period."""
    actuals: dict[str, float] = defaultdict(float)
    for row in rows:
        if row.get("psrType") in {"Wind Onshore", "Wind Offshore"}:
            actuals[row["startTime"]] += float(row["quantity"])
    return dict(actuals)


def compare(forecasts: dict[str, dict[str, Any]], actuals: dict[str, float]) -> dict[str, Any]:
    points = []
    for target in sorted(set(forecasts) & set(actuals)):
        forecast = float(forecasts[target]["generation"])
        actual = actuals[target]
        points.append({"time": target, "forecast": forecast, "actual": actual,
                       "error": forecast - actual, "publishTime": forecasts[target]["publishTime"]})
    if not points:
        return {"points": [], "mae": None, "rmse": None}
    errors = [point["error"] for point in points]
    return {"points": points, "mae": sum(abs(e) for e in errors) / len(errors),
            "rmse": sqrt(sum(e * e for e in errors) / len(errors))}
