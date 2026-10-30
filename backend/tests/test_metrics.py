from datetime import datetime, timezone
from app.metrics import combine_actuals, compare, select_available_forecasts


def test_only_uses_forecasts_published_by_cutoff():
    rows = [
        {"startTime": "2026-10-01T10:00:00Z", "publishTime": "2026-10-01T06:00:00Z", "generation": 100},
        {"startTime": "2026-10-01T10:00:00Z", "publishTime": "2026-10-01T09:00:00Z", "generation": 120},
        {"startTime": "2026-10-01T10:00:00Z", "publishTime": "2026-10-01T11:00:00Z", "generation": 999},
    ]
    chosen = select_available_forecasts(rows, datetime(2026, 10, 1, 10, tzinfo=timezone.utc))
    assert chosen["2026-10-01T10:00:00Z"]["generation"] == 120


def test_combines_wind_types_and_calculates_metrics():
    actuals = combine_actuals([
        {"startTime": "t", "psrType": "Wind Onshore", "quantity": 70},
        {"startTime": "t", "psrType": "Wind Offshore", "quantity": 30},
    ])
    result = compare({"t": {"generation": 110, "publishTime": "2026-10-01T00:00:00Z"}}, actuals)
    assert actuals == {"t": 100.0}
    assert result["mae"] == 10
    assert result["rmse"] == 10
