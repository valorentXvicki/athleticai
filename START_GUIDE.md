# Athletic Spirit - Quick Start Guide

## ✅ All Checks Passed - Ready to Run!

### Prerequisites Verified:
- ✅ Python 3.13.7 installed with all packages
- ✅ Backend files integrated and error-free
- ✅ Database module configured (SQLite)
- ✅ API keys configured (.env file)
- ✅ Frontend connected to backend

---

## 🚀 How to Start the Application

### **Option 1: Double-Click (Easiest)**
1. Double-click `START_SERVER.bat` in your project folder
2. Wait for "Uvicorn running on http://0.0.0.0:3000"
3. Open browser: `http://localhost:3000` or open any `.html` file

### **Option 2: PowerShell**
```powershell
cd C:\Users\vigne\OneDrive\Desktop\proj\capstone\backend
python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

### **Option 3: VS Code Terminal**
```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

---

## 📂 How to Access the Application

### **Frontend Files (Open in Browser):**
- 🏠 **Main App:** `athleteai.html`
- 🔐 **Login:** `login.html`
- 📝 **Sign Up:** `signup.html`
- 📊 **Dashboard:** `dashboard.html`
- 🔑 **Forgot Password:** `forgot-password.html`

### **Backend API:**
- 📡 **Base URL:** http://localhost:3000
- 💚 **Health Check:** http://localhost:3000/health
- 📖 **API Docs:** http://localhost:3000/docs

---

## 🔧 Available Endpoints

### Authentication
- `POST /signup` - Register new user
- `POST /login` - User login (returns JWT token)
- `POST /forgot-password` - Request password reset
- `POST /send-otp` - Send OTP to email
- `POST /verify-otp` - Verify OTP code
- `POST /reset-password` - Reset password with OTP

### User Data
- `GET /api/preferences` - Get user preferences (Protected)
- `POST /api/preferences` - Save preferences (Protected)
- `POST /api/rsvp` - RSVP to event (Protected)
- `POST /api/activities` - Log activity (Protected)
- `GET /api/dashboard/{user_id}` - Get dashboard data (Protected)

### AI Features
- `POST /chat` - Chat with AI assistant
- `GET /api/smart-recommendations` - AI-filtered event recommendations
- `GET /api/nearby-events` - Fetch events from Eventbrite

### Events
- `POST /recsys/scrape-events` - Scrape events from web
- `POST /recsys/update-events` - Update events with AI
- `GET /recsys/recommend-events` - Get recommendations
- `GET /recsys/get-event-link` - Get event enrollment link

---

## 🎯 First Time Setup

1. **Start Backend:**
   - Run `START_SERVER.bat` or use PowerShell command
   - Wait until you see: `Uvicorn running on http://0.0.0.0:3000`

2. **Open Frontend:**
   - Open `signup.html` in your browser
   - Create an account
   - Login to access main app

3. **Explore Features:**
   - Chat with AI assistant
   - Set your sports preferences
   - Get personalized event recommendations
   - Track your activities

---

## 🛠️ Troubleshooting

### Database Issues
- Database (`athletic_spirit.db`) will auto-create on first run
- Located in: `backend/athletic_spirit.db`

### Port Already in Use
```powershell
# Use different port
python -m uvicorn main:app --port 8000 --reload
# Update frontend URLs to http://localhost:8000
```

### Import Errors
```powershell
# Reinstall packages
pip install -r requirements.txt
```

---

## 📊 Project Status

✅ **Backend:** Fully integrated
✅ **Frontend:** All pages connected
✅ **Database:** SQLite configured
✅ **Authentication:** JWT tokens working
✅ **API Keys:** Configured (Gemini, Eventbrite)
✅ **AI Features:** EventRecommender, Chat (Gemini API), Event Enhancement

---

## 🔐 Security Notes

- JWT tokens expire after 7 days
- Passwords hashed with SHA256
- `.env` file protected by `.gitignore`
- Never commit API keys to Git

---


---

## 🚦 Gemini API Setup & Chatbot Usage

1. **Set your Gemini API key:**
   - Create a `.env` file in the project root (if not present).
   - Add this line (replace with your actual key):
     ```
     GEMINI_API_KEY=your-gemini-api-key-here
     ```

2. **Start the backend:**
   - Run `START_SERVER.bat` or use the PowerShell command in this guide.
   - Wait for the server to start (see health check at http://localhost:3000/health).

3. **Open the frontend:**
   - Open `athleteai.html` or your React app with the chatbot UI.
   - Type a message in the chat. Your message will be sent to the backend, which uses Gemini API to generate a response.

4. **Troubleshooting:**
   - If you see errors about missing API keys, double-check your `.env` file and restart the backend.
   - For connection issues, ensure the backend is running and accessible at the correct port.

---

**Ready to run! Start with `START_SERVER.bat` and open `athleteai.html` or your React chatbot. Enjoy Gemini-powered AI chat!** 🚀
