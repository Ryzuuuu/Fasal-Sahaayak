"""Soil-test ratings and fertilizer quantities from cited agronomic references.

This is a transparent rule engine, not a trained model. docs/MODEL_DECISIONS.md
explains why. A crop only gets a dose if it has a citable source; other crops
return "no_verified_dose" rather than an invented number.
"""

from __future__ import annotations

ACRES_TO_HECTARES = 0.404686

# Nutrient content of common fertilizers, as mass fractions.
UREA_N = 0.46
DAP_N = 0.18
DAP_P2O5 = 0.46
MOP_K2O = 0.60

# Available-nutrient rating bands (kg/ha): (low below, high above).
# Source: ICAR-Indian Institute of Soil Science, Harit Dhara e-magazine, vol. 4(1).
RATING_BANDS = {"n": (280, 560), "p": (10, 25), "k": (120, 280)}
RATING_SOURCE = {
    "title": "ICAR-IISS Harit Dhara: soil fertility rating table",
    "url": "https://iiss.icar.gov.in/eMagazine/v4i1/12.pdf",
}

# Soil pH classes. Source: TNAU Agritech soil rating chart.
PH_ACIDIC_BELOW = 6.0
PH_ALKALINE_ABOVE = 8.5
PH_SOURCE = {
    "title": "TNAU Agritech: soil rating chart",
    "url": "https://agritech.tnau.ac.in/agriculture/agri_soil_rating.html",
}

# Reference doses as kg/ha of N, P2O5 and K2O.
REFERENCE_DOSES = {
    "rice": {
        "n": 80,
        "p2o5": 40,
        "k2o": 40,
        "source": {
            "title": (
                "Sharma et al. (2019), Field Crops Research 241:107578. Blanket "
                "recommendation benchmark of 80 N, 17 P, 33 K kg/ha, shown here as rounded oxides."
            ),
            "url": "https://agris.fao.org/search/es/records/6798e6e4d6a63682f0462dc6",
        },
    },
    "maize": {
        "n": 120,
        "p2o5": 60,
        "k2o": 60,
        "source": {
            "title": "Present Status and Future Prospects of Maize Cultivation in South Odisha",
            "url": (
                "https://www.researchgate.net/publication/340545923_Present_Status_and_"
                "Future_Prospects_of_Maize_Cultivation_in_South_Odisha"
            ),
        },
    },
}


def rate_nutrient(nutrient: str, value: float) -> str:
    low_below, high_above = RATING_BANDS[nutrient]
    if value < low_below:
        return "low"
    return "high" if value > high_above else "medium"


def classify_ph(value: float) -> str:
    if value < PH_ACIDIC_BELOW:
        return "acidic"
    return "alkaline" if value > PH_ALKALINE_ABOVE else "normal"


def products_for_dose(n: float, p2o5: float, k2o: float) -> dict[str, float]:
    """Convert a nutrient dose to kg of DAP, urea and MOP, per hectare.

    DAP supplies all the P2O5 and some N, urea supplies the remaining N, and MOP
    supplies the K2O.
    """
    dap = p2o5 / DAP_P2O5
    urea = max(n - dap * DAP_N, 0) / UREA_N
    mop = k2o / MOP_K2O
    return {"urea": round(urea, 1), "dap": round(dap, 1), "mop": round(mop, 1)}


def recommend(crop: str, field_acres: float) -> dict:
    dose = REFERENCE_DOSES.get(crop)
    if dose is None:
        return {"status": "no_verified_dose"}

    per_hectare = products_for_dose(dose["n"], dose["p2o5"], dose["k2o"])
    hectares = field_acres * ACRES_TO_HECTARES
    return {
        "status": "available",
        "dose_kg_per_ha": {"n": dose["n"], "p2o5": dose["p2o5"], "k2o": dose["k2o"]},
        "products_kg_per_ha": per_hectare,
        "products_kg_for_field": {name: round(kg * hectares, 1) for name, kg in per_hectare.items()},
        "source": dose["source"],
    }
