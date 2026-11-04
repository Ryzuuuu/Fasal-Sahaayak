"""Download monthly weather for each Odisha district from NASA POWER (free, no key).

Saves data/raw/nasa_power_monthly.csv, which train_yield.py aggregates into growing
seasons. Monthly values let each season use its own months, including seasons that
cross a calendar year.

Usage (from backend/):  python -m ml.fetch_nasa_weather
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "nasa_power_monthly.csv"
API_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
START_YEAR, END_YEAR = 1997, 2020
SECONDS_BETWEEN_REQUESTS = 0.5
MISSING_VALUE = -999

DISTRICT_COORDINATES = {
    "ANUGUL": (20.83, 85.09), "BALANGIR": (20.71, 83.48), "BALESHWAR": (21.49, 86.92),
    "BARGARH": (21.33, 83.62), "BHADRAK": (21.06, 86.50), "BOUDH": (20.84, 84.32),
    "CUTTACK": (20.46, 85.88), "DEOGARH": (21.53, 84.73), "DHENKANAL": (20.66, 85.59),
    "GAJAPATI": (19.08, 84.08), "GANJAM": (19.38, 85.05), "JAGATSINGHAPUR": (20.26, 86.17),
    "JAJAPUR": (20.84, 86.33), "JHARSUGUDA": (21.87, 84.03), "KALAHANDI": (19.85, 83.21),
    "KANDHAMAL": (20.43, 84.23), "KENDRAPARA": (20.50, 86.42), "KENDUJHAR": (21.63, 85.58),
    "KHORDHA": (20.18, 85.62), "KORAPUT": (18.82, 82.72), "MALKANGIRI": (18.35, 81.89),
    "MAYURBHANJ": (21.93, 86.75), "NABARANGPUR": (19.23, 82.55), "NAYAGARH": (20.13, 85.10),
    "NUAPADA": (20.83, 82.66), "PURI": (19.81, 85.83), "RAYAGADA": (19.17, 83.42),
    "SAMBALPUR": (21.47, 83.97), "SONEPUR": (20.85, 83.90), "SUNDARGARH": (22.12, 84.03),
}


def fetch_district(district: str, latitude: float, longitude: float) -> pd.DataFrame:
    response = requests.get(
        API_URL,
        params={
            "parameters": "T2M,PRECTOTCORR_SUM",
            "community": "AG",
            "latitude": latitude,
            "longitude": longitude,
            "start": START_YEAR,
            "end": END_YEAR,
            "format": "JSON",
        },
        timeout=60,
    )
    response.raise_for_status()
    parameters = response.json()["properties"]["parameter"]

    rows = []
    for period, temperature in parameters["T2M"].items():
        year, month = int(period[:4]), int(period[4:])
        rainfall = parameters["PRECTOTCORR_SUM"][period]
        # Keys with month 13 are annual summaries, not months.
        if month <= 12 and MISSING_VALUE not in (temperature, rainfall):
            rows.append(
                {
                    "District": district,
                    "year": year,
                    "month": month,
                    "temp_c": temperature,
                    "rain_mm": rainfall,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    frames = []
    for district, (latitude, longitude) in DISTRICT_COORDINATES.items():
        frames.append(fetch_district(district, latitude, longitude))
        print(f"Fetched {district}")
        time.sleep(SECONDS_BETWEEN_REQUESTS)
    pd.concat(frames).to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
