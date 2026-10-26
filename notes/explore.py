import requests
import pandas as pd

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

def fetch(dataset, start, end, extra=None):
    """Download data for one dataset between two dates, 2 days at a time."""
    pieces = []
    days = pd.date_range(start, end, freq="2D")
    for s in days:
        e = min(s + pd.Timedelta(days=2), pd.Timestamp(end))
        params = {
            "publishDateTimeFrom": s.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": e.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "format": "json",
        }
        if extra:
            params.update(extra)
        r = requests.get(f"{BASE}/{dataset}/stream", params=params, timeout=60)
        if r.status_code != 200:
            print("PROBLEM:", dataset, s.date(), r.status_code, r.text[:200])
            continue
        pieces.append(pd.DataFrame(r.json()))
        print("downloaded", dataset, s.date(), len(pieces[-1]), "rows")
    return pd.concat(pieces, ignore_index=True)

# 1. Actual wind generation for January 2026
actuals = fetch("FUELHH", "2026-01-01", "2026-02-01", extra={"fuelType": "WIND"})
actuals.to_csv("actuals.csv", index=False)

# 2. Wind forecasts published from 31 Dec 2025 to end of January 2026
forecasts = fetch("WINDFOR", "2025-12-31", "2026-02-01")
forecasts.to_csv("forecasts.csv", index=False)

# 3. Print facts about what we got
print("\n===== ACTUALS =====")
print(actuals.columns.tolist())
print(actuals.head(3))
print("total rows:", len(actuals))

print("\n===== FORECASTS =====")
print(forecasts.columns.tolist())
print(forecasts.head(3))
print("total rows:", len(forecasts))

forecasts["startTime"] = pd.to_datetime(forecasts["startTime"])
forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"])
hours_ahead = (forecasts["startTime"] - forecasts["publishTime"]).dt.total_seconds() / 3600
print("forecast versions per target slot:")
print(forecasts.groupby("startTime").size().describe())
print("hours ahead (target minus publish):")
print(hours_ahead.describe())
print("publish hours (UTC):", sorted(forecasts["publishTime"].dt.hour.unique()))