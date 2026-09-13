from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from APP.database import SessionLocal
from APP.models import ScheduledInterview, InterviewSession, InterviewQuestion
from APP.notifications import create_notification

router = APIRouter(prefix="/api/interviews", tags=["interviews-scheduling"])

class InterviewScheduleSchema(BaseModel):
    candidate_id: Optional[int] = 1
    candidate_name: str
    candidate_email: Optional[str] = "candidate@smarthire.ai"
    recruiter_id: Optional[int] = 1
    recruiter_name: Optional[str] = "Recruiter"
    interview_date: str
    interview_time: str
    notes: Optional[str] = ""

class InterviewUpdateSchema(BaseModel):
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    status: Optional[str] = None  # Scheduled, Completed, Cancelled, Rescheduled
    reminder_status: Optional[str] = None
    notes: Optional[str] = None

@router.post("/schedule")
def schedule_interview(payload: InterviewScheduleSchema):
    db = SessionLocal()
    try:
        scheduled = ScheduledInterview(
            candidate_id=payload.candidate_id or 1,
            candidate_name=payload.candidate_name,
            candidate_email=payload.candidate_email or "candidate@smarthire.ai",
            recruiter_id=payload.recruiter_id or 1,
            recruiter_name=payload.recruiter_name or "Recruiter",
            interview_date=payload.interview_date,
            interview_time=payload.interview_time,
            status="Scheduled",
            reminder_status="Pending",
            notes=payload.notes or "",
            created_at=datetime.utcnow()
        )
        db.add(scheduled)
        db.commit()
        db.refresh(scheduled)

        # Trigger notification & email
        title = f"Interview Scheduled: {payload.candidate_name}"
        msg = f"Your interview with {payload.recruiter_name} has been scheduled for {payload.interview_date} at {payload.interview_time}."
        create_notification(
            db,
            user_email=payload.candidate_email or "candidate@smarthire.ai",
            title=title,
            message=msg,
            notification_type="SCHEDULED",
            send_email=True
        )

        return {
            "status": "success",
            "message": "Interview successfully scheduled",
            "interview": {
                "id": scheduled.id,
                "candidate_name": scheduled.candidate_name,
                "recruiter_name": scheduled.recruiter_name,
                "interview_date": scheduled.interview_date,
                "interview_time": scheduled.interview_time,
                "status": scheduled.status,
                "reminder_status": scheduled.reminder_status,
                "notes": scheduled.notes
            }
        }
    finally:
        db.close()

@router.get("/upcoming")
def get_upcoming_interviews(candidate_id: Optional[int] = None):
    db = SessionLocal()
    try:
        query = db.query(ScheduledInterview).filter(ScheduledInterview.status != "Cancelled")
        if candidate_id:
            query = query.filter(ScheduledInterview.candidate_id == candidate_id)
        
        interviews = query.order_by(ScheduledInterview.created_at.desc()).all()
        return [
            {
                "id": item.id,
                "candidate_id": item.candidate_id,
                "candidate_name": item.candidate_name,
                "candidate_email": item.candidate_email,
                "recruiter_id": item.recruiter_id,
                "recruiter_name": item.recruiter_name,
                "interview_date": item.interview_date,
                "interview_time": item.interview_time,
                "status": item.status,
                "reminder_status": item.reminder_status,
                "notes": item.notes,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            for item in interviews
        ]
    finally:
        db.close()

@router.get("/history/{candidate_id}")
def get_interview_history(candidate_id: int):
    db = SessionLocal()
    try:
        # Retrieve all interview sessions for the candidate
        sessions = db.query(InterviewSession).filter(
            (InterviewSession.candidate_id == candidate_id) | (InterviewSession.candidate_id == 1)
        ).order_by(InterviewSession.created_at.desc()).all()

        history = []
        for s in sessions:
            history.append({
                "id": s.id,
                "session_id": s.session_id,
                "candidate_name": s.candidate_name,
                "date": s.start_time.strftime("%Y-%m-%d") if s.start_time else (s.created_at.strftime("%Y-%m-%d") if s.created_at else "N/A"),
                "start_time": s.start_time.strftime("%H:%M:%S") if s.start_time else "N/A",
                "end_time": s.end_time.strftime("%H:%M:%S") if s.end_time else "N/A",
                "duration_seconds": s.total_duration_seconds or 0.0,
                "status": s.status or "COMPLETED",
                "overall_score": s.overall_score or 0.0,
                "overall_grade": s.overall_grade or "N/A",
                "communication_score": s.communication_score or 0.0,
                "confidence_score": s.confidence_score or 0.0,
                "technical_score": s.technical_relevance_score or 0.0,
                "professionalism_score": s.professionalism_score or 0.0,
                "ai_feedback": s.ai_feedback_json,
                "behavior_summary": s.behavior_summary,
                "video_url": s.video_url
            })
        return history
    finally:
        db.close()

@router.put("/{id}")
def update_scheduled_interview(id: int, payload: InterviewUpdateSchema):
    db = SessionLocal()
    try:
        item = db.query(ScheduledInterview).filter(ScheduledInterview.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Scheduled interview not found")

        if payload.interview_date is not None: item.interview_date = payload.interview_date
        if payload.interview_time is not None: item.interview_time = payload.interview_time
        if payload.status is not None: item.status = payload.status
        if payload.reminder_status is not None: item.reminder_status = payload.reminder_status
        if payload.notes is not None: item.notes = payload.notes

        db.commit()

        # Send status notification
        title = f"Interview Status Updated: {item.candidate_name}"
        msg = f"Your scheduled interview status is now: {item.status} for {item.interview_date} at {item.interview_time}."
        create_notification(
            db,
            user_email=item.candidate_email or "candidate@smarthire.ai",
            title=title,
            message=msg,
            notification_type="STATUS_UPDATE",
            send_email=True
        )

        return {"status": "success", "message": "Interview updated successfully", "id": item.id}
    finally:
        db.close()

@router.delete("/{id}")
def delete_scheduled_interview(id: int):
    db = SessionLocal()
    try:
        item = db.query(ScheduledInterview).filter(ScheduledInterview.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Scheduled interview not found")

        item.status = "Cancelled"
        db.commit()
        return {"status": "success", "message": "Interview cancelled successfully", "id": id}
    finally:
        db.close()
