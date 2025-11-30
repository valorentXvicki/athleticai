"""
Athletic Spirit Backend - FastAPI Server
Provides authentication, AI chatbot, event recommendations, and user data management.
"""

import os
import sqlite3
import hashlib
import secrets
import random
import string
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import jwt

# Try to import optional dependencies
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "athletic_spirit.db")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

# Initialize FastAPI app
app = FastAPI(
    title="Athletic Spirit API",
    description="Backend API for Athletic Spirit - AI-powered sports coaching platform",
    version="1.0.0"
)

# CORS Configuration - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI if available
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None


# ---------- DATABASE SETUP ----------

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            interests TEXT DEFAULT '["running"]',
            preferred_time TEXT DEFAULT 'morning',
            rsvps TEXT DEFAULT '[]',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            distance REAL,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # OTP table for password reset
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_codes (
            email TEXT PRIMARY KEY,
            otp TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    
    # Password reset tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reset_tokens (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL
        )
    ''')
    
    # User profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            discipline TEXT DEFAULT 'Athlete',
            bio TEXT,
            profile_pic_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()


# Initialize database on startup
init_db()


# ---------- PYDANTIC MODELS ----------

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ChatRequest(BaseModel):
    user_input: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    user_id: str


class PreferencesUpdate(BaseModel):
    interests: Optional[List[str]] = None
    time: Optional[str] = None


class RSVPRequest(BaseModel):
    eventId: int


class ActivityLog(BaseModel):
    type: str
    distance: Optional[float] = None
    duration: Optional[int] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class SendOTPRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


# ---------- HELPER FUNCTIONS ----------

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_jwt_token(user_id: int, email: str) -> str:
    """Create JWT token for authentication."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: str = Header(None)) -> dict:
    """Get current user from JWT token in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    return verify_jwt_token(token)


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))


# ---------- API ENDPOINTS ----------

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Athletic Spirit API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gemini_available": gemini_model is not None,
        "database": "connected"
    }


# -------- AUTHENTICATION --------

@app.post("/signup")
async def signup(user: UserSignup):
    """Register a new user."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists (using 'name' column from existing schema)
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user (using existing schema: name, email, password)
    password_hash = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (user.username, user.email, password_hash)
    )
    user_id = cursor.lastrowid
    
    # Create default preferences (if table exists)
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO user_preferences (user_id) VALUES (?)",
            (user_id,)
        )
    except Exception:
        pass  # Table may not exist
    
    # Create default profile (if table exists)
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO user_profiles (user_id, name) VALUES (?, ?)",
            (user_id, user.username)
        )
    except Exception:
        pass  # Table may not exist
    
    conn.commit()
    conn.close()
    
    return {"message": "Account created successfully! Please login."}


@app.post("/login")
async def login(user: UserLogin):
    """Login and get JWT token."""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(user.password)
    # Use 'password' column from existing schema (not password_hash)
    cursor.execute(
        "SELECT id, email FROM users WHERE email = ? AND password = ?",
        (user.email, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_jwt_token(result["id"], result["email"])
    return {"token": token, "message": "Login successful"}


@app.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Handle Google OAuth authentication."""
    # In a real implementation, you would verify the Google ID token
    # For now, we'll create a mock user or return existing one
    return {"error": "Google authentication requires proper configuration"}


@app.get("/auth/github")
async def github_auth():
    """Redirect to GitHub OAuth."""
    return {"error": "GitHub authentication requires proper configuration"}


# -------- PASSWORD RESET --------

@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset link."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
    if not cursor.fetchone():
        conn.close()
        # Return success even if email doesn't exist (security best practice)
        return {"message": "If an account with that email exists, a reset link has been sent."}
    
    conn.close()
    return {"message": "If an account with that email exists, a reset link has been sent."}


@app.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send OTP to user's email for password reset."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Generate and store OTP
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    cursor.execute(
        "INSERT OR REPLACE INTO otp_codes (email, otp, expires_at) VALUES (?, ?, ?)",
        (request.email, otp, expires_at)
    )
    conn.commit()
    conn.close()
    
    # In production, send actual email here
    # For development, we'll return a message indicating OTP was "sent"
    print(f"[DEV] OTP for {request.email}: {otp}")  # Remove in production
    
    return {"message": f"OTP has been sent to {request.email}"}


@app.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and return reset token."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT otp, expires_at FROM otp_codes WHERE email = ?",
        (request.email,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    
    stored_otp = result["otp"]
    expires_at = datetime.fromisoformat(result["expires_at"])
    
    if datetime.utcnow() > expires_at:
        cursor.execute("DELETE FROM otp_codes WHERE email = ?", (request.email,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    if request.otp != stored_otp:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=1)
    
    cursor.execute(
        "INSERT OR REPLACE INTO reset_tokens (token, email, expires_at) VALUES (?, ?, ?)",
        (reset_token, request.email, token_expires)
    )
    
    # Delete used OTP
    cursor.execute("DELETE FROM otp_codes WHERE email = ?", (request.email,))
    
    conn.commit()
    conn.close()
    
    return {"token": reset_token, "message": "OTP verified successfully"}


@app.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT email, expires_at FROM reset_tokens WHERE token = ?",
        (request.token,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    email = result["email"]
    expires_at = datetime.fromisoformat(result["expires_at"])
    
    if datetime.utcnow() > expires_at:
        cursor.execute("DELETE FROM reset_tokens WHERE token = ?", (request.token,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Update password (using 'password' column from existing schema)
    password_hash = hash_password(request.password)
    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (password_hash, email)
    )
    
    # Delete used token
    cursor.execute("DELETE FROM reset_tokens WHERE token = ?", (request.token,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Password has been reset successfully!"}


# -------- CHATBOT --------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI chatbot endpoint using Gemini API."""
    user_input = request.user_input
    user_id = request.user_id
    
    if gemini_model:
        try:
            # Create a sports-focused prompt
            system_prompt = """You are an AI sports coach for Athletic Spirit, 
            a fitness and sports platform. You help users with:
            - Finding local run clubs and sports events
            - Planning training schedules and workouts
            - Logging activities and tracking progress
            - Providing motivation and fitness advice
            
            Keep responses concise, friendly, and actionable.
            Use emojis sparingly to keep it engaging.
            """
            
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\n\nCoach:"
            response = gemini_model.generate_content(full_prompt)
            ai_response = response.text
        except Exception as e:
            ai_response = f"I'm having trouble connecting to my AI brain right now. Please try again in a moment. (Error: {str(e)})"
    else:
        # Fallback responses when Gemini is not available
        ai_response = get_fallback_response(user_input)
    
    return ChatResponse(response=ai_response, user_id=user_id)


def get_fallback_response(user_input: str) -> str:
    """Provide fallback responses when AI is unavailable."""
    user_input_lower = user_input.lower()
    
    if "club" in user_input_lower or "recommend" in user_input_lower:
        return "🏃 Great question! I'd recommend checking out local running clubs in your area. Morning Run Crew at Cubbon Park (Sun 6 AM) and Interval Tuesdays at Kanteerava Track (Tue 6:30 PM) are popular choices!"
    
    if "event" in user_input_lower or "weekend" in user_input_lower:
        return "📅 This weekend there's the City 10K on Saturday at 7 AM (MG Road) and Weekend Football Crew on Saturday at 6 PM (Sports Arena). Would you like to RSVP for any of these?"
    
    if "log" in user_input_lower or "run" in user_input_lower:
        return "✔️ I've noted your run! Great job staying active. Keep up the good work! 💪"
    
    if "interval" in user_input_lower or "plan" in user_input_lower:
        return "🎯 Here's a sample interval workout: 5 min warm-up jog, then 6x400m at 80% effort with 90 sec rest between, followed by 5 min cool-down. Adjust based on your fitness level!"
    
    if "hello" in user_input_lower or "hi" in user_input_lower:
        return "Hey there! 👋 I'm your AI Coach. How can I help you train smarter today? You can ask me about run clubs, events, workout plans, or just log your activities!"
    
    return "I'm here to help with your fitness journey! Try asking about local run clubs, upcoming events, or how to plan your training. 🏃‍♂️"


# -------- USER PREFERENCES --------

@app.get("/api/preferences")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    """Get user preferences."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Use user_email from existing schema (not user_id)
    cursor.execute(
        "SELECT interests, preferred_time, rsvps FROM user_preferences WHERE user_email = ?",
        (current_user["email"],)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {"interests": ["running"], "time": "morning", "rsvps": []}
    
    import json
    return {
        "interests": json.loads(result["interests"]) if result["interests"] else ["running"],
        "time": result["preferred_time"] or "morning",
        "rsvps": json.loads(result["rsvps"]) if result["rsvps"] else []
    }


@app.post("/api/preferences")
async def save_preferences(prefs: PreferencesUpdate, current_user: dict = Depends(get_current_user)):
    """Save user preferences."""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if preferences exist for this user
    cursor.execute(
        "SELECT id FROM user_preferences WHERE user_email = ?",
        (current_user["email"],)
    )
    existing = cursor.fetchone()
    
    if existing:
        # Update existing preferences
        updates = []
        values = []
        
        if prefs.interests is not None:
            updates.append("interests = ?")
            values.append(json.dumps(prefs.interests))
        
        if prefs.time is not None:
            updates.append("preferred_time = ?")
            values.append(prefs.time)
        
        if updates:
            values.append(current_user["email"])
            cursor.execute(
                f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_email = ?",
                values
            )
    else:
        # Insert new preferences
        cursor.execute(
            "INSERT INTO user_preferences (user_email, interests, preferred_time, rsvps) VALUES (?, ?, ?, ?)",
            (current_user["email"], json.dumps(prefs.interests or ["running"]), prefs.time or "morning", "[]")
        )
    
    conn.commit()
    conn.close()
    return {"message": "Preferences saved successfully"}


@app.put("/api/preferences")
async def update_preferences(prefs: PreferencesUpdate, current_user: dict = Depends(get_current_user)):
    """Update user preferences (alias for POST)."""
    return await save_preferences(prefs, current_user)


# -------- RSVP --------

@app.post("/api/rsvp")
async def rsvp_event(request: RSVPRequest, current_user: dict = Depends(get_current_user)):
    """RSVP to an event."""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    # Use user_email from existing schema
    cursor.execute(
        "SELECT rsvps FROM user_preferences WHERE user_email = ?",
        (current_user["email"],)
    )
    result = cursor.fetchone()
    
    current_rsvps = json.loads(result["rsvps"]) if result and result["rsvps"] else []
    
    if request.eventId not in current_rsvps:
        current_rsvps.append(request.eventId)
        if result:
            cursor.execute(
                "UPDATE user_preferences SET rsvps = ? WHERE user_email = ?",
                (json.dumps(current_rsvps), current_user["email"])
            )
        else:
            cursor.execute(
                "INSERT INTO user_preferences (user_email, rsvps) VALUES (?, ?)",
                (current_user["email"], json.dumps(current_rsvps))
            )
        conn.commit()
    
    conn.close()
    return {"message": "RSVP saved successfully", "rsvps": current_rsvps}


# -------- ACTIVITIES --------

@app.post("/api/activities")
async def log_activity(activity: ActivityLog, current_user: dict = Depends(get_current_user)):
    """Log a user activity."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Use user_email and 'type' column from existing schema
    cursor.execute(
        "INSERT INTO activities (user_email, type, distance) VALUES (?, ?, ?)",
        (current_user["email"], activity.type, activity.distance)
    )
    
    conn.commit()
    activity_id = cursor.lastrowid
    conn.close()
    
    return {"message": "Activity logged successfully", "activity_id": activity_id}


# -------- DASHBOARD --------

@app.get("/api/dashboard/{user_id}")
async def get_dashboard(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get dashboard data for a user."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user info from users table (name column)
    cursor.execute(
        "SELECT id, name FROM users WHERE email = ?",
        (current_user["email"],)
    )
    user_info = cursor.fetchone()
    
    # Get user profile if exists
    profile = None
    if user_info:
        cursor.execute(
            "SELECT name, discipline, bio, profile_pic_url FROM user_profiles WHERE user_id = ?",
            (user_info["id"],)
        )
        profile = cursor.fetchone()
    
    # Get recent activities (using user_email and 'type' column)
    cursor.execute(
        """SELECT type as activity_type, distance, date as created_at 
           FROM activities WHERE user_email = ? 
           ORDER BY created_at DESC LIMIT 10""",
        (current_user["email"],)
    )
    activities = [dict(row) for row in cursor.fetchall()]
    
    # Calculate weekly stats (using user_email from existing schema)
    cursor.execute(
        """SELECT SUM(distance) as total_distance, COUNT(*) as activity_count
           FROM activities 
           WHERE user_email = ? AND created_at >= date('now', '-7 days')""",
        (current_user["email"],)
    )
    weekly_stats = cursor.fetchone()
    
    conn.close()
    
    # Build profile dict
    profile_dict = {"name": "Athlete", "discipline": "Runner"}
    if profile:
        profile_dict = dict(profile)
    elif user_info:
        profile_dict = {"name": user_info["name"], "discipline": "Athlete"}
    
    return {
        "profile": profile_dict,
        "activities": activities,
        "weekly_stats": {
            "total_distance": weekly_stats["total_distance"] or 0,
            "activity_count": weekly_stats["activity_count"] or 0
        }
    }


# -------- SMART RECOMMENDATIONS --------

@app.get("/api/smart-recommendations")
async def get_smart_recommendations(user_id: str = "default"):
    """Get AI-powered event recommendations."""
    # Sample events for recommendations
    events = [
        {"id": 1, "name": "Morning Run Crew", "type": "club", "location": "Cubbon Park", "time": "Sun 6:00 AM"},
        {"id": 2, "name": "City 10K", "type": "event", "location": "MG Road", "time": "Sat 7:00 AM"},
        {"id": 3, "name": "Interval Tuesdays", "type": "club", "location": "Kanteerava Track", "time": "Tue 6:30 PM"},
        {"id": 4, "name": "Trail Half Marathon", "type": "event", "location": "Nandi Hills", "time": "Next Sun 5:30 AM"},
        {"id": 5, "name": "Weekend Football Crew", "type": "club", "location": "Sports Arena", "time": "Sat 6:00 PM"},
    ]
    
    return {"recommendations": events, "user_id": user_id}


@app.get("/api/nearby-events")
async def get_nearby_events():
    """Get nearby events (mock data)."""
    return {
        "events": [
            {"name": "Community Fun Run", "location": "Local Park", "date": "This Sunday"},
            {"name": "Yoga in the Park", "location": "Central Park", "date": "Saturday 8 AM"},
        ]
    }


# -------- RECOMMENDATION SYSTEM --------

@app.post("/recsys/scrape-events")
async def scrape_events():
    """Scrape events from web (placeholder)."""
    return {"message": "Event scraping initiated", "status": "mock"}


@app.post("/recsys/update-events")
async def update_events():
    """Update events with AI enhancement (placeholder)."""
    return {"message": "Events updated", "status": "mock"}


@app.get("/recsys/recommend-events")
async def recommend_events():
    """Get event recommendations."""
    return await get_smart_recommendations()


@app.get("/recsys/get-event-link")
async def get_event_link(event_id: int):
    """Get enrollment link for an event."""
    return {"event_id": event_id, "link": f"https://example.com/events/{event_id}"}


# -------- API DOCS --------

@app.get("/docs")
async def api_docs():
    """Redirect to API documentation."""
    return {"message": "API documentation available at /docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
