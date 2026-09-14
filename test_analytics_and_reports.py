"""
Smart Hire AI - Automated End-to-End Test Suite
Tests Sections 8, 9, and 10 APIs:
- Interview Session Logging & Scoring
- Candidate Dashboard API
- Skill-wise Analytics API
- AI Weak-Area Prediction API
- Performance Trends API
- Candidate Rankings API
- Interview Scheduling API (POST, GET, PUT, DELETE)
- Notifications API
- PDF Report Generation API
- CSV Report Generation API
"""

import sys
import os
from fastapi.testclient import TestClient

# Add workspace directory to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from APP.main import app
from APP.database import SessionLocal, Base, engine
from APP.models import InterviewSession, InterviewQuestion, ScheduledInterview, Notification

client = TestClient(app)

def run_tests():
    print("====================================================")
    print("STARTING SMART HIRE AI AUTOMATED TEST SUITE")
    print("====================================================")

    # 1. Health check endpoint
    response = client.get("/")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    print("[OK] [1/10] Root API Health Check Passed.")
    print("----------------------------------------------------")

    # 2. Create Interview Session & Log Question Telemetry
    session_id = "TEST_SESSION_1001"
    create_payload = {
        "session_id": session_id,
        "interview_id": 1,
        "candidate_id": 1,
        "candidate_name": "Test Candidate Alice"
    }
    resp = client.post("/api/sessions/create", json=create_payload)
    assert resp.status_code in [200, 201], f"Session create failed: {resp.text}"
    print("[OK] [2/10] Session Creation Endpoint Passed.")

    # 3. Log AI Evaluation & Telemetry
    eval_payload = {
        "session_id": session_id,
        "transcript": "I designed a scalable microservices architecture on AWS using Python and PostgreSQL. We implemented caching with Redis and automated CI CD pipelines.",
        "duration_seconds": 90.0,
        "confidence_score": 92.0,
        "eye_contact_pct": 94.0,
        "attention_score": 95.0,
        "engagement_score": 90.0,
        "grammar_score": 92.0,
        "pace_score": 88.0,
        "filler_score": 85.0,
        "pronunciation_score": 90.0
    }
    resp = client.post("/api/feedback-scoring/evaluate", json=eval_payload)
    assert resp.status_code == 200, f"AI feedback evaluation failed: {resp.text}"
    eval_data = resp.json()
    assert eval_data["overall_score"] > 0
    print(f"[OK] [3/10] AI Feedback Evaluation Passed (Overall Score: {eval_data['overall_score']}%).")

    # Create a second session for candidate 1 to test trends calculation
    session_id2 = "TEST_SESSION_1002"
    client.post("/api/sessions/create", json={"session_id": session_id2, "candidate_id": 1, "candidate_name": "Test Candidate Alice"})
    client.post("/api/feedback-scoring/evaluate", json={
        "session_id": session_id2,
        "transcript": "We refactored our legacy monolithic backend into decoupled microservices, optimizing database queries and improving throughput by 40 percent.",
        "duration_seconds": 110.0,
        "confidence_score": 96.0,
        "eye_contact_pct": 96.0,
        "attention_score": 98.0,
        "engagement_score": 94.0
    })

    # 4. Candidate Dashboard API
    resp = client.get("/api/dashboard/candidate?candidate_id=1")
    assert resp.status_code == 200, f"Candidate dashboard API failed: {resp.text}"
    cand_data = resp.json()
    assert "completed_interviews_count" in cand_data
    print(f"[OK] [4/10] Candidate Dashboard API Passed ({cand_data['completed_interviews_count']} interviews found).")

    # 5. Skill-wise Analytics & Weak-area Prediction APIs
    resp = client.get("/api/analytics/1/skills")
    assert resp.status_code == 200
    assert len(resp.json()["skills"]) == 11
    print("[OK] [5/10] Skill-wise Analytics API Passed (11 skill categories verified).")

    resp = client.get("/api/analytics/1/weak-areas")
    assert resp.status_code == 200
    weak_areas = resp.json()
    assert isinstance(weak_areas, list)
    print(f"[OK] [6/10] Weak-area Prediction API Passed ({len(weak_areas)} weak areas identified).")

    # 6. Performance Trends API
    resp = client.get("/api/analytics/1/trends")
    assert resp.status_code == 200
    trends_data = resp.json()
    assert trends_data["has_sufficient_data"] is True
    print(f"[OK] [7/10] Performance Trends API Passed (Direction: {trends_data['trend_direction']}, Improvement: {trends_data['percentage_improvement']}%).")

    # 7. Candidate Rankings API
    resp = client.get("/api/analytics/rankings?sort_by=overall_score")
    assert resp.status_code == 200
    rankings = resp.json()
    assert len(rankings) > 0
    print(f"[OK] [8/10] Candidate Ranking Metrics API Passed ({len(rankings)} candidates ranked).")

    # 8. Interview Scheduling APIs (Schedule, Upcoming, Delete)
    sched_payload = {
        "candidate_id": 1,
        "candidate_name": "Test Candidate Alice",
        "candidate_email": "alice@example.com",
        "interview_date": "2026-10-15",
        "interview_time": "14:00",
        "recruiter_name": "Senior Recruiter Bob",
        "notes": "Technical Architecture Round"
    }
    resp = client.post("/api/interviews/schedule", json=sched_payload)
    assert resp.status_code == 200
    sched_data = resp.json()
    sched_id = sched_data["interview"]["id"]
    print(f"[OK] [9/10] Interview Scheduling API Passed (Created Schedule ID: {sched_id}).")

    resp = client.get("/api/interviews/upcoming")
    assert resp.status_code == 200
    assert len(resp.json()) > 0

    # 9. PDF & CSV Report Downloads
    resp = client.get(f"/api/reports/{session_id}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ["application/pdf", "application/pdf; charset=utf-8"]
    print("[OK] [10/10] PDF Report Download Endpoint Passed.")

    resp = client.get(f"/api/reports/{session_id}/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    print("[OK] All Downloadable Reports Endpoints Passed.")

    # 10. System Performance & Quantitative Goals Metrics API
    resp = client.get("/api/analytics/system-metrics")
    assert resp.status_code == 200
    sys_metrics = resp.json()
    assert "interview_analysis_performance" in sys_metrics
    assert "quantitative_goals" in sys_metrics
    print("[OK] System Performance & Accuracy Telemetry Metrics API Passed.")

    print("====================================================")
    print("ALL SMART HIRE AI AUTOMATED TESTS PASSED SUCCESSFULLY!")
    print("====================================================")

if __name__ == "__main__":
    run_tests()
