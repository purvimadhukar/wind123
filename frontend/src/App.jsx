import { useEffect, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";

const API = import.meta.env.VITE_API_URL ?? "";
const DAYS = Array.from({ length: 31 }, (_, i) => `2026-01-${String(i + 1).padStart(2, "0")}`);

const card = { background: "white", borderRadius: 8, padding: 16, boxShadow: "0 1px 3px rgba(0,0,0,.1)" };

function Stat({ label, value, note }) {
  return (
    <div style={{ ...card, flex: 1, minWidth: 180 }}>
      <div style={{ fontSize: 13, color: "#5b6878" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 600 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#5b6878" }}>{note}</div>
    </div>
  );
}

export default function App() {
  const [cutoff, setCutoff] = useState("09:20");
  const [day, setDay] = useState("2026-01-15");
  const [errors, setErrors] = useState(null);
  const [rows, setRows] = useState([]);
  const [problem, setProblem] = useState("");

  // Whenever the cutoff changes, ask the backend for the error numbers
  useEffect(() => {
    fetch(`${API}/api/errors?cutoff=${cutoff}`)
      .then((r) => r.json())
      .then(setErrors)
      .catch(() => setProblem("Cannot reach the backend. Is it running?"));
  }, [cutoff]);

  // Whenever the day or cutoff changes, ask for that day's forecast
  useEffect(() => {
    fetch(`${API}/api/forecast?day=${day}&cutoff=${cutoff}`)
      .then((r) => r.json())
      .then((d) =>
        setRows(d.rows.map((x) => ({ ...x, time: x.startTime.slice(11, 16) })))
      )
      .catch(() => setProblem("Cannot reach the backend. Is it running?"));
  }, [day, cutoff]);

  const mw = (n) => `${Math.round(n).toLocaleString()} MW`;

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
      <h1>UK Wind Forecast Accuracy: January 2026</h1>
      <p style={{ color: "#5b6878" }}>
        For each hour, this shows the latest wind forecast available before the day-ahead
        deadline, and how far it was from what actually happened.
      </p>

      {problem && <p style={{ color: "crimson" }}>{problem}</p>}

      <label>
        Decision cutoff (day before):{" "}
        <select value={cutoff} onChange={(e) => setCutoff(e.target.value)}>
          <option value="09:20">09:20 (EPEX GB auction)</option>
          <option value="09:50">09:50 (N2EX auction)</option>
        </select>
      </label>

      {errors && (
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "16px 0" }}>
          <Stat label="Bias" value={mw(errors.bias)} note="Forecast minus actual, on average (positive = too high)" />
          <Stat label="MAE" value={mw(errors.mae)} note="Typical size of a miss" />
          <Stat label="RMSE" value={mw(errors.rmse)} note="Like MAE, but big misses count more" />
          <Stat label="90% safety margin" value={mw(errors.margin_p90)} note="Forecast was too high by less than this in 90% of hours" />
        </div>
      )}

      <div style={{ ...card, marginBottom: 16 }}>
        <h3>Forecast vs actual for one day</h3>
        <label>
          Delivery day:{" "}
          <select value={day} onChange={(e) => setDay(e.target.value)}>
            {DAYS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>
        <div style={{ height: 320, marginTop: 12 }}>
          <ResponsiveContainer>
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis unit=" MW" width={80} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="forecast" stroke="#2f6fed" dot={false} name="Forecast" />
              <Line type="monotone" dataKey="actual" stroke="#e8590c" dot={false} name="Actual" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {errors && (
        <div style={card}>
          <h3>Average forecast error by hour of day</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={errors.by_hour}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis unit=" MW" width={80} />
                <Tooltip formatter={(v) => `${Math.round(v)} MW`} />
                <Bar dataKey="bias" fill="#2f6fed" name="Bias (forecast minus actual)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}