import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import './styles.css'

const iso = (date) => new Date(date).toISOString()
const now = new Date()
const yesterday = new Date(now - 24 * 60 * 60 * 1000)

function App() {
  const [start, setStart] = useState(yesterday.toISOString().slice(0, 10))
  const [end, setEnd] = useState(now.toISOString().slice(0, 10))
  const [cutoff, setCutoff] = useState(now.toISOString().slice(0, 16))
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function load(event) {
    event.preventDefault(); setLoading(true); setError(''); setData(null)
    try {
      const params = new URLSearchParams({ start: iso(`${start}T00:00:00Z`), end: iso(`${end}T23:59:59Z`), cutoff: iso(cutoff) })
      const response = await fetch(`http://localhost:8000/api/dashboard?${params}`)
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail || 'Unable to load Elexon data.')
      setData(body)
    } catch (err) { setError(err.message) } finally { setLoading(false) }
  }
  const chartPoints = data?.points.map(p => ({ ...p, label: new Date(p.time).toLocaleString([], { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' }) })) || []
  return <main>
    <header><p className="eyebrow">GRIDBRICKS · ELEXON INSIGHTS</p><h1>Wind forecast accuracy</h1><p>Compare GB wind forecasts with actual generation and backtest what was genuinely known at a selected publication cutoff.</p></header>
    <form onSubmit={load}>
      <label>From<input type="date" value={start} onChange={e => setStart(e.target.value)} required /></label>
      <label>To<input type="date" value={end} onChange={e => setEnd(e.target.value)} required /></label>
      <label>Forecast cutoff (local time)<input type="datetime-local" value={cutoff} onChange={e => setCutoff(e.target.value)} required /></label>
      <button disabled={loading}>{loading ? 'Loading…' : 'Analyse forecast'}</button>
    </form>
    {error && <div className="notice error">{error}</div>}
    {!data && !error && <div className="notice">Choose a historical window of up to 2 days, then analyse it.</div>}
    {data && <>
      <section className="cards"><article><span>MAE</span><strong>{data.mae?.toFixed(1) ?? '—'} MW</strong></article><article><span>RMSE</span><strong>{data.rmse?.toFixed(1) ?? '—'} MW</strong></article><article><span>Matched periods</span><strong>{data.matchedPeriods}</strong></article></section>
      <section className="chart"><h2>Forecast vs actual generation</h2><p>Each forecast is the latest revision published on or before {new Date(data.cutoff).toLocaleString()}.</p>
        {chartPoints.length ? <ResponsiveContainer width="100%" height={380}><LineChart data={chartPoints}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="label" minTickGap={40} /><YAxis unit=" MW" /><Tooltip /><Legend /><Line type="monotone" dataKey="forecast" stroke="#60a5fa" strokeWidth={2} dot={false} name="Forecast" /><Line type="monotone" dataKey="actual" stroke="#34d399" strokeWidth={2} dot={false} name="Actual" /></LineChart></ResponsiveContainer> : <div className="notice">No matched records returned for this range/cutoff.</div>}
      </section>
    </>}
  </main>
}
createRoot(document.getElementById('root')).render(<App />)
