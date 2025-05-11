# Historical Weather Data Service API

This backend service fetches historical weather data from the Open-Meteo Historical Weather API for specified locations and date ranges. It stores the API responses as JSON files in Google Cloud Storage (GCS) and provides API endpoints to list and retrieve these stored files.

The application is built with Python and Flask, containerized with Docker, and deployed on Google Cloud Run.

## Features

*   Fetches specified daily weather variables from Open-Meteo.
*   Stores fetched data as JSON files in Google Cloud Storage.
*   Provides an API to:
    *   Trigger data fetching and storage.
    *   List all stored weather data files.
    *   Retrieve the content of a specific stored weather data file.

## Tech Stack

*   **Framework:** Python 3.9+ with Flask
*   **Cloud Platform:** Google Cloud Platform (GCP)
*   **Storage:** Google Cloud Storage (GCS)
*   **Containerization:** Docker
*   **WSGI Server:** Gunicorn
*   **Deployment:** Google Cloud Run

## API Endpoints

The base URL for the deployed service is: `https://weather-service-989989734580.asia-south2.run.app`

### 1. Store Weather Data

*   **Endpoint:** `/store-weather-data`
*   **Method:** `POST`
*   **Description:** Fetches historical weather data from the Open-Meteo API for the given parameters and stores the results as a JSON file in Google Cloud Storage.
*   **Request Body (JSON):**
    ```json
    {
      "latitude": 52.52,
      "longitude": 13.41,
      "start_date": "2023-01-01",
      "end_date": "2023-01-05"
    }
    ```
    *   `latitude`: (float) Geographical latitude.
    *   `longitude`: (float) Geographical longitude.
    *   `start_date`: (string) Start date in `YYYY-MM-DD` format.
    *   `end_date`: (string) End date in `YYYY-MM-DD` format.
*   **Success Response (201 Created):**
    ```json
    {
      "message": "Weather data fetched and stored successfully.",
      "file_name": "weather_lat52_52_lon13_41_from20230101_to20230105.json",
      "gcs_path": "gs://<YOUR_GCS_BUCKET_NAME>/weather_lat52_52_lon13_41_from20230101_to20230105.json"
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: If input is invalid (e.g., missing parameters, incorrect format).
        ```json
        {
          "error": "Missing parameters: latitude"
        }
        ```
    *   `502 Bad Gateway`: If fetching data from Open-Meteo API fails.
        ```json
        {
          "error": "Failed to fetch weather data from external API."
        }
        ```
    *   `500 Internal Server Error`: If storing data to GCS fails or other server-side issues.
        ```json
        {
          "error": "Failed to store weather data in GCS."
        }
        ```

### 2. List Weather Files

*   **Endpoint:** `/list-weather-files`
*   **Method:** `GET`
*   **Description:** Lists all weather data JSON files stored in the GCS bucket (filtered by names starting with "weather\_").
*   **Request Body:** None
*   **Success Response (200 OK):**
    ```json
    {
      "bucket": "<YOUR_GCS_BUCKET_NAME>",
      "files": [
        "weather_lat52_52_lon13_41_from20230101_to20230105.json",
        "weather_lat34_05_lon-118_24_from20230210_to20230212.json"
      ]
    }
    ```
*   **Error Response (500 Internal Server Error):**
    ```json
    {
      "error": "Failed to retrieve file list from GCS."
    }
    ```

### 3. Get Weather File Content

*   **Endpoint:** `/weather-file-content/<file_name>`
*   **Method:** `GET`
*   **Description:** Fetches and displays the content of a specific JSON file stored in GCS.
*   **URL Parameter:**
    *   `file_name`: (string) The name of the JSON file in GCS (e.g., `weather_lat52_52_lon13_41_from20230101_to20230105.json`).
*   **Request Body:** None
*   **Success Response (200 OK):**
    The JSON content of the requested file.
    ```json
    {
      "latitude": 52.52,
      "longitude": 13.41,
      // ... other weather data from Open-Meteo response ...
      "daily": {
        "time": ["2023-01-01", "2023-01-02", ...],
        "temperature_2m_max": [2.5, 3.1, ...],
        // ... other daily variables ...
      }
    }
    ```
*   **Error Response (404 Not Found):**
    ```json
    {
      "error": "File '<file_name>' not found or unable to retrieve/parse content."
    }
    ```

## Setup and Installation (Local Development)

### Prerequisites

*   Python 3.9+
*   `pip` and `venv`
*   Google Cloud SDK (`gcloud` CLI) installed and authenticated.
*   Docker Desktop or Docker Engine installed and running.
*   A Google Cloud Platform project with billing enabled.
*   A Google Cloud Storage bucket created.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Devashish08/weatherAPI.git
    cd weatherAPI
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Google Cloud authentication for local development:**
    If you haven't already, log in and set up Application Default Credentials:
    ```bash
    gcloud auth application-default login
    ```
    Ensure the authenticated user has permissions for your GCS bucket (e.g., Storage Object Admin).

5.  **Set required environment variables:**
    For the application to connect to your GCS bucket and for the GCS client library to identify the project context when running locally (especially if the ADC file doesn't strongly specify it):
    ```bash
    export GCS_BUCKET_NAME="your-gcs-bucket-name" # e.g., inrisk_assignment
    export GOOGLE_CLOUD_PROJECT="your-gcp-project-id" # e.g., weather-app-challenge-459414
    ```

6.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:8080`.

