# 🌾 Fasal Sahaayak

**Smart India Hackathon 2025 submission.** A multilingual crop-advisory web app for farmers. A React interface collects farm details (crop, location, field size, soil nutrients and more) and a Flask API returns advice on soil, water, pests and farm management, including a machine-learning **fertilizer recommendation**.

## How it works

```
React + Vite UI  ──POST /analyze──▶  Flask API (SERVER/main.py)
 (UI/, port 5173)                      ├─ loads RandomForest models (.joblib) at startup
                                       ├─ fertilizer recommender → recommended fertilizer
                                       └─ builds soil / water / pest / management advice
```

- **Frontend (`UI/`)**: React 19 + Vite, Tailwind CSS (via CDN), Axios. A farm-input form, an advice panel, a language switcher (**English, Hindi, Odia**) and a chatbot-style sidebar.
- **Backend (`SERVER/`)**: Flask + Flask-CORS, scikit-learn, pandas, joblib. One endpoint, `POST /analyze`, on port 5000.
- **Models (trained in the notebooks in `SERVER/`)**: a `RandomForestClassifier` for fertilizer recommendation (trained on `data_core.csv`, a crop and soil-nutrient dataset) and a `RandomForestRegressor` for crop yield (trained on Odisha crop-production data merged with weather and nutrient features: `odisha_final_data.csv`). Data sources are listed in `SERVER/Sources_data.txt`.

## Run it

You need **Python 3.10+** and **Node.js 18+**.

**1. Start the API**

```bash
cd SERVER
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt     # on macOS/Linux you may need to drop the Windows-only pywin32 line first
python main.py                      # http://127.0.0.1:5000
```

**2. Start the UI** (new terminal)

```bash
cd UI
npm install
npm run dev                         # http://localhost:5173
```

Fill in the form and press the advice button. The UI calls `http://localhost:5000/analyze`.

> The location field expects the format **`Village, District`**. The API reads the district from the part after the comma.

## Current status (prototype)

Being upfront about what is and isn't wired up yet:

- ✅ The fertilizer recommendation comes from the trained Random Forest model.
- ⚠️ The yield model is trained and loaded, and a prediction helper exists, but `/analyze` does not use it in its response yet.
- ⚠️ Climate inputs (average temperature and rainfall) are currently fixed placeholder values; live NASA POWER lookups are not implemented in the API yet. Only a few districts have coordinates configured.
- ⚠️ The soil, water, pest and management text is template-based, filled in with your inputs and the model's fertilizer pick.
- ⚠️ The chatbot sidebar is a UI placeholder (its input is disabled).

## Repository layout

```
SERVER/   Flask API, trained models (*.joblib), datasets (*.csv), training notebooks, NASA data merge script
UI/       React + Vite frontend (components, i18n translations, API service)
```

## Tech stack

Python · Flask · scikit-learn (Random Forest) · pandas · joblib · React 19 · Vite · Tailwind CSS · Axios · Jupyter
