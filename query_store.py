import os
import requests
from datetime import date
from dotenv import load_dotenv


load_dotenv()

BIN_ID = os.getenv("JSONBIN_BIN_ID")
API_KEY = os.getenv("JSONBIN_API_KEY")
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def get_data():
    """Fetch the full JSON record from JSONBin."""
    try:
        res = requests.get(f"{BASE_URL}/latest", headers=HEADERS)
        print("📡 Status code:", res.status_code)
        print("📡 Response:", res.text[:200])
        if res.status_code == 200:
            record = res.json().get("record", {})
            if isinstance(record, dict):
                return record
        print("⚠️ Unexpected response:", res.text)
    except Exception as e:
        print("🚨 Error fetching data:", e)
    # fallback
    return {"query_count": 0, "last_reset": str(date.today())}


def save_data(data):
    """Update JSONBin with new data."""
    try:
        res = requests.put(BASE_URL, json=data, headers=HEADERS)
        return res.status_code == 200
    except Exception as e:
        print("Error saving data:", e)
        return False

def get_query_count():
    """Return the current query count (resets if a new day)."""
    data = get_data()
    today = str(date.today())
    last_reset = data.get("last_reset")

    print(f"🕒 Today: {today} | Last reset: {last_reset}")

    # Force reset if day changed OR if JSON is malformed
    if not last_reset or last_reset != today:
        print("🔄 New day detected — resetting query count to 0.")
        data = {"query_count": 0, "last_reset": today}
        save_data(data)
        return 0

    return data.get("query_count", 0)




def update_query_count(new_count):
    """Increment and save updated count."""
    today = str(date.today())
    data = {"query_count": new_count, "last_reset": today}
    save_data(data)
