from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from APP.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="Candidate")  # Candidate, Recruiter, Admin
    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    interview_id = Column(Integer, nullable=True, default=1)
    candidate_id = Column(Integer, nullable=True, default=1)
    candidate_name = Column(String(100), default="Candidate")
    status = Column(String(50), default="CREATED")  # CREATED, IN_PROGRESS, PAUSED, COMPLETED
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Float, default=0.0)
    video_url = Column(String(255), nullable=True)
    overall_score = Column(Float, nullable=True)
    overall_grade = Column(String(10), nullable=True)
    confidence_score = Column(Float, nullable=True)
    eye_contact_pct = Column(Float, nullable=True)
    attention_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    dominant_emotion = Column(String(50), nullable=True)
    emotion_breakdown_json = Column(Text, nullable=True)
    behavior_summary = Column(Text, nullable=True)
    attention_events_count = Column(Integer, default=0)
    communication_score = Column(Float, nullable=True)
    technical_relevance_score = Column(Float, nullable=True)
    professionalism_score = Column(Float, nullable=True)
    performance_rating = Column(String(50), nullable=True)
    ai_feedback_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    question_index = Column(Integer, nullable=False)
    question_text = Column(String(500), nullable=False)
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    grammar_score = Column(Float, nullable=True)
    pace_score = Column(Float, nullable=True)
    filler_score = Column(Float, nullable=True)
    pronunciation_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledInterview(Base):
    __tablename__ = "scheduled_interviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=True, default=1)
    candidate_name = Column(String(100), nullable=False)
    candidate_email = Column(String(100), nullable=True)
    recruiter_id = Column(Integer, nullable=True, default=1)
    recruiter_name = Column(String(100), default="Recruiter")
    interview_date = Column(String(50), nullable=False)
    interview_time = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, default=30)
    interview_type = Column(String(100), default="Technical & Behavioral AI Interview")
    status = Column(String(50), default="Scheduled")  # Scheduled, Ongoing, Completed, Cancelled, Missed, Rescheduled
    reminder_status = Column(String(50), default="Pending")  # Pending, Sent
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(100), nullable=True)
    recruiter_id = Column(Integer, nullable=True)
    scheduled_interview_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="INFO")  # SCHEDULED, REMINDER, REPORT, ALERT, SYSTEM
    is_read = Column(Integer, default=0)  # 0 = false, 1 = true
    is_dismissed = Column(Integer, default=0)  # 0 = false, 1 = true
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateReminder(Base):
    __tablename__ = "candidate_reminders"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, default=1)
    candidate_email = Column(String(100), nullable=True)
    scheduled_interview_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    reminder_time = Column(String(50), nullable=False)
    lead_time_minutes = Column(Integer, default=10)
    status = Column(String(50), default="Pending")  # Pending, Triggered, Completed, Snoozed, Dismissed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)