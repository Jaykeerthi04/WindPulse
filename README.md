# Gridbricks — Elexon wind forecast accuracy dashboard

A React + Vite dashboard backed by FastAPI. It compares GB wind forecasts with actual/estimated wind generation from Elexon and reports MAE and RMSE.

## The historical-selection rule

Backtests are not allowed to use a forecast revision that was published after the chosen cutoff. The backend receives the forecast evolution, groups records by `startTime`, discards each record whose `publishTime` is after the cutoff, then selects the most recent remaining publication. This avoids look-ahead bias.

Actuals are aggregated from the Elexon `AGWS` endpoint by summing Wind Onshore and Wind Offshore quantities for each settlement period.

## Run locally (no Docker required)

Open two terminals:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Select up to two days. The actual-wind endpoint permits seven days, while Elexon's forecast-evolution endpoint is queried once for every half-hour delivery period; this focused limit keeps the dashboard responsive and avoids aggressive API usage.

## Test

```powershell
cd backend
pytest
```

The tests cover cutoff-based revision selection, wind-type aggregation, MAE and RMSE.

## Docker (optional)

When Docker is available:

```powershell
docker compose up --build
```

The frontend is served on `http://localhost:5173`; the API on `http://localhost:8000`.

## Data source

Elexon BMRS Insights API: `WINDFOR` forecast evolution and `AGWS/B1630` actual or estimated wind/solar generation. See the Elexon API documentation and licence terms before commercial use.
