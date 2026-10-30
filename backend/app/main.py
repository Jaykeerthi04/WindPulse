import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .metrics import combine_actuals, compare, parse_time, select_available_forecasts

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
app = FastAPI(title="Gridbricks Wind Forecast API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


async def fetch(path: str, params: dict[str, str]) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BASE_URL}{path}", params=params)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", payload) if isinstance(payload, dict) else payload


async def fetch_forecast_evolution(start: datetime, end: datetime) -> list[dict[str, Any]]:
    """The Elexon evolution endpoint takes one delivery `startTime` per call."""
    targets = []
    cursor = start
    while cursor < end:
        targets.append(cursor)
        cursor += timedelta(minutes=30)
    semaphore = asyncio.Semaphore(8)

    async def get_target(target: datetime) -> list[dict[str, Any]]:
        async with semaphore:
            return await fetch("/forecast/generation/wind/evolution", {"startTime": target.isoformat()})
    batches = await asyncio.gather(*(get_target(target) for target in targets))
    return [row for batch in batches for row in batch]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
async def dashboard(
    start: datetime = Query(..., description="UTC start"),
    end: datetime = Query(..., description="UTC end"),
    cutoff: datetime | None = Query(None, description="Latest allowed forecast publication UTC"),
):
    if end <= start or end - start > timedelta(days=2):
        raise HTTPException(400, "Choose a period from 30 minutes up to 2 days.")
    cutoff = cutoff or end
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    # Evolution contains forecast revisions. We deliberately request publish data
    # through the cutoff, then select the last revision known at that cutoff.
    try:
        forecasts = await fetch_forecast_evolution(start, end)
        actual_rows = await fetch("/generation/actual/per-type/wind-and-solar", {"from": start.isoformat(), "to": end.isoformat()})
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Elexon data request failed: {exc}") from exc
    selected = select_available_forecasts(forecasts, cutoff)
    result = compare(selected, combine_actuals(actual_rows))
    return {**result, "start": start, "end": end, "cutoff": cutoff,
            "selectedForecasts": len(selected), "matchedPeriods": len(result["points"])}
