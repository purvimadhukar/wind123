import pandas as pd

r = pd.read_csv("results.csv", parse_dates=["startTime"]).sort_values("startTime")
r["abs_error"] = r["error"].abs()

# 1. Which hours of the day are worst?
r["hour_of_day"] = r["startTime"].dt.hour
print("1) ERROR BY HOUR OF DAY")
print(r.groupby("hour_of_day")["error"].agg(bias="mean").round(0).join(
      r.groupby("hour_of_day")["abs_error"].mean().round(0).rename("MAE")))

# 2. Which days are worst?
r["day"] = r["startTime"].dt.date
daily = r.groupby("day")["abs_error"].mean().round(0).sort_values(ascending=False)
print("\n2) 5 WORST DAYS (average miss, MW)")
print(daily.head(5))
print("5 BEST DAYS")
print(daily.tail(5))

# 3. Safety margin
print("\n3) SAFETY MARGIN")
print("90% of hours, the forecast was too high by LESS than",
      round(r["error"].quantile(0.90)), "MW")
print("95% of hours, the forecast was too high by LESS than",
      round(r["error"].quantile(0.95)), "MW")
print("Share of hours where forecast was too high:",
      round((r["error"] > 0).mean() * 100), "%")