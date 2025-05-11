# gcs_client.py
from google.cloud import storage
from google.cloud.exceptions import NotFound, Forbidden
import json
import os # To get environment variables

# It's good practice to initialize the client once, potentially outside functions
# if it's going to be used by multiple functions in the same module/application.
# When running locally, it uses Application Default Credentials (ADC).
# When running on GCP services (like Cloud Run, Cloud Functions), it uses the
# service account associated with that resource by default.
try:
    storage_client = storage.Client()
except Exception as e:
    print(f"Critical Error: Could not initialize Google Cloud Storage client: {e}")
    print("Ensure you have run 'gcloud auth application-default login' or "
          "that the environment is correctly configured for GCP authentication.")
    storage_client = None # Set to None so later functions can check

def upload_to_gcs(bucket_name, destination_blob_name, data_json_string):
    """
    Uploads a string of JSON data to the specified GCS bucket.

    Args:
        bucket_name (str): The name of the GCS bucket.
        destination_blob_name (str): The desired name for the file in GCS (e.g., "data/my_file.json").
        data_json_string (str): The JSON data as a string.

    Returns:
        bool: True if upload was successful, False otherwise.
    """
    if not storage_client:
        print("GCS client not initialized. Cannot upload.")
        return False

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(
            data_json_string,
            content_type='application/json' # Set the content type for proper handling
        )
        print(f"Data successfully uploaded to gs://{bucket_name}/{destination_blob_name}")
        return True
    except NotFound:
        print(f"Error: Bucket '{bucket_name}' not found.")
        return False
    except Forbidden as e:
        print(f"Error: Permission denied for bucket '{bucket_name}' or blob '{destination_blob_name}'. Details: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during GCS upload: {e}")
        return False

def list_gcs_files(bucket_name, prefix=None):
    """
    Lists all blobs (files) in the specified GCS bucket, optionally filtered by a prefix.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str, optional): A prefix to filter blob names. Defaults to None (list all).

    Returns:
        list: A list of blob names (strings) if successful, or None if an error occurs.
    """
    if not storage_client:
        print("GCS client not initialized. Cannot list files.")
        return None

    try:
        blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
        file_names = [blob.name for blob in blobs]
        print(f"Found {len(file_names)} files in gs://{bucket_name}/" + (f" with prefix '{prefix}'" if prefix else ""))
        return file_names
    except NotFound:
        print(f"Error: Bucket '{bucket_name}' not found.")
        return None
    except Forbidden as e:
        print(f"Error: Permission denied for listing blobs in bucket '{bucket_name}'. Details: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while listing GCS files: {e}")
        return None

def get_gcs_file_content(bucket_name, blob_name):
    """
    Fetches the content of a specific blob from GCS and parses it as JSON.

    Args:
        bucket_name (str): The name of the GCS bucket.
        blob_name (str): The name of the blob (file) to retrieve.

    Returns:
        dict/list: The parsed JSON content if successful and the file is valid JSON.
                   Returns None if the file is not found, permission is denied,
                   the content is not valid JSON, or another error occurs.
    """
    if not storage_client:
        print("GCS client not initialized. Cannot get file content.")
        return None

    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            print(f"Error: File 'gs://{bucket_name}/{blob_name}' not found.")
            return None

        # Download content as string (text). The client library handles decoding based on content type
        # or defaults to UTF-8.
        content_string = blob.download_as_text()

        # Parse the string content as JSON
        json_content = json.loads(content_string)
        print(f"Successfully retrieved and parsed content from gs://{bucket_name}/{blob_name}")
        return json_content

    except NotFound: # This specific NotFound for blob.exists() is already handled above.
                    # This would catch if bucket itself was not found during blob.exists() indirectly,
                    # but the bucket specific NotFound is better caught earlier if possible.
        print(f"Error: Bucket '{bucket_name}' or file '{blob_name}' not found during download operation.")
        return None
    except Forbidden as e:
        print(f"Error: Permission denied for reading file 'gs://{bucket_name}/{blob_name}'. Details: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Content of 'gs://{bucket_name}/{blob_name}' is not valid JSON.")
        # print(f"Raw content was: {content_string}") # Uncomment for debugging if needed
        return None
    except Exception as e:
        print(f"An unexpected error occurred while retrieving GCS file content: {e}")
        return None