### Running with Docker Locally

1.  **Build the Docker image:**
    (Ensure Docker is running)
    ```bash
    docker build -t weather-app-service .
    ```

2.  **Run the Docker container:**
    Replace `your-gcs-bucket-name` and `your-gcp-project-id`.
    ```bash
    docker run -p 8080:8080 \
           -e GCS_BUCKET_NAME="your-gcs-bucket-name" \
           -e GOOGLE_CLOUD_PROJECT="your-gcp-project-id" \
           -e GOOGLE_APPLICATION_CREDENTIALS="/tmp/adc.json" \
           -v ${HOME}/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro \
           weather-app-service
    ```
    *   **Note on ADC path for `-v` on Windows:** The path to `application_default_credentials.json` might differ. For PowerShell, it's often `"$env:APPDATA\gcloud\application_default_credentials.json"`.
    The application inside Docker will be available at `http://127.0.0.1:8080`.

## Deployment to Google Cloud Run

### Prerequisites

*   GCP Project set up (as above).
*   `gcloud` CLI configured for your project.
*   Docker image built successfully.
*   Google Cloud APIs enabled: Cloud Run API, Artifact Registry API, Cloud Storage API.
*   An Artifact Registry Docker repository created in your GCP project.

### Steps

1.  **Configure Docker to authenticate with Artifact Registry:**
    Replace `YOUR_REGION` with the region of your Artifact Registry (e.g., `asia-south2`).
    ```bash
    gcloud auth configure-docker YOUR_REGION-docker.pkg.dev
    ```

2.  **Tag your local Docker image for Artifact Registry:**
    Replace placeholders with your values.
    ```bash
    export PROJECT_ID="your-gcp-project-id"
    export REGION="your-artifact-registry-region" # e.g., asia-south2
    export AR_REPO_NAME="your-artifact-registry-repo-name" # e.g., weather-app-repo
    export LOCAL_IMAGE_NAME="weather-app-service"

    export TARGET_IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO_NAME}/${LOCAL_IMAGE_NAME}:latest"
    
    docker tag ${LOCAL_IMAGE_NAME} ${TARGET_IMAGE_TAG}
    ```

3.  **Push the image to Artifact Registry:**
    ```bash
    docker push ${TARGET_IMAGE_TAG}
    ```

4.  **Deploy to Cloud Run:**
    Replace placeholders. The `${TARGET_IMAGE_TAG}`, `${REGION}`, and `${PROJECT_ID}` variables should be set from the previous step.
    ```bash
    gcloud run deploy weather-service \
        --image "${TARGET_IMAGE_TAG}" \
        --platform managed \
        --region "${REGION}" \
        --allow-unauthenticated \
        --set-env-vars GCS_BUCKET_NAME="your-gcs-bucket-name",GOOGLE_CLOUD_PROJECT="${PROJECT_ID}" \
        --port 8080
    ```
    Note the `Service URL` provided upon successful deployment.

5.  **Configure IAM Permissions for Cloud Run Service Account:**
    The Cloud Run service runs as a specific service account (by default, the Compute Engine default service account: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`). This service account needs permissions to access your GCS bucket.
    *   Go to your GCS bucket in the GCP Console.
    *   Navigate to the "Permissions" tab.
    *   Click "+ Grant Access".
    *   **New principals:** Enter the email of the service account Cloud Run is using.
    *   **Assign roles:**
        *   `Storage Object Creator`
        *   `Storage Object Viewer`
    *   Click "Save".

## Live Demo URL

The deployed service can be accessed at:
`https://weather-service-989989734580.asia-south2.run.app`

---
