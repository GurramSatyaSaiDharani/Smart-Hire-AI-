// Speech-to-Text & Communication Analysis JS Module

const API_BASE = (window.location.origin && window.location.origin !== "null" && window.location.protocol.startsWith("http")) ? window.location.origin : "http://127.0.0.1:8000";

let recognition = null;
let isRecording = false;
let startTime = 0;
let timerInterval = null;
let speechDurationSeconds = 0;
let wordConfidences = [];

// Initialize Web Speech API if supported by browser
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Web Speech API not supported in this browser. Manual input mode enabled.");
        const statusEl = document.getElementById("micStatusText");
        if (statusEl) {
            statusEl.innerText = "Browser mic recognition unavailable. Use preset sample or type below.";
        }
        return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';

    rec.onstart = function() {
        isRecording = true;
        startTime = Date.now();
        speechDurationSeconds = 0;
        wordConfidences = [];
        updateMicUI(true);
        startTimer();
    };

    rec.onresult = function(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            const result = event.results[i];
            const text = result[0].transcript;
            const confidence = result[0].confidence || 0.90;

            if (result.isFinal) {
                finalTranscript += text + ' ';
                // Store confidence info per word
                const words = text.trim().split(/\s+/);
                words.forEach(w => {
                    if (w) wordConfidences.push({ word: w, confidence: confidence });
                });
            } else {
                interimTranscript += text;
            }
        }

        const liveText = (finalTranscript + interimTranscript).trim();
        const inputArea = document.getElementById("transcriptInput");
        if (inputArea && liveText) {
            inputArea.value = liveText;
        }
    };

    rec.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        stopRecording();
        const statusEl = document.getElementById("micStatusText");
        if (statusEl) {
            statusEl.innerText = "Mic error: " + event.error;
        }
    };

    rec.onend = function() {
        if (isRecording) {
            stopRecording();
        }
    };

    return rec;
}

function toggleMicRecording() {
    if (!recognition) {
        recognition = initSpeechRecognition();
    }

    if (!recognition) {
        alert("Web Speech API is not supported in your current browser. You can type or paste your speech text into the transcript area below and click 'Analyze Communication'!");
        return;
    }

    if (isRecording) {
        recognition.stop();
        stopRecording();
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.error("Failed to start mic:", e);
            stopRecording();
        }
    }
}

function stopRecording() {
    isRecording = false;
    if (timerInterval) clearInterval(timerInterval);
    updateMicUI(false);
    
    // Automatically calculate duration
    if (startTime > 0) {
        speechDurationSeconds = Math.max(1, Math.round((Date.now() - startTime) / 1000));
        const durInput = document.getElementById("speechDurationInput");
        if (durInput) durInput.value = speechDurationSeconds;
    }
}

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    const timerDisplay = document.getElementById("recordTimer");
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        if (timerDisplay) timerDisplay.innerText = `${mins}:${secs}`;
    }, 1000);
}

function updateMicUI(active) {
    const btn = document.getElementById("startMicBtn");
    const statusText = document.getElementById("micStatusText");
    const pulseDot = document.getElementById("recordingDot");

    if (active) {
        if (btn) {
            btn.innerText = "⏹ Stop Listening";
            btn.className = "mic-btn recording";
        }
        if (statusText) statusText.innerText = "Listening to live speech...";
        if (pulseDot) pulseDot.style.display = "inline-block";
    } else {
        if (btn) {
            btn.innerText = "🎙️ Start Real-Time Speech";
            btn.className = "mic-btn";
        }
        if (statusText) statusText.innerText = "Click to start speaking into your microphone";
        if (pulseDot) pulseDot.style.display = "none";
    }
}

// Preset Sample Loader for quick testing
function loadSampleTranscript() {
    const sampleText = "Um, hello everyone. I am, like, applying for the Senior Software Developer role. Basically, I have over 5 years of experience with Python and JavaScript. You know, I don't have no problem working under tight deadlines, and I always ensure the quality is high. So, actually, I am very excited to join your team.";
    
    const inputArea = document.getElementById("transcriptInput");
    const durInput = document.getElementById("speechDurationInput");
    
    if (inputArea) inputArea.value = sampleText;
    if (durInput) durInput.value = 24; // 24 seconds sample speech
    
    // Automatically submit for analysis
    analyzeCommunication();
}