# This block will only run if the script is executed directly
if __name__ == "__main__":
    print("Testing GCS client...")

    # IMPORTANT: Set this environment variable to your GCS bucket name before running.
    # For example, in your terminal:
    # export GCS_TEST_BUCKET="your-actual-gcs-bucket-name" (Linux/macOS)
    # $env:GCS_TEST_BUCKET="your-actual-gcs-bucket-name" (PowerShell)
    # set GCS_TEST_BUCKET=your-actual-gcs-bucket-name (Windows CMD)
    TEST_BUCKET_NAME = os.environ.get("GCS_TEST_BUCKET")

    if not storage_client:
        print("Exiting test script as GCS client could not be initialized.")
    elif not TEST_BUCKET_NAME:
        print("Error: The 'GCS_TEST_BUCKET' environment variable is not set.")
        print("Please set it to your GCS bucket name to run the tests.")
    else:
        print(f"Using bucket: {TEST_BUCKET_NAME}")

        # --- Test 1: Upload a file ---
        print("\n--- Test Upload ---")
        sample_data_to_upload = {"city": "Testville", "temperature": 25.5, "conditions": "sunny"}
        # Convert Python dict to JSON string
        sample_json_string = json.dumps(sample_data_to_upload, indent=2)
        test_file_name_1 = "test_data/sample_weather_1.json"

        if upload_to_gcs(TEST_BUCKET_NAME, test_file_name_1, sample_json_string):
            print(f"Upload test for '{test_file_name_1}' seems successful (check GCS console).")
        else:
            print(f"Upload test for '{test_file_name_1}' failed.")

        # Upload another file for listing tests
        sample_data_to_upload_2 = {"city": "Cloudburg", "data_points": [1,2,3]}
        test_file_name_2 = "test_data/sample_weather_2.json"
        upload_to_gcs(TEST_BUCKET_NAME, test_file_name_2, json.dumps(sample_data_to_upload_2))

        other_test_file = "other_stuff/notes.txt"
        upload_to_gcs(TEST_BUCKET_NAME, other_test_file, "This is not JSON.")


        # --- Test 2: List files (all and with prefix) ---
        print("\n--- Test List Files (All) ---")
        all_files = list_gcs_files(TEST_BUCKET_NAME)
        if all_files is not None:
            print("All files found:")
            for f_name in all_files:
                print(f" - {f_name}")

        print("\n--- Test List Files (With Prefix 'test_data/') ---")
        test_data_files = list_gcs_files(TEST_BUCKET_NAME, prefix="test_data/")
        if test_data_files is not None:
            print("Files with prefix 'test_data/':")
            for f_name in test_data_files:
                print(f" - {f_name}")

        # --- Test 3: Get file content ---
        print("\n--- Test Get File Content (Successful) ---")
        if test_data_files and test_file_name_1 in test_data_files: # Check if upload was listed
            content = get_gcs_file_content(TEST_BUCKET_NAME, test_file_name_1)
            if content:
                print(f"Content of '{test_file_name_1}':")
                print(json.dumps(content, indent=2)) # Print retrieved content
                # Basic check
                if content.get("city") == "Testville":
                    print("Content check passed for Testville data.")
                else:
                    print("Content check FAILED for Testville data.")
            else:
                print(f"Failed to retrieve or parse content for '{test_file_name_1}'.")
        else:
            print(f"Skipping get content test for '{test_file_name_1}' as it was not found in the list or upload failed.")


        # --- Test 4: Get content of a non-JSON file ---
        print("\n--- Test Get File Content (Non-JSON file) ---")
        non_json_content = get_gcs_file_content(TEST_BUCKET_NAME, other_test_file)
        if non_json_content is None:
            print(f"Correctly handled non-JSON file '{other_test_file}' (returned None).")
        else:
            print(f"Unexpectedly got content for non-JSON file '{other_test_file}': {non_json_content}")


        # --- Test 5: Get content of a non-existent file ---
        print("\n--- Test Get File Content (Non-Existent File) ---")
        non_existent_file = "test_data/does_not_exist.json"
        no_content = get_gcs_file_content(TEST_BUCKET_NAME, non_existent_file)
        if no_content is None:
            print(f"Correctly handled non-existent file '{non_existent_file}' (returned None).")
        else:
            print(f"Unexpectedly got content for non-existent file '{non_existent_file}'.")

        # --- Test 6: Operations on a non-existent bucket (Optional, harder to fully automate without creating/deleting buckets) ---
        # print("\n--- Test Operations on Non-Existent Bucket ---")
        # non_existent_bucket = "this-bucket-surely-does-not-exist-gcs-client-test"
        # if not upload_to_gcs(non_existent_bucket, "test.json", "{}"):
        #     print("Correctly failed to upload to non-existent bucket.")
        # if list_gcs_files(non_existent_bucket) is None:
        #     print("Correctly failed to list from non-existent bucket.")
        # if get_gcs_file_content(non_existent_bucket, "test.json") is None:
        #     print("Correctly failed to get content from non-existent bucket.")

        print("\n--- GCS Client Tests Complete ---")
        print(f"Remember to check your GCS bucket '{TEST_BUCKET_NAME}' in the GCP console to verify uploads and clean up test files if needed.")