
import requests
import os
from dotenv import load_dotenv

load_dotenv()
EVENTBRITE_API_TOKEN = os.getenv("EVENTBRITE_API_TOKEN", "YOUR_EVENTBRITE_API_TOKEN")

def fetch_events_nearby(location, query="running", radius_km=30, page_size=15):
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "location.address": location,
        "location.within": f"{radius_km}km",
        "q": query,
        "expand": "venue",
        "page_size": page_size
    }
    headers = {
        "Authorization": f"Bearer {EVENTBRITE_API_TOKEN}"
    }
    try:
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"Eventbrite fetch error: {e}")
        return []
    events = []
    for ev in resp.json().get("events", []):
        if not ev.get("venue"): continue
        events.append({
            "id": ev.get("id"),
            "name": ev["name"]["text"],
            "type": "event",
            "location": ev["venue"]["address"]["localized_address_display"],
            "date": ev["start"]["local"],
            "url": ev.get("url", "")
        })
    return events