async function analyzeCommunication() {
    const transcriptText = document.getElementById("transcriptInput")?.value || "";
    const durationInput = document.getElementById("speechDurationInput")?.value || 10;
    const duration = parseFloat(durationInput) || 10.0;

    if (!transcriptText.trim()) {
        alert("Please speak into the microphone or enter a speech transcript to analyze!");
        return;
    }

    const payload = {
        transcript: transcriptText,
        duration_seconds: duration,
        word_confidences: wordConfidences.length > 0 ? wordConfidences : null
    };

    const resultsContainer = document.getElementById("analysisResultsDashboard");
    if (resultsContainer) {
        resultsContainer.innerHTML = `<div class="loading-spinner">Analyzing Speech & Communication Metrics...</div>`;
    }

    try {
        const response = await fetch(`${API_BASE}/speech/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        renderAnalysisResults(data);
    } catch (err) {
        console.error("Analysis request failed:", err);
        if (resultsContainer) {
            resultsContainer.innerHTML = `<div class="error-box">Analysis Error: ${err.message}. Make sure backend server is running at ${API_BASE}.</div>`;
        }
    }
}

function renderAnalysisResults(data) {
    const container = document.getElementById("analysisResultsDashboard");
    if (!container) return;

    const g = data.grammar;
    const f = data.filler_words;
    const p = data.speech_pace;
    const pr = data.pronunciation;
    const q = data.communication_quality;

    // Determine color badges
    const qualityColor = q.overall_score >= 85 ? "#28a745" : (q.overall_score >= 70 ? "#ffc107" : "#dc3545");
    const paceBadgeColor = p.status === "Optimal Pace" ? "#28a745" : "#fd7e14";

    let fillerItemsHTML = "";
    if (Object.keys(f.detected_words).length > 0) {
        fillerItemsHTML = Object.entries(f.detected_words)
            .map(([word, count]) => `<span class="filler-tag">"${word}" × ${count}</span>`)
            .join(" ");
    } else {
        fillerItemsHTML = "<span class="clean-tag">✨ Zero filler words detected! Outstanding clarity.</span>";
    }

    let grammarIssuesHTML = "";
    if (g.issues.length > 0) {
        grammarIssuesHTML = g.issues.map(iss => `<li class="issue-item">⚠️ ${iss}</li>`).join("");
    } else {
        grammarIssuesHTML = "<li class="success-item">✅ No grammatical errors detected!</li>";
    }

    let grammarSuggestionsHTML = g.suggestions.map(sug => `<li>💡 ${sug}</li>`).join("");
    let summaryHTML = q.summary.map(s => `<li>📌 ${s}</li>`).join("");

    container.innerHTML = `
        <!-- 6. Communication Quality Assessment Banner -->
        <div class="card quality-banner" style="border-left: 6px solid ${qualityColor}">
            <div class="quality-header">
                <div>
                    <h2>5. Speech-to-Text & Communication Analysis</h2>
                    <p class="subtitle">Comprehensive evaluation of candidate spoken response</p>
                </div>
                <div class="score-badge-circle" style="background-color: ${qualityColor}">
                    <span class="score-num">${q.overall_score}</span>
                    <span class="score-label">/ 100</span>
                </div>
            </div>
            <div class="rating-tag">Overall Rating: <strong>${q.rating}</strong></div>
            <ul class="summary-list">${summaryHTML}</ul>
        </div>

        <div class="features-grid">
            <!-- 1. Real-time Speech Transcription -->
            <div class="card feature-card">
                <h3>📝 1. Real-time Speech Transcription</h3>
                <p class="meta-info">Total Words: <strong>${data.total_words}</strong> | Duration: <strong>${data.duration_seconds}s</strong></p>
                <div class="transcript-display-box">
                    ${f.highlighted_transcript || data.transcript}
                </div>
                <small class="hint-text">* Highlighted words indicate detected filler phrases.</small>
            </div>

            <!-- 2. Grammar Checking -->
            <div class="card feature-card">
                <h3>✍️ 2. Grammar Checking</h3>
                <div class="metric-score-row">
                    <span class="metric-label">Grammar Score:</span>
                    <span class="score-pill" style="background:${g.score >= 80 ? '#28a745':'#dc3545'}">${g.score}%</span>
                </div>
                <div class="issues-block">
                    <strong>Issues Identified:</strong>
                    <ul>${grammarIssuesHTML}</ul>
                </div>
                <div class="suggestions-block">
                    <strong>Improvement Suggestions:</strong>
                    <ul>${grammarSuggestionsHTML}</ul>
                </div>
            </div>

            <!-- 3. Filler-Word Detection -->
            <div class="card feature-card">
                <h3>🛑 3. Filler-Word Detection</h3>
                <div class="metric-score-row">
                    <span class="metric-label">Filler Count: <strong>${f.count}</strong></span>
                    <span class="metric-label">Filler Density: <strong>${f.density_percent}%</strong></span>
                </div>
                <div class="filler-tags-wrapper">
                    <strong>Detected Filler Words:</strong><br>
                    <div style="margin-top:8px">${fillerItemsHTML}</div>
                </div>
            </div>

            <!-- 4. Speech Pace Analysis -->
            <div class="card feature-card">
                <h3>⏱️ 4. Speech Pace Analysis</h3>
                <div class="metric-score-row">
                    <span class="metric-label">Cadence Speed:</span>
                    <span class="pace-badge" style="background:${paceBadgeColor}">${p.wpm} WPM (${p.status})</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${Math.min(100, (p.wpm / 200) * 100)}%; background:${paceBadgeColor}"></div>
                </div>
                <p class="recommendation-text">💡 <strong>Pace Recommendation:</strong> ${p.recommendation}</p>
            </div>

            <!-- 5. Pronunciation Evaluation -->
            <div class="card feature-card">
                <h3>🎯 5. Pronunciation Evaluation</h3>
                <div class="metric-score-row">
                    <span class="metric-label">Clarity & Confidence:</span>
                    <span class="score-pill" style="background:${pr.score >= 85 ? '#28a745':'#fd7e14'}">${pr.score}%</span>
                </div>
                <p class="feedback-text">🗣️ <strong>Pronunciation Feedback:</strong> ${pr.feedback}</p>
            </div>
        </div>
    `;
}

// Attach event listeners when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    const micBtn = document.getElementById("startMicBtn");
    if (micBtn) {
        micBtn.addEventListener("click", toggleMicRecording);
    }
    
    const analyzeBtn = document.getElementById("analyzeBtn");
    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", analyzeCommunication);
    }

    const sampleBtn = document.getElementById("loadSampleBtn");
    if (sampleBtn) {
        sampleBtn.addEventListener("click", loadSampleTranscript);
    }
});
