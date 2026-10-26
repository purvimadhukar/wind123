import pandas as pd

CUTOFF = pd.Timedelta(hours=9, minutes=20)   # decision time on the day before

a = pd.read_csv("actuals.csv", parse_dates=["startTime"])
f = pd.read_csv("forecasts.csv", parse_dates=["startTime", "publishTime"])

# ---- Rule 1 and 2: clean the actuals, make them hourly ----
a = a.drop_duplicates("startTime")
a = a[(a["startTime"] >= "2026-01-01") & (a["startTime"] < "2026-02-01")]
a["hour"] = a["startTime"].dt.floor("h")
actual_hourly = a.groupby("hour")["generation"].mean().rename("actual")

# ---- Rule 3: keep only forecasts published before the cutoff ----
f = f[(f["startTime"] >= "2026-01-01") & (f["startTime"] < "2026-02-01")]
delivery_day = f["startTime"].dt.floor("D")
f["cutoff"] = delivery_day - pd.Timedelta(days=1) + CUTOFF
f = f[f["publishTime"] <= f["cutoff"]]

# ---- Rule 4: for each hour, keep the most recent one ----
f = f.sort_values("publishTime").drop_duplicates("startTime", keep="last")
forecast_hourly = f.set_index("startTime")[["generation", "publishTime"]]
forecast_hourly.columns = ["forecast", "forecast_published"]

# ---- Compare ----
r = forecast_hourly.join(actual_hourly, how="inner")
r["error"] = r["forecast"] - r["actual"]
r.to_csv("results.csv")

print("hours in result:", len(r), "(expected 744)")
print("forecast published times used:")
print(r["forecast_published"].dt.strftime("%H:%M").value_counts().sort_index())
print("\nBias (average error, MW):", round(r["error"].mean()))
print("MAE (average size of error, MW):", round(r["error"].abs().mean()))
print("RMSE (punishes big misses, MW):", round((r["error"] ** 2).mean() ** 0.5))
print("\nFirst rows:")
print(r.head(5))