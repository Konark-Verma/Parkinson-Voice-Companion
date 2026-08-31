# Parkinson's Voice Companion — Project Plan

## 1. Project Overview

**Name:** Parkinson's Voice Companion — Integrated Monitoring, Therapy & Alert System

**One-line description:** A system that uses voice biomarkers to monitor Parkinson's disease patients, correlates symptom severity with medication timing to detect "wearing-off" episodes, delivers LSVT LOUD-style speech therapy exercises with real-time feedback, and flags sudden (vs. gradual) decline for caregivers/doctors.

**Team:** 2 members
- **Person A** — owns the ML/core pipeline: feature extraction, baseline classifier, wearing-off correlation logic, decline alert (change-point) detection.
- **Person B** — owns the speech therapy coach module, frontend dashboard, and backend/API integration.

**Timeline:** 8 weeks, using an **Incremental Model** SDLC (well-defined requirements from clinical literature, delivered as 5 sequential increments, each independently working software).

**Framing constraint (must be respected throughout the build and in all UI copy/docs):** This is a **screening/monitoring support tool and a therapy aid**, not a diagnostic device and not a replacement for a doctor or an LSVT-certified therapist. No feature should imply a clinical diagnosis.

---

## 2. Problem Statement

Once a patient is already diagnosed with Parkinson's, three real gaps exist in day-to-day care:

1. **Medication timing is guessed, not measured.** Levodopa's effect wears off between doses ("OFF episodes"), but patients rely on subjective self-report to tell their doctor.
2. **Speech therapy (LSVT LOUD) exists but isn't tied to monitoring.** Patients do therapy exercises separately from any tracking of whether it's helping.
3. **Decline tracking doesn't distinguish cause.** A gradual expected decline and a sudden concerning drop (infection, fall, medication issue) look identical on a simple downward trend line.

## 3. Novelty Statement (for report/demo — state exactly this, do not overclaim)

> Voice-based screening, wearable-based wearing-off detection, and LSVT-style speech therapy apps each already exist as separate, disconnected tools from different teams. This project combines passive voice-based monitoring, medication-correlated wearing-off detection, active speech therapy coaching, and severity-of-change-based alerting into one integrated system built around a shared patient data pipeline.

Do not claim "world-first" or "invention" anywhere in documentation, UI, or demo narration.

---

## 4. System Architecture

### 4.1 Modules
1. **Symptom & Medication Correlation Tracker** — voice sample → feature extraction → classification → correlate against medication log → flag wearing-off patterns.
2. **AI Speech Therapy Coach** — guided LSVT LOUD-style exercises with real-time volume/clarity/pitch feedback, session history tracking.
3. **Decline Alert System** — change-point detection on the severity trend; distinguishes gradual (informational) vs. sudden (urgent) decline.

### 4.2 Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** SQLite for development (upgrade path to PostgreSQL if needed later — do not over-engineer this early)
- **ML/Signal processing:** `parselmouth` (Praat wrapper) for voice feature extraction; `scikit-learn` / `xgboost` for classification; `scipy` for change-point detection
- **Frontend:** React, browser-based audio recording via the Web Audio API
- **No paid APIs, no cloud dependency required.** Everything must run locally on a laptop, no GPU required.

### 4.3 High-Level Data Flow
```
Voice recording (browser) 
  → uploaded to backend 
  → parselmouth feature extraction (jitter, shimmer, HNR, pitch variation) 
  → classifier → risk_score + severity_level 
  → stored with timestamp 
  → correlated against medication_log timestamps → wearing-off flag 
  → fed into change-point detection across time → decline alert (if triggered) 
  → all surfaced on dashboard (patient/caregiver view + doctor view)
```

---

## 5. Database Schema (ERD summary — already finalized, do not redesign)

Entities: `PATIENT`, `DOCTOR`, `CAREGIVER`, `PATIENT_CAREGIVER` (junction table for many-to-many), `VOICE_SAMPLE`, `EXTRACTED_FEATURES`, `CLASSIFICATION_RESULT`, `MEDICATION`, `MEDICATION_LOG`, `THERAPY_SESSION`, `ALERT`.

Key relationships:
- `PATIENT` 1:many `VOICE_SAMPLE`
- `VOICE_SAMPLE` 1:1 `EXTRACTED_FEATURES`
- `VOICE_SAMPLE` 1:1 `CLASSIFICATION_RESULT`
- `PATIENT` 1:many `MEDICATION`; `MEDICATION` 1:many `MEDICATION_LOG`
- `PATIENT` 1:many `THERAPY_SESSION`
- `PATIENT` 1:many `ALERT`
- `PATIENT` many:1 `DOCTOR`
- `PATIENT` many:many `CAREGIVER` (via `PATIENT_CAREGIVER`)

Full column-level schema with types and PK/FK flags is in the accompanying ERD (StarUML `.mdj` file) — implement `CREATE TABLE` statements exactly matching those column names/types so the schema stays consistent across documentation, diagram, and code.

---

## 6. Week-by-Week Build Plan (Incremental Model, 5 increments)

