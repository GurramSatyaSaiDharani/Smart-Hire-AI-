from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import re

from APP.database import SessionLocal
from APP.models import InterviewSession

router = APIRouter(prefix="/api/feedback-scoring", tags=["ai-feedback-scoring"])

class FeedbackScoringRequest(BaseModel):
    session_id: Optional[str] = None
    transcript: str
    duration_seconds: Optional[float] = 0.0
    # Section 6 Computer Vision Telemetry
    confidence_score: Optional[float] = 90.0
    eye_contact_pct: Optional[float] = 92.0
    attention_score: Optional[float] = 95.0
    engagement_score: Optional[float] = 88.0
    # Speech Quality Metrics
    grammar_score: Optional[float] = 90.0
    pace_score: Optional[float] = 85.0
    filler_score: Optional[float] = 85.0
    pronunciation_score: Optional[float] = 90.0
    question_text: Optional[str] = ""

TECHNICAL_KEYWORDS = [
    "architecture", "design", "algorithm", "database", "api", "rest", "graphql",
    "scalable", "optimization", "performance", "lead", "manage", "agile",
    "ci/cd", "deployment", "security", "framework", "testing", "refactor",
    "debug", "cache", "async", "event", "microservices", "object", "system",
    "frontend", "backend", "cloud", "aws", "docker", "kubernetes", "python"
]

