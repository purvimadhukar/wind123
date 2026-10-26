import pandas as pd

a = pd.read_csv("actuals.csv", parse_dates=["startTime", "publishTime"])
f = pd.read_csv("forecasts.csv", parse_dates=["startTime", "publishTime"])

print("actuals: duplicate startTime rows:", a.duplicated("startTime").sum())
print("actuals: unique slots:", a["startTime"].nunique())
print("actuals: first/last startTime:", a["startTime"].min(), a["startTime"].max())
print("actuals: minutes in startTime:", sorted(a["startTime"].dt.minute.unique()))

print("forecasts: minutes in startTime:", sorted(f["startTime"].dt.minute.unique()))
print("forecasts: published AFTER target:", (f["publishTime"] > f["startTime"]).sum())
print("forecasts: duplicate (startTime, publishTime):", f.duplicated(["startTime", "publishTime"]).sum())
print("forecasts: publish times (hh:mm) and counts:")
print(f["publishTime"].dt.strftime("%H:%M").value_counts().sort_index())