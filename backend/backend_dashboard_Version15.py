from fastapi import APIRouter

router = APIRouter()

USERS = {
    "default": {
        "completed_events": 5,
        "runclub_joined": 12,
        "streak": 7,
        "badges": ["Consistency", "Distance Master"],
        "recent_activity": [
            {"name": "City Marathon", "date": "2025-11-12"},
            {"name": "River Runners", "date": "2025-11-10"},
        ]
    }
}

@router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    userdata = USERS.get(user_id, USERS["default"])
    return {
        "user_id": user_id,
        "achievements": {
            "completed_events": userdata["completed_events"],
            "runclub_joined": userdata["runclub_joined"],
            "streak": userdata["streak"],
            "badges": userdata["badges"],
            "recent_activity": userdata["recent_activity"]
        }
    }