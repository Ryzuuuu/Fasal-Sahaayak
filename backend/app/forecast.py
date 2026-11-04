"""Loads the trained yield model and the climate and history tables it depends on."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from .catalog import CROPS, SEASONS
from .fertilizer import ACRES_TO_HECTARES

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BACKEND_DIR / "models" / "yield_model.joblib"
METRICS_PATH = BACKEND_DIR / "models" / "metrics.json"
CLIMATE_PATH = BACKEND_DIR / "data" / "climate_normals.csv"
HISTORY_PATH = BACKEND_DIR / "data" / "yield_history.csv"
MIN_SEASONS_FOR_FORECAST = 3
EARLIEST_USABLE_RECORD_YEAR = 2014  # The data ends in 2019-20; older history is too stale to forecast from.
NASA_ATTRIBUTION = "NASA POWER season averages, 1997-2020"


def _usable(history: dict | None) -> bool:
    return (
        history is not None
        and history["seasons_observed"] >= MIN_SEASONS_FOR_FORECAST
        and int(history["last_year"][:4]) >= EARLIEST_USABLE_RECORD_YEAR
    )


@dataclass(frozen=True)
class ForecastStore:
    model: object
    climate: dict
    history: dict
    metrics: dict

    @classmethod
    def load(cls) -> ForecastStore:
        climate = pd.read_csv(CLIMATE_PATH)
        history = pd.read_csv(HISTORY_PATH)
        return cls(
            model=joblib.load(MODEL_PATH),
            climate=climate.set_index(["District", "Season"]).to_dict("index"),
            history=history.set_index(["District", "Crop", "Season"]).to_dict("index"),
            metrics=json.loads(METRICS_PATH.read_text(encoding="utf-8")),
        )

    def climate_for(self, district: str, season: str, temp_c: float | None, rain_mm: float | None) -> dict:
        normal = self.climate.get((district, SEASONS[season]))
        if normal is None and (temp_c is None or rain_mm is None):
            return {"status": "unavailable"}
        overridden = temp_c is not None or rain_mm is not None
        return {
            "status": "available",
            "avg_temp_c": temp_c if temp_c is not None else normal["Avg_Temp"],
            "rainfall_mm": rain_mm if rain_mm is not None else normal["Total_Precipitation"],
            "source": "user_input" if overridden else NASA_ATTRIBUTION,
        }

    def yield_forecast(self, district: str, crop: str, season: str, climate: dict, acres: float) -> dict:
        crop_name, season_name = CROPS[crop], SEASONS[season]
        history = self.history.get((district, crop_name, season_name))
        if not _usable(history) or climate["status"] != "available":
            return {
                "status": "insufficient_history",
                "seasons_with_recent_data": [
                    season_id
                    for season_id, name in SEASONS.items()
                    if _usable(self.history.get((district, crop_name, name)))
                ],
            }

        features = pd.DataFrame(
            [
                {
                    "District": district,
                    "Crop": crop_name,
                    "Season": season_name,
                    "Avg_Temp": climate["avg_temp_c"],
                    "Total_Precipitation": climate["rainfall_mm"],
                    "recent_yield": history["recent_yield"],
                    "last_yield": history["last_yield"],
                }
            ]
        )
        predicted = max(float(self.model.predict(features)[0]), 0.0)
        typical_error = self.metrics["per_crop"][crop_name]["model_mae_t_per_ha"]
        return {
            "status": "available",
            "t_per_ha": round(predicted, 2),
            "low_t_per_ha": round(max(predicted - typical_error, 0.0), 2),
            "high_t_per_ha": round(predicted + typical_error, 2),
            "recent_average_t_per_ha": round(history["recent_yield"], 2),
            "last_recorded_season": history["last_year"],
            "total_tonnes_for_field": round(predicted * acres * ACRES_TO_HECTARES, 2),
        }
