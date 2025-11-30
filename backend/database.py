"""
Database module for Athletic Spirit application.
Uses SQLite for persistent storage.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

DATABASE_PATH = "athletic_spirit.db"

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                auth_provider TEXT DEFAULT 'local',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE NOT NULL,
                interests TEXT,
                preferred_time TEXT,
                rsvps TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                link TEXT,
                category TEXT DEFAULT 'sports',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                type TEXT NOT NULL,
                distance REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # Chat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
            )
        """)
        
        # OTP storage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                otp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        
        conn.commit()
        print("Database initialized successfully!")

# User operations
def create_user(email: str, name: str, password: str, auth_provider: str = "local") -> bool:
    """Create a new user."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, name, password, auth_provider) VALUES (?, ?, ?, ?)",
                (email, name, password, auth_provider)
            )
            return True
    except sqlite3.IntegrityError:
        return False

def get_user(email: str) -> Optional[Dict]:
    """Get user by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None

def update_user(email: str, **kwargs):
    """Update user fields."""
    with get_db() as conn:
        cursor = conn.cursor()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [email]
        cursor.execute(f"UPDATE users SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE email = ?", values)

# Preferences operations
def get_preferences(user_email: str) -> Dict:
    """Get user preferences."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_preferences WHERE user_email = ?", (user_email,))
        row = cursor.fetchone()
        if row:
            return {
                "interests": json.loads(row["interests"]) if row["interests"] else [],
                "time": row["preferred_time"] or "morning",
                "rsvps": json.loads(row["rsvps"]) if row["rsvps"] else []
            }
    # Return defaults if not found
    return {"interests": ["running"], "time": "morning", "rsvps": []}

def save_preferences(user_email: str, interests: List[str] = None, time: str = None, rsvps: List[int] = None):
    """Save or update user preferences."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_preferences WHERE user_email = ?", (user_email,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            updates = []
            values = []
            if interests is not None:
                updates.append("interests = ?")
                values.append(json.dumps(interests))
            if time is not None:
                updates.append("preferred_time = ?")
                values.append(time)
            if rsvps is not None:
                updates.append("rsvps = ?")
                values.append(json.dumps(rsvps))
            
            if updates:
                values.append(user_email)
                cursor.execute(
                    f"UPDATE user_preferences SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_email = ?",
                    values
                )
        else:
            # Create new
            cursor.execute(
                """INSERT INTO user_preferences (user_email, interests, preferred_time, rsvps) 
                   VALUES (?, ?, ?, ?)""",
                (user_email, 
                 json.dumps(interests or ["running"]), 
                 time or "morning",
                 json.dumps(rsvps or []))
            )

# Event operations
def create_event(name: str, date: str, location: str, description: str, link: str, category: str = "sports") -> int:
    """Create a new event."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO events (name, date, location, description, link, category) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, date, location, description, link, category)
        )
        return cursor.lastrowid

def get_all_events() -> List[Dict]:
    """Get all events."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def update_event(event_id: int, **kwargs):
    """Update event fields."""
    with get_db() as conn:
        cursor = conn.cursor()
        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [event_id]
        cursor.execute(f"UPDATE events SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)

def clear_events():
    """Clear all events (for refresh)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events")

# Activity operations
def log_activity(user_email: str, activity_type: str, distance: float) -> int:
    """Log a user activity."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (user_email, type, distance) VALUES (?, ?, ?)",
            (user_email, activity_type, distance)
        )
        return cursor.lastrowid

def get_user_activities(user_email: str, limit: int = 10) -> List[Dict]:
    """Get user activities."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM activities WHERE user_email = ? ORDER BY date DESC LIMIT ?",
            (user_email, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# Chat history operations
def save_chat_message(user_email: str, role: str, content: str):
    """Save a chat message."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_email, role, content) VALUES (?, ?, ?)",
            (user_email, role, content)
        )

def get_chat_history(user_email: str, limit: int = 50) -> List[Dict]:
    """Get chat history for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE user_email = ? ORDER BY timestamp ASC LIMIT ?",
            (user_email, limit)
        )
        rows = cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

def clear_chat_history(user_email: str):
    """Clear chat history for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_email = ?", (user_email,))

# OTP operations
def store_otp(email: str, otp: str, expires_minutes: int = 10):
    """Store OTP for password reset."""
    from datetime import timedelta
    expires_at = datetime.now() + timedelta(minutes=expires_minutes)
    with get_db() as conn:
        cursor = conn.cursor()
        # Delete old OTPs for this email
        cursor.execute("DELETE FROM otp_storage WHERE email = ?", (email,))
        # Insert new OTP
        cursor.execute(
            "INSERT INTO otp_storage (email, otp, expires_at) VALUES (?, ?, ?)",
            (email, otp, expires_at)
        )

def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP is valid and not expired."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM otp_storage WHERE email = ? AND otp = ? AND expires_at > datetime('now')",
            (email, otp)
        )
        row = cursor.fetchone()
        if row:
            # Delete used OTP
            cursor.execute("DELETE FROM otp_storage WHERE id = ?", (row["id"],))
            return True
    return False

# Initialize database on module import
init_db()
