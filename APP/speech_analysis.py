from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import re
import math

router = APIRouter(prefix="/api/speech-analysis", tags=["speech-analysis"])

FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "actually",
    "literally", "so", "i mean", "right", "kind of", "sort of",
    "hmm", "ah", "well", "er", "you see", "at the end of the day"
]

GRAMMAR_RULES = [
    {
        "pattern": r"\b(i|you|we|they)\s+(is|was)\b",
        "message": "Subject-verb disagreement: Subject does not match 'is/was'.",
        "suggestion": "Use 'am/are' or 'were' instead."
    },
    {
        "pattern": r"\b(he|she|it)\s+(are|were)\b",
        "message": "Subject-verb disagreement: Singular third-person subject with plural verb.",
        "suggestion": "Use 'is' or 'was' instead."
    },
    {
        "pattern": r"\b(dont|cant|wont|isnt|arent|couldnt|shouldnt|wouldnt)\b",
        "message": "Missing apostrophe in contraction.",
        "suggestion": "Add apostrophe (e.g., don't, can't)."
    },
    {
        "pattern": r"\b(ain't|aint)\b",
        "message": "Informal contraction detected.",
        "suggestion": "Use 'is not', 'are not', or 'am not' for professional context."
    },
    {
        "pattern": r"\b(gonna|wanna|gotta)\b",
        "message": "Informal spoken slang detected.",
        "suggestion": "Use formal phrasing like 'going to', 'want to', or 'have to'."
    },
    {
        "pattern": r"\b(don't|doesn't|didn't|never|no|not)\s+\w+\s+(no|nothing|nobody|nowhere|neither|none)\b",
        "message": "Possible double negative detected.",
        "suggestion": "Rephrase to avoid double negatives."
    },
    {
        "pattern": r"\b(more|most)\s+\w+(er|est)\b",
        "message": "Double comparative or superlative used.",
        "suggestion": "Remove 'more' or 'most' when using -er or -est suffix."
    },
    {
        "pattern": r"\b(i\s+has|he\s+have|she\s+have|it\s+have)\b",
        "message": "Irregular verb conjugation error.",
        "suggestion": "Use 'I have' or 'he/she/it has'."
    }
]

class SpeechAnalysisRequest(BaseModel):
    transcript: str
    duration_seconds: Optional[float] = 0.0
    confidence_scores: Optional[List[float]] = None

