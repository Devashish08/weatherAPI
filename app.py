# app.py
from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
from open_meteo_client import fetch_weather_data
from gcs_client import upload_to_gcs, list_gcs_files, get_gcs_file_content

app = Flask(__name__)

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

def generate_filename(latitude, longitude, start_date_str, end_date_str):
    """Generates a standardized filename for the weather data."""
    start_date_fn = start_date_str.replace("-", "")
    end_date_fn = end_date_str.replace("-", "")
    lat_str = f"{latitude:.2f}".replace('.', '_')
    lon_str = f"{longitude:.2f}".replace('.', '_')
    return f"weather_lat{lat_str}_lon{lon_str}_from{start_date_fn}_to{end_date_fn}.json"

def validate_date_format(date_str):
    """Validates if the date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# --- API Endpoints ---

@app.route('/')
def index():
    """A simple index route to check if the app is running."""
    return jsonify({"message": "Welcome to the Weather Data Service API!"}), 200

@app.route('/store-weather-data', methods=['POST'])
def store_weather_data_endpoint():
    """
    Endpoint to fetch historical weather data and store it in GCS.
    Expects a JSON body with: latitude, longitude, start_date, end_date.
    """
    if not GCS_BUCKET_NAME:
        app.logger.error("GCS_BUCKET_NAME not configured on the server.")
        return jsonify({"error": "Server configuration error: GCS bucket not set."}), 500

    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"error": "Invalid request: No JSON payload received."}), 400
    except Exception as e: # Catches errors if request body is not valid JSON
        app.logger.error(f"Failed to parse request JSON: {e}")
        return jsonify({"error": "Invalid request: Malformed JSON."}), 400

    latitude = req_data.get('latitude')
    longitude = req_data.get('longitude')
    start_date = req_data.get('start_date')
    end_date = req_data.get('end_date')

    required_params = {"latitude": latitude, "longitude": longitude, "start_date": start_date, "end_date": end_date}
    missing_params = [key for key, value in required_params.items() if value is None]
    if missing_params:
        return jsonify({"error": f"Missing parameters: {', '.join(missing_params)}"}), 400

    if not (isinstance(latitude, (int, float)) and isinstance(longitude, (int, float))):
        return jsonify({"error": "Invalid data type for latitude or longitude. Must be float or integer."}), 400

    if not (isinstance(start_date, str) and validate_date_format(start_date) and
            isinstance(end_date, str) and validate_date_format(end_date)):
        return jsonify({"error": "Invalid date format for start_date or end_date. Use YYYY-MM-DD."}), 400

    app.logger.info(f"Fetching weather data for {latitude}, {longitude} from {start_date} to {end_date}")
    weather_api_data = fetch_weather_data(latitude, longitude, start_date, end_date)

    if weather_api_data is None:
        app.logger.error("Failed to fetch weather data from Open-Meteo.")
        return jsonify({"error": "Failed to fetch weather data from external API."}), 502 # Bad Gateway

    file_name = generate_filename(latitude, longitude, start_date, end_date)
    weather_data_json_string = json.dumps(weather_api_data, indent=2) # Pretty print for stored JSON

    app.logger.info(f"Uploading data to GCS: gs://{GCS_BUCKET_NAME}/{file_name}")
    if upload_to_gcs(GCS_BUCKET_NAME, file_name, weather_data_json_string):
        return jsonify({
            "message": "Weather data fetched and stored successfully.",
            "file_name": file_name,
            "gcs_path": f"gs://{GCS_BUCKET_NAME}/{file_name}"
        }), 201 # 201 Created
    else:
        app.logger.error(f"Failed to upload data to GCS bucket '{GCS_BUCKET_NAME}'.")
        return jsonify({"error": "Failed to store weather data in GCS."}), 500


@app.route('/list-weather-files', methods=['GET'])
def list_weather_files_endpoint():
    """Endpoint to list all weather data files stored in the GCS bucket."""
    if not GCS_BUCKET_NAME:
        app.logger.error("GCS_BUCKET_NAME not configured on the server.")
        return jsonify({"error": "Server configuration error: GCS bucket not set."}), 500

    file_prefix = "weather_"
    app.logger.info(f"Listing files from GCS bucket '{GCS_BUCKET_NAME}' with prefix '{file_prefix}'")
    files = list_gcs_files(GCS_BUCKET_NAME, prefix=file_prefix)

    if files is None: # list_gcs_files returns None on error
        app.logger.error(f"Failed to retrieve file list from GCS bucket '{GCS_BUCKET_NAME}'.")
        return jsonify({"error": "Failed to retrieve file list from GCS."}), 500

    return jsonify({"files": files, "bucket": GCS_BUCKET_NAME}), 200


@app.route('/weather-file-content/<path:file_name>', methods=['GET'])
def weather_file_content_endpoint(file_name):
    """
    Endpoint to fetch and display the content of a specific JSON file from GCS.
    <path:file_name> allows filenames to contain slashes (if they are in "subfolders").
    """
    if not GCS_BUCKET_NAME:
        app.logger.error("GCS_BUCKET_NAME not configured on the server.")
        return jsonify({"error": "Server configuration error: GCS bucket not set."}), 500

    if not file_name:
        return jsonify({"error": "File name cannot be empty."}), 400

    app.logger.info(f"Fetching content for file 'gs://{GCS_BUCKET_NAME}/{file_name}'")
    content = get_gcs_file_content(GCS_BUCKET_NAME, file_name)

    if content is None:
        return jsonify({"error": f"File '{file_name}' not found or unable to retrieve/parse content."}), 404

    return jsonify(content), 200

if __name__ == '__main__':
    if not GCS_BUCKET_NAME:
        print("ERROR: The 'GCS_BUCKET_NAME' environment variable is not set.")
        print("Please set it before running the application for local development.")
        print("Example (Linux/macOS): export GCS_BUCKET_NAME='your-gcs-bucket-name'")
        print("Example (Windows PowerShell): $env:GCS_BUCKET_NAME='your-gcs-bucket-name'")
    else:
        port = int(os.environ.get('PORT', 8080))
        app.run(debug=True, host='0.0.0.0', port=port)