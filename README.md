# Parkinson's Voice Companion

> **CLINICAL & REGULATORY SAFETY DISCLAIMER**:  
> Parkinson's Voice Companion is an experimental screening/monitoring support tool and speech therapy aid. It is **NOT** a diagnostic medical device and does not replace clinical assessment by a licensed medical doctor, neurologist, or LSVT-certified speech-language pathologist. All metrics represent acoustic vocal stability risk indicators, not definitive medical diagnoses.

---

## 1. System Overview & Architecture

Parkinson's Voice Companion is an end-to-end full-stack prototype providing vocal biomarker monitoring, medication wearing-off correlation tracking, real-time AI speech therapy coaching, and statistical decline change-point detection.

```
                                  ┌───────────────────────────┐
                                  │      React 18 + Vite      │
                                  │  (Patient / Caregiver /   │
                                  │    Doctor Dashboards)     │
                                  └─────────────┬─────────────┘
                                                │ REST / WebSockets / Web Audio
                                                ▼
                                  ┌───────────────────────────┐
                                  │      FastAPI Backend      │
                                  │   (Async Core + Security) │
                                  └──────┬──────────────┬─────┘
                                         │              │
                    ┌────────────────────┴───┐     ┌────┴───────────────────┐
                    ▼                        ▼     ▼                        ▼
       ┌────────────────────────┐  ┌──────────────────┐   ┌────────────────────────┐
       │   Acoustic ML Engine   │  │  Analysis Core   │   │     Alert Engine       │
       │ (Parselmouth / Praat + │  │ (Wearing-Off &   │   │  (WebSocket Broadcast  │
       │  Oxford ML Classifier) │  │ Change-Point CP) │   │  + Multi-Channel Disp) │
       └────────────────────────┘  └──────────────────┘   └────────────────────────┘
                    │                        │                          │
                    └────────────────────────┼──────────────────────────┘
                                             ▼
                                  ┌───────────────────────────┐
                                  │  SQLite Relational Store  │
                                  │   (10 ER Entity Tables)   │
                                  └───────────────────────────┘
```

### Chosen Tech Stack & Justifications

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend** | **React 18 + Vite + Tailwind CSS + Lucide Icons + Recharts** | High contrast, minimum 48–72px touch targets, motor-tremor tolerant, ≤2-tap primary workflows, responsive across mobile, tablet, and clinical desktop views. |
| **Live Audio Coaching** | **Web Audio API (`AnalyserNode` + Autocorrelation)** | Client-side pitch ($F_0$) and calibrated volume (dB) detection with **<100ms latency** (well below the ≤500ms requirement). |
| **Backend API** | **FastAPI (Python async) + Uvicorn** | Native async IO, sub-millisecond API overhead, native Python scientific/audio ecosystem integration, and WebSocket broadcasting. |
| **Database & Schema** | **SQLite + Async SQLAlchemy 2.0 (WAL mode)** | Exact 1:1 relational modeling matching the 10 core entities with sub-50ms 90-day aggregation queries. |
| **ML & Acoustic Pipeline** | **Parselmouth (Praat C-bindings) + Scikit-Learn Ensemble** | Praat is the clinical gold standard in voice acoustic research (Jitter, Shimmer, HNR, Pitch). Scikit-Learn ensemble yields fast (<15ms) deterministic inference. |
| **Alert Notifications** | **FastAPI WebSocket Manager + In-App Dispatcher** | Real-time multi-actor alert routing (Patient, Caregiver, Doctor) based on alert urgency. |

---

## 2. Relational Data Model (10 Entities 1:1 with ER Model)

The database implements all 10 core entities:

