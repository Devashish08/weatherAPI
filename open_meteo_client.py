import requests

import json

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "apparent_temperature_mean",
]

def fetch_weather_data(latitude, longitude, start_date, end_date): # Corrected typo: latitute -> latitude
    """"
      Fetches historical weather data from the Open-Meteo API.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date for the data range (YYYY-MM-DD).
        end_date (str): End date for the data range (YYYY-MM-DD).

    Returns:
        dict: A dictionary containing the weather data if successful,
              None otherwise.
    """

    params = {
        "latitude": latitude, # Corrected typo: latitute -> latitude
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "GMT"
    }


    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        weather_data = response.json()
        return weather_data

    except requests.exceptions.Timeout:
        print(f"Error: The request to open-meteo timed out. Response was: {response.text}") 
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Error: Could not connect to Open-Meteo. Check your internet connection. Details: {conn_err}")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Status Code: {response.status_code}")
        print(f"Response content: {response.text}") 
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Open-Meteo: {e}")
        if 'response' in locals() and response is not None:
             print(f"Response content: {response.text}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from Open-Meteo. Response was: {response.text}")
        return None
if __name__ == "__main__":
    test_latitude = 52.52
    test_longitude = 13.41
    start_date = "2023-03-01"
    end_date = "2023-03-03"
    print(f"Fetching data for Lat: {test_latitude}, Lon: {test_longitude}, "
          f"From: {start_date} To: {end_date}") # Corrected variable name: test_start_date -> start_date

    data = fetch_weather_data(test_latitude, test_longitude, start_date, end_date)

    if data:
        print("\nSuccessfully fetched weather data.")
        print(json.dumps(data, indent=2))

        if "daily" in data and "time" in data["daily"]:
            print(f"\nDates reported: {data['daily']['time']}")
        if "daily" in data and "temperature_2m_max" in data["daily"]:
            print(f"Max temperatures: {data['daily']['temperature_2m_max']}")
    else:
        print("\nFailed to fetch weather data.")

    print("\n--- Test with invalid parameter (e.g., invalid variable name, should be caught by API) ---")
    original_daily_vars = list(DAILY_VARIABLES)
    DAILY_VARIABLES.append("invalid_variable_name")
    print(f"Fetching data with an invalid variable: {','.join(DAILY_VARIABLES)}")

    data_invalid_param = fetch_weather_data(test_latitude, test_longitude, start_date, end_date)
    if not data_invalid_param:
        print("Correctly handled invalid parameter (API returned error).")
    else:
        print("Unexpectedly got data with invalid parameter:")
        print(json.dumps(data_invalid_param, indent=2))
    DAILY_VARIABLES = original_daily_vars

    print("\n--- Test with invalid date (expecting an error from API) ---")
    invalid_start_date = "2023-15-01" # Invalid month
    data_invalid = fetch_weather_data(test_latitude, test_longitude, invalid_start_date, end_date)
    if not data_invalid:
        print("Correctly handled invalid date input (or other API error).")
    else:
        print("Unexpectedly got data for invalid date input:")
        print(json.dumps(data_invalid, indent=2))
    
    print("\n--- Test with invalid date format (client-side or API error) ---")
    invalid_format_date = "01-03-2023"
    data_invalid_format = fetch_weather_data(test_latitude, test_longitude, invalid_format_date, end_date)
    if not data_invalid_format:
        print("Correctly handled invalid date format (API returned error).")
    else:
        print("Unexpectedly got data for invalid date format:")
        print(json.dumps(data_invalid_format, indent=2))
       