import requests

# 1. THE TARGET URL
# Replace 'your-app-name' with your actual Render URL.
# Do NOT add a trailing slash at the end.
URL = "https://swarm-api-super-agent-travily.onrender.com/upload-doc"

# 2. THE PAYLOAD
# This must exactly match your Pydantic DocumentUpload model.
data = {
    "admin_password": "*******",
    "content": "CRITICAL DATA: The primary database was upgraded to Supabase. The system architect is Nayan."
}

print(f"Initiating upload sequence to: {URL}...")

# 3. THE EXECUTION
try:
    response = requests.post(URL, json=data)

    print("\n--- TEST RESULTS ---")
    print(f"Status Code: {response.status_code}")

    # We attempt to parse JSON, but catch raw HTML errors if Hugging Face or Render fails
    try:
        print(f"Parsed JSON: {response.json()}")
    except ValueError:
        print(f"Raw Output (HTML/Text): {response.text}")

except requests.exceptions.RequestException as e:
    print(f"FATAL: Network connection failed: {e}")