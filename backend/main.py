from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATA = Path(__file__).parent / "data"
DEFAULT_CUTOFF = "09:20"   # day-ahead gate closure (EPEX GB hourly auction)

app = FastAPI(title="Wind forecast API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ---- Load and clean data once, when the server starts ----
_a = pd.read_csv(DATA / "actuals.csv", parse_dates=["startTime"])
_a = _a.drop_duplicates("startTime")
_a = _a[(_a["startTime"] >= "2026-01-01") & (_a["startTime"] < "2026-02-01")]
_a["hour"] = _a["startTime"].dt.floor("h")
ACTUAL_HOURLY = _a.groupby("hour")["generation"].mean().rename("actual")

_f = pd.read_csv(DATA / "forecasts.csv", parse_dates=["startTime", "publishTime"])
FORECASTS = _f[(_f["startTime"] >= "2026-01-01") & (_f["startTime"] < "2026-02-01")].copy()


def parse_cutoff(text):
    try:
        h, m = text.split(":")
        return pd.Timedelta(hours=int(h), minutes=int(m))
    except Exception:
        raise HTTPException(400, "cutoff must look like 09:20")


def build(cutoff_text):
    """For every January hour: latest forecast published before the cutoff."""
    f = FORECASTS.copy()
    f["cutoff"] = f["startTime"].dt.floor("D") - pd.Timedelta(days=1) + parse_cutoff(cutoff_text)
    f = f[f["publishTime"] <= f["cutoff"]]
    f = f.sort_values("publishTime").drop_duplicates("startTime", keep="last")
    f = f.set_index("startTime")[["generation", "publishTime"]]
    f.columns = ["forecast", "forecast_published"]
    r = f.join(ACTUAL_HOURLY, how="left").sort_index()
    r["error"] = r["forecast"] - r["actual"]
    return r


def clean(df):
    return df.astype(object).where(df.notna(), None)


@app.get("/api/forecast")
def forecast(day: str, cutoff: str = DEFAULT_CUTOFF):
    r = build(cutoff)
    r = r[r.index.strftime("%Y-%m-%d") == day]
    if r.empty:
        raise HTTPException(404, "no data for that day (use 2026-01-01 to 2026-01-31)")
    out = r.reset_index()
    out["startTime"] = out["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["forecast_published"] = out["forecast_published"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"day": day, "cutoff": cutoff, "rows": clean(out).to_dict("records")}


@app.get("/api/errors")
def errors(cutoff: str = DEFAULT_CUTOFF):
    r = build(cutoff).dropna(subset=["actual"])
    r["abs_error"] = r["error"].abs()
    by_hour = r.groupby(r.index.hour).agg(bias=("error", "mean"), mae=("abs_error", "mean"))
    by_day = r.groupby(r.index.strftime("%Y-%m-%d"))["abs_error"].mean()
    return {
        "cutoff": cutoff,
        "hours": len(r),
        "bias": r["error"].mean(),
        "mae": r["abs_error"].mean(),
        "rmse": (r["error"] ** 2).mean() ** 0.5,
        "share_too_high": (r["error"] > 0).mean(),
        "margin_p90": r["error"].quantile(0.90),
        "margin_p95": r["error"].quantile(0.95),
        "by_hour": [{"hour": int(h), "bias": row.bias, "mae": row.mae}
                    for h, row in by_hour.iterrows()],
        "by_day": [{"day": d, "mae": v} for d, v in by_day.items()],
        
    }
from fastapi.staticfiles import StaticFiles

STATIC = Path(__file__).parent / "static"
if STATIC.exists():   # only inside Docker, where the built React files are copied
    app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
