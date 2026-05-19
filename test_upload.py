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

