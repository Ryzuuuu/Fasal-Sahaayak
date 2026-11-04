"""Combines the rule engine and the forecast into one farm report.

Advice is returned as codes, not sentences, so the frontend can show it in the
farmer's language.
"""

from __future__ import annotations

from . import fertilizer
from .forecast import ForecastStore
from .schemas import FarmInput

LOW_SEASON_RAINFALL_MM = 200
HIGH_SEASON_RAINFALL_MM = 1000


def _water_advice(rainfall_mm: float | None, irrigation: str) -> list[str]:
    codes = []
    if rainfall_mm is not None:
        if rainfall_mm < LOW_SEASON_RAINFALL_MM:
            codes.append("rain_low_rainfed_risk" if irrigation == "rainfed" else "rain_low_irrigate")
        elif rainfall_mm > HIGH_SEASON_RAINFALL_MM:
            codes.append("rain_high_drainage")
        else:
            codes.append("rain_moderate")
    if irrigation in ("drip", "sprinkler"):
        codes.append("efficient_irrigation")
    return codes


def analyze_farm(farm: FarmInput, store: ForecastStore) -> dict:
    soil = {
        "n": {"value": farm.nitrogen, "rating": fertilizer.rate_nutrient("n", farm.nitrogen)},
        "p": {"value": farm.phosphorus, "rating": fertilizer.rate_nutrient("p", farm.phosphorus)},
        "k": {"value": farm.potassium, "rating": fertilizer.rate_nutrient("k", farm.potassium)},
        "ph": None
        if farm.soil_ph is None
        else {"value": farm.soil_ph, "class": fertilizer.classify_ph(farm.soil_ph)},
        "sources": [fertilizer.RATING_SOURCE, fertilizer.PH_SOURCE],
    }
    climate = store.climate_for(farm.district, farm.season, farm.avg_temp_c, farm.rainfall_mm)
    rainfall = climate.get("rainfall_mm")

    return {
        "soil": soil,
        "fertilizer": fertilizer.recommend(farm.crop, farm.field_acres),
        "climate": climate,
        "yield_forecast": store.yield_forecast(
            farm.district, farm.crop, farm.season, climate, farm.field_acres
        ),
        "advice": {
            "water": _water_advice(rainfall, farm.irrigation),
            "pest": ["same_crop_repeat" if farm.previous_crop == farm.crop else "rotation_good"]
            if farm.previous_crop
            else ["rotation_general"],
        },
    }
