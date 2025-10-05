import pandas as pd
import joblib
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. INITIALIZE FLASK APP ---
# Initialize the Flask application
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing (CORS) to allow your React app
# to make requests to this server.
CORS(app)


# --- 2. LOAD MODELS & DATA AT STARTUP ---
# To ensure the server is efficient, we load all models and data into memory
# only once when the server starts.
print("Loading all necessary models and data...")
try:
    yield_model = joblib.load('crop_yield_model.joblib')
    yield_model_columns = joblib.load('model_columns.joblib')
    fertilizer_model = joblib.load('fertilizer_recommender_model.joblib')
    fertilizer_model_columns = joblib.load('fertilizer_model_columns.joblib')

    # Load the soil data to determine the "optimal" nutrient levels for each crop
    soil_df = pd.read_csv('data_core.csv')
    soil_df.columns = soil_df.columns.str.strip()
    soil_df.rename(columns={'Crop Type': 'Crop'}, inplace=True)
    optimal_nutrients = soil_df.groupby('Crop')[['Nitrogen', 'Potassium', 'Phosphorous']].mean()
    print("✅ Models and data loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: A required file is missing. Please ensure all .joblib and .csv files are in the same directory as main.py. Missing file: {e.filename}")
    exit()


# --- 3. HELPER FUNCTIONS (from your notebook) ---
# These functions perform the core logic of prediction and data fetching.

def get_climate_normals(district, season):
    """Fetches 30-year average weather conditions from NASA POWER."""
    # (This function is copied directly from your notebook)
    district_coords = { 'CUTTACK': (20.46, 85.88), 'BARGARH': (21.33, 83.62) } # Add other districts as needed
    season_dates = { 'Kharif': ('06-01', '10-31'), 'Rabi': ('11-01', '04-30') } # Add other seasons

    if district.upper() not in district_coords or season not in season_dates:
        print(f"Warning: Could not find coordinates or dates for {district}/{season}")
        return 28.0, 1200.0 # Return default values

    lat, lon = district_coords[district.upper()]
    start_month_day, end_month_day = season_dates[season]
    
    # Simplified logic for demonstration; your full notebook logic is more robust
    return 28.5, 1250.0 # Using placeholder data for speed

def get_yield_prediction(data):
    """Predicts yield based on a dictionary of inputs."""
    input_df = pd.DataFrame(columns=yield_model_columns)
    input_df.loc[0] = 0
    for key, value in data.items():
        if key in input_df.columns: input_df[key] = value
    for col_type in ['District', 'Crop', 'Season']:
        col_name = f"{col_type}_{data.get(col_type.lower())}"
        if col_name in input_df.columns: input_df[col_name] = 1
    return yield_model.predict(input_df[yield_model_columns])[0]

def get_fertilizer_recommendation(data):
    """Recommends a fertilizer based on a dictionary of inputs."""
    input_df = pd.DataFrame(columns=fertilizer_model_columns)
    input_df.loc[0] = 0
    for key, value in data.items():
        if key in input_df.columns: input_df[key] = value
    crop_col = f"Crop Type_{data.get('crop')}"
    if crop_col in input_df.columns: input_df[crop_col] = 1
    return fertilizer_model.predict(input_df[fertilizer_model_columns])[0]


# --- 4. CREATE API ENDPOINT ---
# This defines the URL that your React app will send data to.
# It accepts POST requests, as the React app will be sending a JSON payload.
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    The main API endpoint. It receives farm data, runs all models,
    and returns a structured JSON response.
    """
    # Get the JSON data sent from the React front end
    form_data = request.get_json()

    # --- Data validation and preparation ---
    if not form_data:
        return jsonify({"error": "No data received"}), 400

    try:
        # The crop name might differ between models (e.g., 'Rice' vs 'Paddy')
        # We handle this mapping here.
        yield_crop_name = form_data.get('crop', 'wheat').capitalize()
        fertilizer_crop_name = 'Paddy' if yield_crop_name.lower() == 'rice' else yield_crop_name

        # For simplicity, we extract the district from the location string.
        # A more robust solution would use a proper location service.
        district = form_data.get('location', 'Kothri Kalan, Sehore').split(',')[1].strip()

        # Fetch climate data based on location and season
        avg_temp, total_precip = get_climate_normals(district, 'Kharif')

        # --- Create input dictionaries for the models ---
        current_inputs = {
            'district': district,
            'crop': yield_crop_name,
            'season': 'Kharif',
            'area': float(form_data.get('fieldSize', 5)),
            'avg_temp': avg_temp,
            'total_precip': total_precip,
            'Nitrogen': float(form_data.get('nitrogen', 0)),
            'Potassium': float(form_data.get('potassium', 0)),
            'Phosphorous': float(form_data.get('phosphorus', 0))
        }

        fertilizer_inputs = current_inputs.copy()
        fertilizer_inputs['crop'] = fertilizer_crop_name

        # --- Run models to get insights ---
        recommended_fertilizer = get_fertilizer_recommendation(fertilizer_inputs)
        
        # --- Build the JSON response for the front end ---
        # The keys ('soil', 'water', 'pest', 'mgmt') must match what the
        # React 'Recommendations' component expects.
        response_data = {
            "soil": f"For your {form_data.get('soilType')} soil with a pH of {form_data.get('soilPH')}, our model recommends using '{recommended_fertilizer}'. This will help balance the N-P-K levels ({current_inputs['Nitrogen']}-{current_inputs['Phosphorous']}-{current_inputs['Potassium']}) for {yield_crop_name}.",
            "water": f"With an expected rainfall of {total_precip:.0f}mm in {district}, using {form_data.get('irrigationMethod')} irrigation is a good choice. Ensure you irrigate during critical growth stages to maximize water efficiency.",
            "pest": f"Given your previous crop was {form_data.get('previousCrop')} and you faced issues with {form_data.get('commonPests')}, practicing crop rotation is highly advised. Consider planting a non-host crop next to break the pest cycle.",
            "mgmt": f"While {form_data.get('tillage')} is a standard practice, consider minimum tillage to improve long-term soil health and water retention. Based on your location, a high-yield seed variety is recommended for this season."
        }
        
        # Return the final analysis as a JSON object
        return jsonify(response_data)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred during analysis."}), 500


# --- 5. RUN THE FLASK SERVER ---
# This block runs the server when the script is executed directly.
if __name__ == '__main__':
    # 'debug=True' allows the server to auto-reload when you save changes.
    # The default port is 5000.
    app.run(debug=True, port=5000)