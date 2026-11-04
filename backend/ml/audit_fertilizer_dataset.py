"""Show why the Kaggle fertilizer dataset cannot train a useful classifier.

The first prototype trained a Random Forest on this dataset. This script measures
it with 5-fold cross-validation against chance, using every available feature and
two algorithms. Accuracy stays at chance level, which means the labels carry no
learnable relationship to the inputs. See docs/MODEL_DECISIONS.md.

Usage (from backend/):  python -m ml.audit_fertilizer_dataset
"""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import cross_val_score

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "kaggle_crop_soil_fertilizer.csv"
LABEL = "Fertilizer Name"
PROTOTYPE_FEATURES = ["Nitrogen", "Potassium", "Phosphorous", "Crop Type"]


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    y = df[LABEL]
    print(f"Rows: {len(df)}  Classes: {y.nunique()}  Chance accuracy: {1 / y.nunique():.4f}")

    feature_sets = {
        "prototype features": pd.get_dummies(df[PROTOTYPE_FEATURES], drop_first=True),
        "all features": pd.get_dummies(df.drop(columns=LABEL), drop_first=True),
    }
    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=0, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=0),
    }
    for feature_name, X in feature_sets.items():
        for model_name, model in models.items():
            accuracy = cross_val_score(model, X.astype(float), y, cv=5).mean()
            print(f"{feature_name:<20} {model_name:<22} accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()