### Week 1 — Requirement Analysis & Planning (Both members)
- [ ] Literature review: vocal biomarkers (jitter, shimmer, HNR, pitch variation), LSVT LOUD protocol basics
- [ ] Download UCI Parkinson's Disease Classification dataset + Oxford Parkinson's Disease Detection dataset
- [ ] Install and test `parselmouth` on sample audio files
- [ ] Write SRS (feature list, module boundaries, success metrics)
- [ ] Finalize database schema (already defined above — implement as SQL DDL)
- [ ] Agree on API contract between backend and frontend (see Section 7)

### Week 2–3 — Increment 1: Core ML Pipeline (Person A primary)
- [ ] Build feature extraction pipeline: audio in → jitter, shimmer, HNR, pitch variation out
- [ ] Exploratory data analysis: how features differ between PD/non-PD samples in the public datasets
- [ ] Train baseline classifier (SVM or Random Forest)
- [ ] Evaluate: precision, recall, F1 (not just accuracy — datasets may be imbalanced); compare against published benchmark numbers, document honestly if results differ
- [ ] (Person B, parallel) Backend scaffolding (FastAPI project structure, DB models) + dashboard skeleton (React project, routing, empty views)

### Week 4 — Increment 2: Wearing-off Tracking Module (Person A primary)
- [ ] Medication log CRUD (add/view medication schedule and intake log)
- [ ] Correlation logic: join classifier severity output against medication log timestamps
- [ ] Wearing-off flagging: detect recurring severity dips that precede next scheduled dose

### Week 5 — Increment 3: Speech Therapy Coach Module (Person B primary)
- [ ] Design guided exercises based on LSVT LOUD principles (sustained loud vowel, phrase repetition)
- [ ] Real-time feedback: volume level, clarity/pitch variation feedback during exercise (using Web Audio API + backend feature extraction)
- [ ] Session history storage (`THERAPY_SESSION` table) with score tracking over time

### Week 6 — Increment 4: Decline Alert System (Person A primary, Person B integrates into UI)
- [ ] Implement change-point detection on the severity trend (simple approach: rolling mean/variance shift detection, or CUSUM — do not over-engineer, this does not need to be a novel algorithm)
- [ ] Classify detected changes as gradual (informational) vs. sudden (urgent alert)
- [ ] Alert generation logic writes to `ALERT` table
- [ ] Person B wires alert data into the dashboard's alert banner/notification UI

### Week 7 — Increment 5: Integration & Dashboard (Both members, full pairing)
- [ ] Finalize backend API endpoints (see Section 7) and connect all modules end-to-end
- [ ] Build full dashboard: patient/caregiver view (today's status, therapy progress, recent alerts) and doctor view (wearing-off pattern chart, severity trend, alert history)
- [ ] Full integration testing — bugs at module boundaries surface here

### Week 8 — Testing, Polish, Delivery (Both members)
- [ ] End-to-end testing with real recorded voice (not just clean dataset audio) — test with both team members' own voices at minimum
- [ ] Bug fixing and UI polish
- [ ] Write final report: architecture, model evaluation results, honest limitations, novelty statement (Section 3), demo script
- [ ] Prepare live demo: (1) record voice → see classification + wearing-off chart populate; (2) run a therapy exercise → see real-time feedback; (3) show a simulated sudden-decline alert firing

---

## 7. API Contract (backend ⇄ frontend — finalize exact shape in Week 1, do not change casually later)

```
POST /patients                      → create patient
GET  /patients/{id}                 → patient profile
POST /voice-samples                 → upload audio, returns { sample_id, risk_score, confidence, severity_level, features: {...} }
GET  /patients/{id}/wearing-off      → { flags: [...], correlation_chart_data: [...] }
POST /medications                   → add medication
POST /medication-logs               → log an intake event
POST /therapy-sessions              → submit a completed session, returns { volume_score, clarity_score }
GET  /patients/{id}/therapy-history  → session history for trend chart
GET  /patients/{id}/alerts           → alert list
GET  /patients/{id}/dashboard        → aggregate view for the dashboard (composite of the above, to minimize frontend round-trips)
```

---

## 8. Testing Plan
- **Unit level:** feature extraction sanity checks (known-clean audio produces sane values); classifier evaluated on held-out test split before touching real recordings.
- **Module level:** each increment's owner tests their own module before marking it "done"; the other member cross-tests it fresh.
- **Integration level:** Weeks 6–7, both members test module boundaries together.
- **Real-world validation:** Week 8, test with real recorded voice from both team members (and friends/family if willing) — clean dataset audio will not reveal real-world pipeline issues.

## 9. Honest Limitations To State In The Report (do not omit)
- Classifier trained/validated on public English-language datasets; performance on other languages/accents is untested.
- Test users for the live demo are healthy volunteers, not diagnosed Parkinson's patients — real patient validation requires clinical partnership and is noted as future work.
- Change-point detection uses a simple statistical method, not a novel algorithm — this is intentional (see Section 3 novelty statement, which is about system integration, not the individual algorithms).

## 10. Deliverables Checklist
- [ ] Working end-to-end system (all 3 modules integrated)
- [ ] ER diagram (already complete)
- [ ] Work Breakdown Structure (already complete)
- [ ] SRS document
- [ ] Final report (architecture, evaluation results, limitations, novelty statement)
- [ ] Live demo script (3 beats: classification, therapy feedback, decline alert)