@router.post("/analyze")
def analyze_speech_endpoint(payload: SpeechAnalysisRequest):
    transcript = payload.transcript.strip()
    duration = payload.duration_seconds or 0.0

    if not transcript:
        return {
            "transcript": "",
            "duration_seconds": 0,
            "word_count": 0,
            "speech_pace": {
                "wpm": 0,
                "status": "No Speech Detected",
                "score": 0,
                "feedback": "Please speak or record audio to perform pace analysis."
            },
            "filler_words": {
                "total_fillers": 0,
                "filler_ratio_percent": 0.0,
                "score": 100,
                "breakdown": {},
                "detected_instances": []
            },
            "grammar": {
                "score": 100,
                "total_issues": 0,
                "issues": []
            },
            "pronunciation": {
                "score": 100,
                "clarity_rating": "N/A",
                "unclear_words": [],
                "feedback": "No speech transcript available."
            },
            "communication_quality": {
                "overall_score": 0,
                "grade": "N/A",
                "metrics": {
                    "grammar_score": 0,
                    "pace_score": 0,
                    "filler_score": 0,
                    "pronunciation_score": 0,
                    "fluency_score": 0
                },
                "strengths": [],
                "improvements": [],
                "executive_summary": "No transcript provided."
            }
        }

    words = [w for w in re.split(r"\s+", transcript) if w]
    word_count = len(words)

    # 1. Speech Pace Analysis
    if duration > 0:
        wpm = round((word_count / duration) * 60, 1)
    else:
        # Default estimation (~ 130 wpm assumption if duration omitted)
        wpm = 130.0

    if wpm < 100:
        pace_status = "Too Slow"
        pace_score = max(50, int(100 - (100 - wpm) * 0.8))
        pace_feedback = "Your speaking pace is slower than ideal. Aim for 110-160 WPM for maximum engagement."
    elif 100 <= wpm <= 165:
        pace_status = "Optimal Pace"
        pace_score = 95 if (120 <= wpm <= 150) else 88
        pace_feedback = "Excellent speaking pace! Your pace maintains candidate clarity and engagement."
    else:
        pace_status = "Too Fast"
        pace_score = max(50, int(100 - (wpm - 165) * 0.7))
        pace_feedback = "Your speaking pace is fast. Try slowing down slightly to ensure clear articulation."

    # 2. Filler-Word Detection
    lower_transcript = transcript.lower()
    filler_counts = {}
    detected_fillers = []
    total_fillers = 0

    for filler in FILLER_WORDS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        matches = list(re.finditer(pattern, lower_transcript))
        if matches:
            count = len(matches)
            filler_counts[filler] = count
            total_fillers += count
            for m in matches:
                detected_fillers.append({
                    "word": filler,
                    "start": m.start(),
                    "end": m.end()
                })

    filler_ratio = round((total_fillers / max(1, word_count)) * 100, 1)
    if filler_ratio == 0:
        filler_score = 100
    elif filler_ratio <= 3:
        filler_score = 90
    elif filler_ratio <= 6:
        filler_score = 75
    elif filler_ratio <= 10:
        filler_score = 60
    else:
        filler_score = 45

    # 3. Grammar Checking
    grammar_issues = []
    for rule in GRAMMAR_RULES:
        matches = list(re.finditer(rule["pattern"], lower_transcript))
        for m in matches:
            matched_text = transcript[m.start():m.end()]
            grammar_issues.append({
                "matched_text": matched_text,
                "message": rule["message"],
                "suggestion": rule["suggestion"],
                "start": m.start(),
                "end": m.end()
            })

    grammar_deduction = len(grammar_issues) * 12
    grammar_score = max(40, 100 - grammar_deduction)

    # 4. Pronunciation Evaluation
    unclear_words = []
    if payload.confidence_scores and len(payload.confidence_scores) == len(words):
        avg_confidence = sum(payload.confidence_scores) / len(payload.confidence_scores)
        pron_score = round(avg_confidence * 100, 1)
        for w, conf in zip(words, payload.confidence_scores):
            if conf < 0.7:
                unclear_words.append(w)
    else:
        # Evaluate based on phonetic complexity & filler distortion
        complex_phoneme_words = [w for w in words if len(w) > 9 or w.lower() in ["specifically", "particularly", "phenomenon", "anonymity"]]
        base_pron = 92
        if len(complex_phoneme_words) > 0:
            base_pron += 3
        pron_score = max(60, min(98, base_pron - (total_fillers * 2)))

    if pron_score >= 88:
        pron_rating = "Excellent Clarity"
        pron_feedback = "Pronunciation is clear, distinct, and easily understandable."
    elif pron_score >= 75:
        pron_rating = "Good Clarity"
        pron_feedback = "Pronunciation is good overall with minor areas for articulation polish."
    else:
        pron_rating = "Needs Improvement"
        pron_feedback = "Some words were indistinct. Focus on enunciating key syllables clearly."

    # 5. Communication Quality Assessment
    fluency_score = max(40, min(100, int((pace_score + filler_score + pron_score) / 3)))

    overall_score = round(
        (grammar_score * 0.25) +
        (pace_score * 0.20) +
        (filler_score * 0.20) +
        (pron_score * 0.20) +
        (fluency_score * 0.15),
        1
    )

    if overall_score >= 90:
        grade = "A+"
    elif overall_score >= 80:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 60:
        grade = "C"
    else:
        grade = "D"

    strengths = []
    improvements = []

    if pace_score >= 85:
        strengths.append(f"Maintained an optimal speaking pace ({wpm} WPM).")
    else:
        improvements.append(f"Adjust speaking pace ({wpm} WPM). {pace_feedback}")

    if filler_score >= 85:
        strengths.append("Minimal filler word usage detected.")
    else:
        improvements.append(f"Reduce filler word frequency ({total_fillers} fillers used, {filler_ratio}% of response).")

    if grammar_score >= 90:
        strengths.append("Strong grammatical accuracy and professional sentence structure.")
    else:
        improvements.append(f"Review grammar accuracy ({len(grammar_issues)} issues found).")

    if pron_score >= 85:
        strengths.append("High speech clarity and distinct pronunciation.")
    else:
        improvements.append("Practice enunciation on complex words for clearer pronunciation.")

    exec_summary = (
        f"Candidate achieved an overall Communication Quality Score of {overall_score}/100 (Grade {grade}). "
        f"Spoke {word_count} words at {wpm} WPM with {total_fillers} filler words and {len(grammar_issues)} grammatical flags."
    )

    return {
        "transcript": transcript,
        "duration_seconds": duration,
        "word_count": word_count,
        "speech_pace": {
            "wpm": wpm,
            "status": pace_status,
            "score": pace_score,
            "feedback": pace_feedback
        },
        "filler_words": {
            "total_fillers": total_fillers,
            "filler_ratio_percent": filler_ratio,
            "score": filler_score,
            "breakdown": filler_counts,
            "detected_instances": detected_fillers
        },
        "grammar": {
            "score": grammar_score,
            "total_issues": len(grammar_issues),
            "issues": grammar_issues
        },
        "pronunciation": {
            "score": pron_score,
            "clarity_rating": pron_rating,
            "unclear_words": unclear_words,
            "feedback": pron_feedback
        },
        "communication_quality": {
            "overall_score": overall_score,
            "grade": grade,
            "metrics": {
                "grammar_score": grammar_score,
                "pace_score": pace_score,
                "filler_score": filler_score,
                "pronunciation_score": pron_score,
                "fluency_score": fluency_score
            },
            "strengths": strengths,
            "improvements": improvements,
            "executive_summary": exec_summary
        }
    }

@router.get("/fillers")
def get_filler_words_list():
    return {
        "filler_words": FILLER_WORDS
    }