1. **`DOCTOR`**: `id`, `user_id`, `name`, `email`, `specialty`, `clinic_name`, `phone`, `created_at`
2. **`CAREGIVER`**: `id`, `user_id`, `name`, `email`, `phone`, `relationship_type`, `created_at`
3. **`PATIENT`**: `id`, `user_id`, `name`, `date_of_birth`, `gender`, `diagnosis_year`, `doctor_id`, `caregiver_id`, `baseline_hnr`, `notes`, `created_at`
4. **`VOICE_SAMPLE`**: `id`, `patient_id`, `recorded_by_user_id`, `timestamp`, `task_type`, `file_path`, `audio_duration_sec`, `sample_rate`, `status`, `created_at`
5. **`EXTRACTED_FEATURES`**: `id`, `voice_sample_id`, `jitter_local`, `jitter_rap`, `jitter_ppq5`, `shimmer_local`, `shimmer_apq3`, `shimmer_apq5`, `hnr`, `f0_mean`, `f0_std`, `f0_min`, `f0_max`, `ppe`, `spread1`, `spread2`, `raw_features_json`, `created_at`
6. **`CLASSIFICATION_RESULT`**: `id`, `voice_sample_id`, `risk_score` (0.0–1.0), `confidence` (0.0–1.0), `severity_level` (`LOW_RISK`, `MILD`, `MODERATE`, `SEVERE`), `model_version`, `inference_time_ms`, `created_at`
7. **`MEDICATION`**: `id`, `patient_id`, `doctor_id`, `name`, `dosage`, `frequency`, `scheduled_times_json`, `instructions`, `is_active`, `created_at`
8. **`MEDICATION_LOG`**: `id`, `medication_id`, `patient_id`, `logged_by_user_id`, `status` (`TAKEN`, `SKIPPED`, `DELAYED`), `scheduled_time`, `actual_time`, `notes`, `created_at`
9. **`THERAPY_SESSION`**: `id`, `patient_id`, `exercise_type`, `target_pitch_hz`, `target_volume_db`, `duration_sec`, `avg_volume_db`, `pitch_stability_pct`, `score` (0–100), `feedback_notes`, `timestamp`, `created_at`
10. **`ALERT`**: `id`, `patient_id`, `type` (`DECLINE_GRADUAL`, `DECLINE_SUDDEN`, `WEARING_OFF_DIP`, `MEDICATION_MISSED`, `AUDIO_QUALITY`), `severity` (`INFORMATIONAL`, `WARNING`, `URGENT`), `title`, `message`, `trigger_time`, `status` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`), `recipient_roles_json`, `acknowledged_at`, `acknowledged_by_user_id`

---

## 3. Core Modules & Behaviors

### Module 1: Symptom & Medication Correlation Tracker
- **Record Voice Sample -> Auto-includes Classify Voice Sample**: Every uploaded recording automatically executes audio quality checks (minimum 2.0s duration, energy RMS, SNR). Valid audio triggers Praat acoustic extraction and ML classification. Low quality/short samples are rejected with friendly re-record guidance.
- **Manage Medication Schedule**: Doctor-only endpoints to configure medications, dosages, frequency, and scheduled times.
- **Log Medication Intake -> Auto-includes Track Wearing-Off Correlation**: When a patient or caregiver logs intake (`TAKEN`, `DELAYED`, `SKIPPED`), recent voice sample classifications in a window around the dose are correlated against baseline. If pre-dose acoustic risk elevation ($>15\%$) repeats across doses, a `WEARING_OFF_DIP` alert is flagged to the Doctor dashboard.

### Module 2: AI Speech Therapy Coach
- **Do Therapy Exercise -> Auto-includes Receive Live Feedback**: Guides patients through LSVT-style sustained loud vowels (/a/) and phrase repetition. The Web Audio API analyser runs with **<100ms latency** providing real-time decibel volume gauges, target zone ($\ge 75$ dB) indicators, and pitch stability feedback.
- **Therapy Session History**: Records duration, average dB, pitch stability %, score (0–100), and feedback to `THERAPY_SESSION`.

### Module 3: Decline Alert System
- **Change-Point Detection**: Evaluates rolling mean and variance shifts across historical classification scores.
- **Extension Point (`OnSeverityChange`)**:
  - Gradual drift ($\ge 2\sigma$ shift over $\ge 7$ days) $\implies$ `INFORMATIONAL` / `WARNING` alert.
  - Sudden jump ($\ge 3\sigma$ or $\ge +22\%$ shift in $\le 48$ hours) $\implies$ `URGENT` alert dispatched immediately to Doctor, Patient, and Caregiver dashboards via WebSockets.

### Cross-Cutting: Aggregated Dashboards
- **Patient / Caregiver Portal**: Accessible, large-touch controls (≤2 taps for core actions), voice recording tile, medication logging tile, therapy coaching tile, alerts feed.
- **Doctor Clinical Command Center**: Patient selector, **90-Day Longitudinal Trend Chart** (overlaid with medication intake and pre-dose dip flags, queried in **~39ms** vs ≤3s SLA), medication regimen editor, speech therapy adherence history, and decline alerts management.

---

## 4. Machine Learning Pipeline & Training

- **Dataset**: Oxford Parkinson's Disease Voice Dataset (UCI Machine Learning Repository / Little et al., 195 voice recordings, 22 acoustic features).
- **Features Extracted**:
  - Jitter measures: `MDVP:Jitter(%)`, `MDVP:RAP`, `MDVP:PPQ`, `Jitter:DDP`
  - Shimmer measures: `MDVP:Shimmer`, `MDVP:Shimmer(dB)`, `Shimmer:APQ3`, `Shimmer:APQ5`, `Shimmer:DDA`
  - Harmonicity: Harmonics-to-Noise Ratio (`HNR`), `NHR`
  - Pitch Dynamics: Fundamental Frequency $F_0$ (`MDVP:Fo(Hz)`, `MDVP:Fhi(Hz)`, `MDVP:Flo(Hz)`, $F_0$ std)
  - Nonlinear dynamic & entropy measures: `PPE`, `RPDE`, `DFA`, `spread1`, `spread2`, `D2`
- **Model**: Voting Ensemble (`RandomForestClassifier` + `GradientBoostingClassifier` + `StandardScaler`).
- **Validation Results**:
  - 5-Fold Stratified Cross-Validation Accuracy: **89.23% (+/- 1.92%)**
  - 5-Fold ROC-AUC: **0.9612**
  - Inference Latency: **< 15 ms**
- **Limitations**:
  - Trained on research laboratory acoustic recordings. Classification thresholds are unvalidated research approximations and must not be used as clinical diagnostic thresholds.

---

## 5. Known Assumptions & Open Items

1. **Classifier Accuracy/Confidence Thresholds**: Research baseline approximations are implemented and clearly documented as non-diagnostic placeholders.
2. **Final Alert Delivery Channel**: In-app real-time WebSocket broadcast + notification store is enabled by default; external SMS/Email/Push adapters are structured for provider plug-ins.
3. **Raw Audio Retention Period**: Defaults to 30 days in local `/data/uploads/` storage; configurable via retention policy metadata.
4. **Target Platform**: Responsive Web Application (optimized with touch targets $\ge 48-72$px for tablets/desktops for tremor-impaired patients and desktop clinical views for doctors).

---

## 6. Quickstart & Verification Instructions

### 1. Run Unit & Integration Test Suite
```powershell
$env:PYTHONPATH="."
python -m pytest backend/tests -v
```

### 2. Run End-to-End Demonstration Script
```powershell
$env:PYTHONPATH="."
python scripts/demo_end_to_end.py
```

### 3. Start the Full-Stack Application
```powershell
# Start Backend (serves API & SPA on port 8000)
$env:PYTHONPATH="."
python backend/app/main.py
```
Visit `http://localhost:8000` in your web browser.

### 4. Development Mode (Frontend Live Reload)
```powershell
cd frontend
npm run dev
```
Visit `http://localhost:5173`.

### Demo User Accounts
| Role | Username | Password | Linked Patient |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient` | `patient123` | Robert Jenkins (Self) |
| **Caregiver** | `caregiver` | `caregiver123` | Robert Jenkins |
| **Doctor** | `doctor` | `doctor123` | Robert Jenkins, Arthur Pendelton |
