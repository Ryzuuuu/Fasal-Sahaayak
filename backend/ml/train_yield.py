"""Train and evaluate the crop-yield forecast model.

The model forecasts a district's average yield for a crop and season from weather
and that district's recent yields. It is evaluated on a temporal holdout (train on
earlier seasons, test on later ones) and compared with a naive baseline: the mean
of the previous three seasons. All numbers quoted in the docs come from
models/metrics.json, which this script regenerates.

Usage (from backend/):  python -m ml.train_yield
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.catalog import CROPS
from app.forecast import BACKEND_DIR, CLIMATE_PATH, HISTORY_PATH, METRICS_PATH, MODEL_PATH

DATA_PATH = BACKEND_DIR / "data" / "raw" / "odisha_crop_production.csv"
WEATHER_PATH = BACKEND_DIR / "data" / "raw" / "nasa_power_monthly.csv"

SUPPORTED_CROPS = list(CROPS.values())
# Growing months per season, as (years after the crop year's start, month). In Indian crop
# statistics these labels describe the crop, not the weather at that time: "Winter" rice is
# the main monsoon crop harvested in early winter, and "Summer" rice is grown from January.
SEASON_MONTHS = {
    "Kharif": [(0, m) for m in range(6, 11)],
    "Autumn": [(0, m) for m in range(6, 10)],
    "Winter": [(0, m) for m in range(6, 13)],
    "Rabi": [(0, 11), (0, 12)] + [(1, m) for m in range(1, 5)],
    "Summer": [(1, m) for m in range(1, 6)],
    "Whole Year": [(0, m) for m in range(6, 13)] + [(1, m) for m in range(1, 6)],
}
KEY = ["District", "Crop", "Season"]
WEATHER = ["Avg_Temp", "Total_Precipitation"]
HISTORY = ["recent_yield", "last_yield"]
FEATURES = KEY + WEATHER + HISTORY
TARGET = "Yield"
HOLDOUT_START_YEAR = 2016
HISTORY_WINDOW = 3


def build_season_weather() -> pd.DataFrame:
    """Aggregate monthly weather into one row per district, crop year and season."""
    monthly = pd.read_csv(WEATHER_PATH).set_index(["District", "year", "month"])
    years = monthly.index.unique("year")
    rows = []
    for district in monthly.index.unique("District"):
        for start_year in range(int(years.min()), int(years.max())):
            for season, months in SEASON_MONTHS.items():
                index = [(district, start_year + offset, month) for offset, month in months]
                window = monthly.reindex(index).dropna()
                if len(window) == len(months):
                    rows.append(
                        {
                            "District": district,
                            "start_year": start_year,
                            "Season": season,
                            "Avg_Temp": window["temp_c"].mean(),
                            "Total_Precipitation": window["rain_mm"].sum(),
                        }
                    )
    return pd.DataFrame(rows)


def load_dataset(season_weather: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df["Season"] = df["Season"].str.strip()
    df["start_year"] = df["Year"].str[:4].astype(int)
    df = df[df["Crop"].isin(SUPPORTED_CROPS)]
    df = df[(df["Production Units"] == "Tonnes") & (df[TARGET] > 0)]
    df = df.merge(season_weather, on=["District", "start_year", "Season"], how="inner")
    df = df.dropna(subset=KEY + WEATHER + [TARGET])
    return df.drop_duplicates(KEY + ["start_year"]).sort_values("start_year").reset_index(drop=True)


def add_history_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add yields from earlier seasons only, so no future value leaks into a row."""
    yields = df.groupby(KEY)[TARGET]
    df = df.copy()
    df["recent_yield"] = yields.transform(
        lambda s: s.shift(1).rolling(HISTORY_WINDOW, min_periods=1).mean()
    )
    df["last_yield"] = yields.shift(1)
    return df.dropna(subset=HISTORY).reset_index(drop=True)


def build_model() -> TransformedTargetRegressor:
    preprocess = ColumnTransformer(
        [("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), KEY)],
        remainder="passthrough",
    )
    regressor = HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        l2_regularization=1.0,
        random_state=42,
    )
    # Yields span two orders of magnitude (sugarcane vs. pulses), so fit on a log scale.
    return TransformedTargetRegressor(
        regressor=Pipeline([("preprocess", preprocess), ("regressor", regressor)]),
        func=np.log1p,
        inverse_func=np.expm1,
    )


def score(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    y_pred = np.asarray(y_pred)
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 3),
        "mae_t_per_ha": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "median_ape_percent": round(float(np.median(np.abs(y_pred - y_true) / y_true) * 100), 1),
    }


def evaluate(df: pd.DataFrame) -> dict:
    train = df[df["start_year"] < HOLDOUT_START_YEAR]
    test = df[df["start_year"] >= HOLDOUT_START_YEAR]
    predictions = build_model().fit(train[FEATURES], train[TARGET]).predict(test[FEATURES])
    baseline = test["recent_yield"].to_numpy()
    not_sugarcane = (test["Crop"] != "Sugarcane").to_numpy()

    per_crop = {}
    for crop, rows in test.groupby("Crop"):
        mask = (test["Crop"] == crop).to_numpy()
        per_crop[crop] = {
            "test_rows": int(len(rows)),
            "model_mae_t_per_ha": round(float(mean_absolute_error(rows[TARGET], predictions[mask])), 3),
            "baseline_mae_t_per_ha": round(float(mean_absolute_error(rows[TARGET], baseline[mask])), 3),
        }

    return {
        "split": f"train: seasons before {HOLDOUT_START_YEAR}; test: {HOLDOUT_START_YEAR} onwards",
        "baseline": f"mean yield of the previous {HISTORY_WINDOW} seasons",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "model_all_crops": score(test[TARGET], predictions),
        "baseline_all_crops": score(test[TARGET], baseline),
        "model_excluding_sugarcane": score(test[TARGET][not_sugarcane], predictions[not_sugarcane]),
        "baseline_excluding_sugarcane": score(test[TARGET][not_sugarcane], baseline[not_sugarcane]),
        "per_crop": per_crop,
    }


def write_climate_normals(season_weather: pd.DataFrame) -> None:
    """Average each season's weather across years, per district."""
    normals = season_weather.groupby(["District", "Season"])[WEATHER].mean().round(2).reset_index()
    normals.to_csv(CLIMATE_PATH, index=False)


def write_yield_history(df: pd.DataFrame) -> None:
    """Store the latest known yields per key, used as inputs when forecasting."""
    rows = []
    for key, group in df.groupby(KEY):
        rows.append(
            {
                **dict(zip(KEY, key, strict=True)),
                "recent_yield": round(group[TARGET].tail(HISTORY_WINDOW).mean(), 4),
                "last_yield": round(group[TARGET].iloc[-1], 4),
                "last_year": group["Year"].iloc[-1],
                "seasons_observed": len(group),
            }
        )
    pd.DataFrame(rows).to_csv(HISTORY_PATH, index=False)


def main() -> None:
    season_weather = build_season_weather()
    raw = load_dataset(season_weather)
    df = add_history_features(raw)
    metrics = evaluate(df)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(build_model().fit(df[FEATURES], df[TARGET]), MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_climate_normals(season_weather)
    write_yield_history(raw)

    print(json.dumps(metrics, indent=2))
    print(f"Model size: {MODEL_PATH.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