@router.post("/evaluate")
def evaluate_interview_performance(payload: FeedbackScoringRequest):
    transcript = payload.transcript.strip()
    words = [w for w in re.split(r"\s+", transcript) if w]
    word_count = len(words)
    lower_tx = transcript.lower()

    # 1. Communication Score (30%)
    # Speech clarity, grammar quality, filler-word frequency, speaking pace, response completeness
    speech_clarity = payload.pronunciation_score or 90.0
    grammar_qual = payload.grammar_score or 90.0
    filler_freq = payload.filler_score or 85.0
    speaking_pace = payload.pace_score or 85.0
    
    # Response completeness based on length depth (ideal 40-150 words per question)
    if word_count >= 50:
        completeness = 95.0
    elif word_count >= 25:
        completeness = 80.0
    elif word_count >= 10:
        completeness = 65.0
    else:
        completeness = 40.0

    communication_score = round(
        (speech_clarity * 0.25) +
        (grammar_qual * 0.25) +
        (filler_freq * 0.20) +
        (speaking_pace * 0.15) +
        (completeness * 0.15),
        1
    )

    # 2. Confidence Score (25%)
    # Eye-contact consistency, facial engagement, response hesitation, speaking confidence, attention level
    eye_contact = payload.eye_contact_pct or 92.0
    facial_engagement = payload.engagement_score or 88.0
    attention = payload.attention_score or 95.0
    speaking_confidence = payload.confidence_score or 90.0
    
    # Hesitation factor derived from filler score & confidence
    hesitation_factor = max(50.0, min(100.0, ((payload.filler_score or 85.0) + (payload.confidence_score or 90.0)) / 2.0))

    confidence_score = round(
        (eye_contact * 0.25) +
        (facial_engagement * 0.25) +
        (speaking_confidence * 0.25) +
        (attention * 0.15) +
        (hesitation_factor * 0.10),
        1
    )

    # 3. Technical Relevance Score (30%)
    # Technical accuracy, keyword relevance, problem-solving ability, domain knowledge, answer completeness
    matched_kw = [kw for kw in TECHNICAL_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_tx)]
    kw_count = len(matched_kw)

    if kw_count >= 5:
        kw_relevance = 96.0
    elif kw_count >= 3:
        kw_relevance = 88.0
    elif kw_count >= 1:
        kw_relevance = 78.0
    else:
        kw_relevance = 65.0

    # Problem solving indicators (words like solved, challenge, outcome, impact, result, approach, built, created)
    problem_solving_words = ["challenge", "problem", "solution", "resolve", "lead", "manage", "impact", "built", "implemented", "result", "approach", "engineered"]
    ps_matches = [w for w in problem_solving_words if w in lower_tx]
    ps_score = min(98.0, 70.0 + len(ps_matches) * 7.0)

    tech_accuracy = min(98.0, kw_relevance * 0.5 + ps_score * 0.5)
    domain_knowledge = min(98.0, 65.0 + (kw_count * 6.0))

    technical_relevance_score = round(
        (tech_accuracy * 0.25) +
        (kw_relevance * 0.25) +
        (ps_score * 0.25) +
        (domain_knowledge * 0.15) +
        (completeness * 0.10),
        1
    )

    # 4. Professionalism Score (15%)
    # Time management, response organization, professional communication, interview etiquette
    dur = payload.duration_seconds or 0.0
    if 20 <= dur <= 180 or word_count >= 30:
        time_mgmt = 95.0
    elif dur > 0:
        time_mgmt = 75.0
    else:
        time_mgmt = 85.0

    # Lack of informal slang (gonna, wanna, ain't)
    informal_slang = len(re.findall(r"\b(gonna|wanna|ain't|aint|yeah|nah)\b", lower_tx))
    prof_comm = max(50.0, 98.0 - (informal_slang * 10.0))

    resp_org = min(96.0, 75.0 + (word_count > 30) * 15.0 + (len(ps_matches) > 0) * 6.0)
    interview_etiquette = min(98.0, (eye_contact * 0.5) + (attention * 0.5))

    professionalism_score = round(
        (time_mgmt * 0.25) +
        (resp_org * 0.25) +
        (prof_comm * 0.25) +
        (interview_etiquette * 0.25),
        1
    )

    # Overall Score Formula: (Communication * 30%) + (Confidence * 25%) + (Technical Relevance * 30%) + (Professionalism * 15%)
    overall_score = round(
        (communication_score * 0.30) +
        (confidence_score * 0.25) +
        (technical_relevance_score * 0.30) +
        (professionalism_score * 0.15),
        1
    )

    # Performance Rating Rubric:
    # 90-100: Excellent
    # 75-89: Good
    # 60-74: Average
    # 40-59: Needs Improvement
    # Below 40: Poor
    if overall_score >= 90.0:
        performance_rating = "Excellent"
        rating_badge_color = "#10b981"
    elif overall_score >= 75.0:
        performance_rating = "Good"
        rating_badge_color = "#2563eb"
    elif overall_score >= 60.0:
        performance_rating = "Average"
        rating_badge_color = "#f59e0b"
    elif overall_score >= 40.0:
        performance_rating = "Needs Improvement"
        rating_badge_color = "#ea580c"
    else:
        performance_rating = "Poor"
        rating_badge_color = "#ef4444"

    # AI Feedback Generation
    strengths = []
    weaknesses = []
    improvements = []
    practice_recs = []
    learning_resources = []

    # Populate Strengths & Weaknesses
    if communication_score >= 85:
        strengths.append(f"High verbal communication quality ({communication_score}%) with clear articulation and pace.")
    else:
        weaknesses.append(f"Communication score ({communication_score}%) indicates minor filler usage or pace variance.")
        improvements.append("Practice speaking with structured pauses instead of filler words (um, like).")

    if confidence_score >= 85:
        strengths.append(f"Strong confidence posture ({confidence_score}%) and consistent camera eye-contact.")
    else:
        weaknesses.append(f"Eye contact or posture hesitation reduced confidence index to {confidence_score}%.")
        improvements.append("Maintain direct lens alignment during response delivery.")

    if technical_relevance_score >= 80:
        strengths.append(f"Rich technical vocabulary and problem-solving depth ({technical_relevance_score}% relevance).")
    else:
        weaknesses.append(f"Technical keyword density and problem-solving depth were moderate ({technical_relevance_score}%).")
        improvements.append("Incorporate specific technical terms, architecture patterns, and quantitative outcomes.")

    if professionalism_score >= 85:
        strengths.append(f"Excellent professional etiquette ({professionalism_score}%) and structured answer delivery.")
    else:
        weaknesses.append(f"Response organization and timing can be polished ({professionalism_score}%).")
        improvements.append("Use the STAR framework (Situation, Task, Action, Result) for structured storytelling.")

    if not strengths:
        strengths.append("Demonstrated willingness to tackle complex technical questions with steady tone.")

    # Practice Recommendations
    practice_recs.append("Conduct 2 mock practice sessions using STAR response structure for system design questions.")
    practice_recs.append("Record candidate responses with web speech active to monitor filler word suppression.")
    practice_recs.append("Practice maintaining 85%+ camera lens eye-contact during answer delivery.")

    # Learning Resources
    learning_resources.append({"title": "STAR Method Interview Masterclass", "type": "Guide", "url": "https://en.wikipedia.org/wiki/Situation,_task,_action,_result"})
    learning_resources.append({"title": "Technical Communication & System Design Blueprint", "type": "Handbook", "url": "https://github.com/donnemartin/system-design-primer"})
    learning_resources.append({"title": "Executive Presentation & Posture Guide", "type": "Article", "url": "https://hbr.org/2013/06/how-to-improve-your-speaking-pace"})

    ai_feedback = {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_suggestions": improvements,
        "practice_recommendations": practice_recs,
        "learning_resources": learning_resources
    }

    # Save to Database if session_id provided
    if payload.session_id:
        db = SessionLocal()
        try:
            session = db.query(InterviewSession).filter(InterviewSession.session_id == payload.session_id).first()
            if session:
                session.overall_score = overall_score
                session.overall_grade = performance_rating
                session.communication_score = communication_score
                session.technical_relevance_score = technical_relevance_score
                session.professionalism_score = professionalism_score
                session.performance_rating = performance_rating
                session.ai_feedback_json = json.dumps(ai_feedback)
                db.commit()
        except Exception as e:
            print("Notice: session update failed", e)
        finally:
            db.close()

    return {
        "status": "success",
        "session_id": payload.session_id,
        "overall_score": overall_score,
        "performance_rating": performance_rating,
        "rating_badge_color": rating_badge_color,
        "scores_breakdown": {
            "communication_score": communication_score,
            "confidence_score": confidence_score,
            "technical_relevance_score": technical_relevance_score,
            "professionalism_score": professionalism_score
        },
        "weights": {
            "communication_weight": "30%",
            "confidence_weight": "25%",
            "technical_relevance_weight": "30%",
            "professionalism_weight": "15%"
        },
        "rubric_mapping": {
            "90-100": "Excellent",
            "75-89": "Good",
            "60-74": "Average",
            "40-59": "Needs Improvement",
            "Below 40": "Poor"
        },
        "ai_feedback": ai_feedback
    }

@router.get("/session/{session_id}")
def get_session_feedback(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        feedback = {}
        if session.ai_feedback_json:
            try:
                feedback = json.loads(session.ai_feedback_json)
            except Exception:
                pass

        return {
            "session_id": session.session_id,
            "candidate_name": session.candidate_name,
            "overall_score": session.overall_score or 85.0,
            "performance_rating": session.performance_rating or "Good",
            "communication_score": session.communication_score or 88.0,
            "confidence_score": session.confidence_score or 90.0,
            "technical_relevance_score": session.technical_relevance_score or 82.0,
            "professionalism_score": session.professionalism_score or 86.0,
            "ai_feedback": feedback
        }
    finally:
        db.close()
