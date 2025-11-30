from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
import database as db

# Load environment variables
load_dotenv()

# Reuse AI from main.py (will be passed or imported)
gen_model = None  # To be set from main.py

router = APIRouter()

class Event(BaseModel):
    name: str
    date: str
    location: str
    description: str
    link: str
    category: str = "sports"  # Default category

class Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_sports_events(self, url: str) -> List[Dict]:
        """Scrape sports events from a given URL."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            events = []
            # Example: Assume events are in divs with class 'event'
            for event_div in soup.find_all('div', class_='event'):
                name = event_div.find('h2').text.strip() if event_div.find('h2') else "Unknown"
                date = event_div.find('span', class_='date').text.strip() if event_div.find('span', class_='date') else "TBD"
                location = event_div.find('span', class_='location').text.strip() if event_div.find('span', class_='location') else "Unknown"
                description = event_div.find('p', class_='desc').text.strip() if event_div.find('p', class_='desc') else "No description"
                link = event_div.find('a')['href'] if event_div.find('a') else url
                events.append({
                    "name": name,
                    "date": date,
                    "location": location,
                    "description": description,
                    "link": link,
                    "category": "sports"
                })
            return events
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

class EventUpdater:
    def __init__(self, gen_model, gemini_key):
        self.gen_model = gen_model
        self.gemini_key = gemini_key
        if gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None

    def update_event_with_ai(self, event: Dict) -> Dict:
        """Use Gemini to enhance event description."""
        if not self.gemini_model:
            return event
            
        try:
            prompt = f"Enhance this sports event description with more details, category, and appeal: {event['description']}"
            response = self.gemini_model.generate_content(prompt)
            event['description'] = response.text.strip()
            return event
        except Exception as e:
            print(f"Gemini error: {e}")
            # Fallback to local GPT-2 if Gemini fails
            try:
                if self.gen_model:
                    prompt = f"You are a helpful AI assistant. Enhance this sports event description: '{event['description']}'."
                    generated = self.gen_model(prompt, max_length=150, do_sample=True, temperature=0.7)
                    response = generated[0]['generated_text'].replace(prompt, '').strip()
                    event['description'] = response
                return event
            except:
                return event  # Return unchanged if AI fails

class Recommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def recommend(self, user_preferences: str, events: List[Dict], top_n: int = 5) -> List[Dict]:
        """Recommend events based on user preferences using content similarity."""
        if not events:
            return []
        descriptions = [event['description'] for event in events]
        tfidf_matrix = self.vectorizer.fit_transform(descriptions + [user_preferences])
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
        top_indices = similarities.argsort()[-top_n:][::-1]
        return [events[i] for i in top_indices]

scraper = Scraper()
updater = EventUpdater(gen_model, os.getenv("GEMINI_API_KEY"))
recommender = Recommender()

@router.post("/scrape-events")
async def scrape_events(url: str):
    """Scrape events from web and save to database."""
    events = scraper.scrape_sports_events(url)
    
    # Save events to database
    for event in events:
        db.create_event(
            name=event["name"],
            date=event["date"],
            location=event["location"],
            description=event["description"],
            link=event["link"],
            category=event.get("category", "sports")
        )
    
    return {"message": f"Scraped and saved {len(events)} events", "events": events}

@router.post("/update-events")
async def update_events():
    """Update all events with AI."""
    events = db.get_all_events()
    updated_count = 0
    
    for event in events:
        # Convert database row to dict format expected by updater
        event_dict = {
            "name": event["name"],
            "date": event["date"],
            "location": event["location"],
            "description": event["description"],
            "link": event["link"],
            "category": event["category"]
        }
        updated = updater.update_event_with_ai(event_dict)
        db.update_event(event["id"], description=updated["description"])
        updated_count += 1
    
    return {"message": f"Updated {updated_count} events with AI"}

@router.get("/recommend-events")
async def recommend_events(user_preferences: str, top_n: int = 5):
    """Get event recommendations based on user preferences."""
    events = db.get_all_events()
    
    # Convert to format expected by recommender
    events_list = [
        {
            "name": e["name"],
            "date": e["date"],
            "location": e["location"],
            "description": e["description"],
            "link": e["link"],
            "category": e["category"]
        }
        for e in events
    ]
    
    recommendations = recommender.recommend(user_preferences, events_list, top_n)
    return {"recommendations": recommendations}

@router.get("/get-event-link")
async def get_event_link(event_name: str):
    """Get enrollment link for a specific event."""
    events = db.get_all_events()
    for event in events:
        if event['name'].lower() == event_name.lower():
            return {"link": event['link']}
    raise HTTPException(status_code=404, detail="Event not found")
