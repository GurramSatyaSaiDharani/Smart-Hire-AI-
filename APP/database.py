from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)

try:
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            pass
    else:
        raise Exception("No DATABASE_URL provided")
except Exception as e:
    print(f"PostgreSQL connection failed ({e}). Falling back to SQLite.")
    DATABASE_URL = "sqlite:///./smart_hire.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def sync_db_schema():
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "interview_sessions" in tables:
            columns = [c["name"] for c in inspector.get_columns("interview_sessions")]
            with engine.begin() as conn:
                if "candidate_name" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN candidate_name VARCHAR(100) DEFAULT 'Candidate'"))
                if "video_url" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN video_url VARCHAR(255)"))
                if "overall_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN overall_score FLOAT"))
                if "overall_grade" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN overall_grade VARCHAR(10)"))
                if "total_duration_seconds" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN total_duration_seconds FLOAT DEFAULT 0.0"))
                if "status" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN status VARCHAR(50) DEFAULT 'CREATED'"))
                if "start_time" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN start_time TIMESTAMP"))
                if "end_time" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN end_time TIMESTAMP"))
                if "confidence_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN confidence_score FLOAT"))
                if "eye_contact_pct" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN eye_contact_pct FLOAT"))
                if "attention_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN attention_score FLOAT"))
                if "engagement_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN engagement_score FLOAT"))
                if "dominant_emotion" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN dominant_emotion VARCHAR(50)"))
                if "emotion_breakdown_json" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN emotion_breakdown_json TEXT"))
                if "behavior_summary" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN behavior_summary TEXT"))
                if "attention_events_count" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN attention_events_count INTEGER DEFAULT 0"))
                if "communication_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN communication_score FLOAT"))
                if "technical_relevance_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN technical_relevance_score FLOAT"))
                if "professionalism_score" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN professionalism_score FLOAT"))
                if "performance_rating" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN performance_rating VARCHAR(50)"))
                if "ai_feedback_json" not in columns:
                    conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN ai_feedback_json TEXT"))

        if "interview_questions" in tables:
            iq_columns = [c["name"] for c in inspector.get_columns("interview_questions")]
            with engine.begin() as conn:
                if "question_index" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN question_index INTEGER DEFAULT 0"))
                if "question_text" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN question_text VARCHAR(500) DEFAULT ''"))
                if "transcript" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN transcript TEXT"))
                if "duration_seconds" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN duration_seconds FLOAT DEFAULT 0.0"))
                if "grammar_score" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN grammar_score FLOAT"))
                if "pace_score" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN pace_score FLOAT"))
                if "filler_score" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN filler_score FLOAT"))
                if "pronunciation_score" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN pronunciation_score FLOAT"))
                if "created_at" not in iq_columns:
                    conn.execute(text("ALTER TABLE interview_questions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

        if "scheduled_interviews" in tables:
            si_columns = [c["name"] for c in inspector.get_columns("scheduled_interviews")]
            with engine.begin() as conn:
                if "duration_minutes" not in si_columns:
                    conn.execute(text("ALTER TABLE scheduled_interviews ADD COLUMN duration_minutes INTEGER DEFAULT 30"))
                if "interview_type" not in si_columns:
                    conn.execute(text("ALTER TABLE scheduled_interviews ADD COLUMN interview_type VARCHAR(100) DEFAULT 'Technical & Behavioral AI Interview'"))

        if "notifications" in tables:
            n_columns = [c["name"] for c in inspector.get_columns("notifications")]
            with engine.begin() as conn:
                if "recruiter_id" not in n_columns:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN recruiter_id INTEGER"))
                if "scheduled_interview_id" not in n_columns:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN scheduled_interview_id INTEGER"))
                if "is_dismissed" not in n_columns:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN is_dismissed INTEGER DEFAULT 0"))

        if "user" in tables:
            user_columns = [c["name"] for c in inspector.get_columns("user")]
            with engine.begin() as conn:
                if "role" not in user_columns:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN role VARCHAR(50) DEFAULT 'Candidate'"))
                if "created_at" not in user_columns:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    except Exception as e:
        print("Schema sync notice:", e)