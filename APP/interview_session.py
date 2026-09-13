from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

from APP.database import SessionLocal
from APP.models import InterviewSession, InterviewQuestion

router = APIRouter(prefix="/api/sessions", tags=["interview-sessions"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "recordings"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SessionCreateSchema(BaseModel):
    session_id: str
    interview_id: Optional[int] = 1
    candidate_id: Optional[int] = 1
    candidate_name: Optional[str] = "Candidate"

class QuestionLogSchema(BaseModel):
    question_index: int
    question_text: str
    transcript: Optional[str] = ""
    duration_seconds: Optional[float] = 0.0
    grammar_score: Optional[float] = None
    pace_score: Optional[float] = None
    filler_score: Optional[float] = None
    pronunciation_score: Optional[float] = None

class SessionEndSchema(BaseModel):
    total_duration_seconds: float
    overall_score: Optional[float] = None
    overall_grade: Optional[str] = None
    confidence_score: Optional[float] = None
    eye_contact_pct: Optional[float] = None
    attention_score: Optional[float] = None
    engagement_score: Optional[float] = None
    dominant_emotion: Optional[str] = None
    emotion_breakdown_json: Optional[str] = None
    behavior_summary: Optional[str] = None
    attention_events_count: Optional[int] = 0

@router.post("/create")
def create_session(payload: SessionCreateSchema):
    db = SessionLocal()
    try:
        existing = db.query(InterviewSession).filter(InterviewSession.session_id == payload.session_id).first()
        if existing:
            return {"message": "Session already exists", "session_id": existing.session_id, "status": existing.status}
        
        session = InterviewSession(
            session_id=payload.session_id,
            interview_id=payload.interview_id or 1,
            candidate_id=payload.candidate_id or 1,
            candidate_name=payload.candidate_name or "Candidate",
            status="CREATED",
            created_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return {"message": "Interview session created", "session_id": session.session_id, "status": session.status}
    finally:
        db.close()

@router.post("/{session_id}/start")
def start_session(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = "IN_PROGRESS"
        if not session.start_time:
            session.start_time = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        return {
            "message": "Session started",
            "session_id": session.session_id,
            "status": session.status,
            "start_time": session.start_time.isoformat()
        }
    finally:
        db.close()

@router.post("/{session_id}/pause")
def pause_session(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = "PAUSED"
        db.commit()
        db.refresh(session)
        return {"message": "Session paused", "session_id": session.session_id, "status": session.status}
    finally:
        db.close()

@router.post("/{session_id}/resume")
def resume_session(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = "IN_PROGRESS"
        db.commit()
        db.refresh(session)
        return {"message": "Session resumed", "session_id": session.session_id, "status": session.status}
    finally:
        db.close()

@router.post("/{session_id}/end")
def end_session(session_id: str, payload: SessionEndSchema):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = "COMPLETED"
        session.end_time = datetime.utcnow()
        session.total_duration_seconds = payload.total_duration_seconds
        session.overall_score = payload.overall_score
        session.overall_grade = payload.overall_grade
        if payload.confidence_score is not None: session.confidence_score = payload.confidence_score
        if payload.eye_contact_pct is not None: session.eye_contact_pct = payload.eye_contact_pct
        if payload.attention_score is not None: session.attention_score = payload.attention_score
        if payload.engagement_score is not None: session.engagement_score = payload.engagement_score
        if payload.dominant_emotion is not None: session.dominant_emotion = payload.dominant_emotion
        if payload.emotion_breakdown_json is not None: session.emotion_breakdown_json = payload.emotion_breakdown_json
        if payload.behavior_summary is not None: session.behavior_summary = payload.behavior_summary
        if payload.attention_events_count is not None: session.attention_events_count = payload.attention_events_count
        
        db.commit()
        db.refresh(session)
        return {
            "message": "Session completed",
            "session_id": session.session_id,
            "status": session.status,
            "end_time": session.end_time.isoformat(),
            "total_duration_seconds": session.total_duration_seconds
        }
    finally:
        db.close()

@router.post("/{session_id}/upload-recording")
async def upload_recording(session_id: str, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        filename = f"{session_id}.webm"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        video_url = f"/uploads/recordings/{filename}"
        session.video_url = video_url
        db.commit()
        db.refresh(session)
        
        return {
            "message": "Recording uploaded successfully",
            "session_id": session.session_id,
            "video_url": video_url
        }
    finally:
        db.close()

@router.post("/{session_id}/log-question")
def log_question(session_id: str, payload: QuestionLogSchema):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        question = InterviewQuestion(
            session_id=session_id,
            question_index=payload.question_index,
            question_text=payload.question_text,
            transcript=payload.transcript,
            duration_seconds=payload.duration_seconds,
            grammar_score=payload.grammar_score,
            pace_score=payload.pace_score,
            filler_score=payload.filler_score,
            pronunciation_score=payload.pronunciation_score,
            created_at=datetime.utcnow()
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return {"message": "Question logged", "id": question.id}
    finally:
        db.close()

@router.get("")
def list_sessions():
    db = SessionLocal()
    try:
        sessions = db.query(InterviewSession).order_by(InterviewSession.created_at.desc()).all()
        result = []
        for s in sessions:
            result.append({
                "id": s.id,
                "session_id": s.session_id,
                "candidate_name": s.candidate_name,
                "status": s.status,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "total_duration_seconds": s.total_duration_seconds,
                "video_url": s.video_url,
                "overall_score": s.overall_score,
                "overall_grade": s.overall_grade,
                "confidence_score": s.confidence_score,
                "eye_contact_pct": s.eye_contact_pct,
                "attention_score": s.attention_score,
                "engagement_score": s.engagement_score,
                "dominant_emotion": s.dominant_emotion,
                "behavior_summary": s.behavior_summary,
                "communication_score": s.communication_score,
                "technical_relevance_score": s.technical_relevance_score,
                "professionalism_score": s.professionalism_score,
                "performance_rating": s.performance_rating,
                "ai_feedback_json": s.ai_feedback_json,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })
        return result
    finally:
        db.close()

@router.get("/{session_id}")
def get_session_details(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()
        q_list = []
        for q in questions:
            q_list.append({
                "question_index": q.question_index,
                "question_text": q.question_text,
                "transcript": q.transcript,
                "duration_seconds": q.duration_seconds,
                "grammar_score": q.grammar_score,
                "pace_score": q.pace_score,
                "filler_score": q.filler_score,
                "pronunciation_score": q.pronunciation_score
            })
            
        return {
            "session_id": session.session_id,
            "candidate_name": session.candidate_name,
            "status": session.status,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_duration_seconds": session.total_duration_seconds,
            "video_url": session.video_url,
            "overall_score": session.overall_score,
            "overall_grade": session.overall_grade,
            "confidence_score": session.confidence_score,
            "eye_contact_pct": session.eye_contact_pct,
            "attention_score": session.attention_score,
            "engagement_score": session.engagement_score,
            "dominant_emotion": session.dominant_emotion,
            "emotion_breakdown_json": session.emotion_breakdown_json,
            "behavior_summary": session.behavior_summary,
            "communication_score": session.communication_score,
            "technical_relevance_score": session.technical_relevance_score,
            "professionalism_score": session.professionalism_score,
            "performance_rating": session.performance_rating,
            "ai_feedback_json": session.ai_feedback_json,
            "questions": q_list
        }
    finally:
        db.close()
