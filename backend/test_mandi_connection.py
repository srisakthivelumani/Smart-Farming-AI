
import os
import urllib.request
import urllib.parse
import urllib.error
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DATAGOV_API_KEY")

if not api_key:
    print("API key not configured")
    raise SystemExit(1)

base_url = (
    "https://api.data.gov.in/resource/"
    "9ef84268-d588-465a-a308-a864a43d0070"
)

params = urllib.parse.urlencode({
    "api-key": api_key,
    "format": "json",
    "limit": 1,
})

url = f"{base_url}?{params}"

request = urllib.request.Request(
    url,
    headers={
        "Accept": "application/json",
        "User-Agent": "SmartFarmingAI/1.0",
    },
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        print("HTTP Status:", response.status)
        print("Response:", response.read(1000).decode("utf-8"))

except urllib.error.HTTPError as error:
    print("HTTP Status:", error.code)
    print("Response:", error.read(1000).decode("utf-8"))

except Exception as error:
    print("Error:", type(error).__name__, str(error))
