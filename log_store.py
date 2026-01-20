# log_store.py
import os
import requests
from datetime import datetime
import pytz
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("JSONBIN_API_KEY")
LOG_BIN_ID = os.getenv("LOG_BIN_ID")
BASE_URL = f"https://api.jsonbin.io/v3/b/{LOG_BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def _fetch_record() -> dict:
    try:
        r = requests.get(f"{BASE_URL}/latest", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            rec = r.json().get("record", {})
            if isinstance(rec, dict):
                return rec
    except Exception as e:
        print("log_store._fetch_record error:", e)
    return {"logs": []}

def _save_record(record: dict) -> bool:
    try:
        r = requests.put(BASE_URL, json=record, headers=HEADERS, timeout=10)
        return r.status_code in (200, 201)
    except Exception as e:
        print("log_store._save_record error:", e)
        return False

def log_entry(query: str, response: str, route: Optional[str]=None, timestamp: Optional[str]=None, user_ip: Optional[str]=None, score: Optional[float]=None):
    """
    Appends a log entry containing:
      - timestamp (in Indian Standard Time if not provided)
      - route (faq/sql/other)
      - query (truncated)
      - response (truncated)
      - optional user_ip (be careful with privacy)
    Best-effort; failures are printed but do not raise.
    """
    try:
        record = _fetch_record()
        logs = record.get("logs", [])

        # ✅ Generate IST timestamp if none provided
        if timestamp:
            ts = timestamp
        else:
            ist = pytz.timezone('Asia/Kolkata')
            ts = datetime.now(ist).strftime("%Y-%m-%d %I:%M:%S %p IST")

        entry = {
            "timestamp": ts,
            "route": route or "unknown",
            "query": (query[:2000] if query else ""),
            "response": (response[:4000] if response else ""),
        }

        if user_ip:
            entry["ip"] = user_ip

        if score is not None:
            entry["score"] = round(float(score), 3)  # ✅ store with 3 decimal precision

        logs.append(entry)
        record["logs"] = logs

        success = _save_record(record)
        if not success:
            print("log_store: failed to save log")

    except Exception as e:
        print("log_store.log_entry error:", e)
