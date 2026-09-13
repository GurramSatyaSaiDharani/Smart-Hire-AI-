from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import json

from APP.database import SessionLocal
from APP.models import InterviewSession

router = APIRouter(prefix="/api/emotion", tags=["emotion-analysis"])

class EmotionTelemetryPayload(BaseModel):
    session_id: str
    confidence_score: Optional[float] = 0.0
    eye_contact_pct: Optional[float] = 0.0
    attention_score: Optional[float] = 0.0
    engagement_score: Optional[float] = 0.0
    dominant_emotion: Optional[str] = "Neutral"
    emotion_breakdown: Optional[Dict[str, float]] = None
    attention_events_count: Optional[int] = 0
    behavior_notes: Optional[List[str]] = []

@router.post("/log-telemetry")
def log_emotion_telemetry(payload: EmotionTelemetryPayload):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == payload.session_id).first()
        if not session:
            # Create session placeholder if missing
            session = InterviewSession(
                session_id=payload.session_id,
                candidate_name="Candidate",
                status="IN_PROGRESS"
            )
            db.add(session)
            db.commit()

        session.confidence_score = payload.confidence_score
        session.eye_contact_pct = payload.eye_contact_pct
        session.attention_score = payload.attention_score
        session.engagement_score = payload.engagement_score
        session.dominant_emotion = payload.dominant_emotion
        session.attention_events_count = payload.attention_events_count

        if payload.emotion_breakdown:
            session.emotion_breakdown_json = json.dumps(payload.emotion_breakdown)

        # Generate automated executive recruitment behavioral summary
        summary = generate_behavioral_summary(payload)
        session.behavior_summary = summary

        db.commit()
        db.refresh(session)

        return {
            "status": "success",
            "message": "Section 6 Emotion & Eye-Tracking Telemetry Logged",
            "session_id": session.session_id,
            "behavior_summary": summary
        }
    finally:
        db.close()

@router.get("/{session_id}/report")
def get_emotion_report(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        breakdown = {}
        if session.emotion_breakdown_json:
            try:
                breakdown = json.loads(session.emotion_breakdown_json)
            except Exception:
                pass

        return {
            "session_id": session.session_id,
            "candidate_name": session.candidate_name,
            "confidence_score": session.confidence_score or 0.0,
            "eye_contact_pct": session.eye_contact_pct or 0.0,
            "attention_score": session.attention_score or 0.0,
            "engagement_score": session.engagement_score or 0.0,
            "dominant_emotion": session.dominant_emotion or "Neutral",
            "emotion_breakdown": breakdown,
            "attention_events_count": session.attention_events_count or 0,
            "behavior_summary": session.behavior_summary or "Candidate exhibited balanced composure and standard engagement during the interview."
        }
    finally:
        db.close()

def generate_behavioral_summary(payload: EmotionTelemetryPayload) -> str:
    parts = []
    
    # 1. Confidence Evaluation
    conf = payload.confidence_score or 0.0
    if conf >= 85:
        parts.append("Candidate displayed exceptional poise, stable head posture, and high vocal composure.")
    elif conf >= 70:
        parts.append("Candidate showed good confidence with minor micro-hesitations.")
    else:
        parts.append("Candidate displayed elevated nervousness, frequent posture shifts, or uncertain expression.")

    # 2. Eye Contact Evaluation
    eye = payload.eye_contact_pct or 0.0
    if eye >= 80:
        parts.append(f"Maintained excellent direct eye contact ({eye:.1f}% ratio) with the camera.")
    elif eye >= 60:
        parts.append(f"Satisfactory eye contact ({eye:.1f}% ratio) with moderate gaze shifts.")
    else:
        parts.append(f"Low eye contact ({eye:.1f}% ratio) with frequent off-screen gaze drift.")

    # 3. Attention & Focus
    att = payload.attention_score or 0.0
    alerts = payload.attention_events_count or 0
    if att >= 85:
        parts.append(f"Strong focus retention ({att:.1f}% attention score) with {alerts} distraction flags.")
    else:
        parts.append(f"Intermittent focus drops ({att:.1f}% attention score) and {alerts} off-screen distraction alerts detected.")

    # 4. Dominant Emotion & Engagement
    dom = payload.dominant_emotion or "Neutral"
    eng = payload.engagement_score or 0.0
    parts.append(f"Dominant facial mood was '{dom}' with an overall Engagement Index of {eng:.1f}/100.")

    return " ".join(parts)
