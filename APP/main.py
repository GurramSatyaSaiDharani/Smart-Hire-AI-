import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from APP.auth import router as auth_router
from APP.speech_analysis import router as speech_router
from APP.interview_session import router as session_router
from APP.emotion_analysis import router as emotion_router
from APP.ai_feedback_scoring import router as feedback_scoring_router
from APP.analytics import router as analytics_router
from APP.scheduling import router as scheduling_router
from APP.notifications import router as notifications_router
from APP.reports import router as reports_router
from APP.database import engine, Base, sync_db_schema

# Sync DB schema and create missing tables/columns
sync_db_schema()

app = FastAPI(title="Smart Hire AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(speech_router)
app.include_router(session_router)
app.include_router(emotion_router)
app.include_router(feedback_scoring_router)
app.include_router(analytics_router)
app.include_router(scheduling_router)
app.include_router(notifications_router)
app.include_router(reports_router)

# Mount static frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Mount static uploads directory for video recording playback
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def home():
    return RedirectResponse(url="/frontend/index.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Smart Hire AI Enterprise Backend Running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("APP.main:app", host="0.0.0.0", port=port)