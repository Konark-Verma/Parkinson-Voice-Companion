# Product Requirements Document (PRD)
## Parkinson's Voice Companion — Integrated Monitoring, Therapy & Alert System

**Version:** 1.0
**Team:** Person A (ML/Core), Person B (Therapy Module/Dashboard)
**Timeline:** 8 weeks

---

## 1. Purpose

This document defines what the Parkinson's Voice Companion system must do, for whom, and why — as the reference all design and engineering decisions should trace back to. It is written before implementation and should be treated as the source of truth if any conflict arises between it and PLAN.md (the execution plan) or the ERD.

---

## 2. Problem Statement

Patients already diagnosed with Parkinson's disease face three unaddressed gaps in ongoing care:

1. **Medication timing is guessed, not measured.** Levodopa's effect wears off between doses ("OFF episodes"). Patients currently rely on subjective self-report to communicate this to their doctor, which is inconsistent and easy to misjudge.
2. **Speech therapy is disconnected from monitoring.** LSVT LOUD-style therapy apps exist, but nothing ties therapy engagement or improvement to the patient's broader symptom trend.
3. **Decline tracking doesn't distinguish cause.** Existing trackers show a downward line without distinguishing ordinary disease progression from a sudden change that may signal something else (infection, fall, medication issue) requiring urgent attention.

---

## 3. Goals

### 3.1 Product Goals
- Give patients and caregivers an objective, passive way to track symptom severity via voice, without requiring clinic visits.
- Surface medication "wearing-off" patterns that are currently invisible without a formal clinical diary.
- Provide an active tool (guided therapy) alongside passive monitoring, not monitoring alone.
- Distinguish routine decline from urgent decline, reducing both unnecessary alarm and missed emergencies.

### 3.2 Academic/Project Goals
- Deliver a working, demoable, end-to-end system within 8 weeks with 2 team members.
- Demonstrate applied ML (classification, time-series correlation, change-point detection) grounded in real clinical literature.
- Produce a defensible, honestly-scoped novelty claim (see Section 4).

### 3.3 Non-Goals (explicitly out of scope)
- This is **not** a diagnostic tool. It does not diagnose Parkinson's disease.
- This is **not** a replacement for a doctor, neurologist, or LSVT-certified speech therapist.
- Real-time continuous monitoring (e.g., always-listening background audio) is out of scope — voice samples are deliberately recorded by the user at chosen intervals.
- Multi-language support is out of scope for the 8-week build (English only); this is stated as a known limitation, not a hidden gap.
- Mobile native apps are out of scope; the deliverable is a web-based system.

---

## 4. Novelty / Differentiation Statement

> Voice-based screening, wearable-based wearing-off detection, and LSVT-style speech therapy apps each already exist as separate, disconnected tools built by different teams. No tool identified in our research combines passive voice-based monitoring, medication-correlated wearing-off detection, active speech therapy coaching, and severity-of-change-based alerting into one integrated system around a shared patient data pipeline. This is a product-integration contribution, not a claim of novel algorithms or a "first-of-its-kind" invention.

---

## 5. Target Users / Personas

| Persona | Description | Needs from the system |
|---|---|---|
| **Patient** | Diagnosed with Parkinson's, using the system day-to-day | Simple recording flow, therapy exercises with clear feedback, non-alarming presentation of results |
| **Caregiver** | Family member or professional aide supporting the patient | Visibility into daily status, clear alerts when something needs attention, low cognitive load (they are often not clinically trained) |
| **Doctor** | Treating neurologist reviewing patient data periodically | Objective trend data (wearing-off pattern, severity over time) to inform medication/treatment decisions during appointments |

---

## 6. User Stories

### Patient
- As a patient, I want to record a short voice sample so that my symptom severity is tracked without needing a clinic visit.
- As a patient, I want to do guided speech therapy exercises with real-time feedback so I know if I'm speaking loud/clear enough.
- As a patient, I want to see my own progress over time so I feel motivated to continue therapy.

### Caregiver
- As a caregiver, I want to log when medication was taken so the system can correlate it with symptom changes.
- As a caregiver, I want to be alerted if the patient's condition changes suddenly, so I know when to seek help urgently versus when it's expected fluctuation.
- As a caregiver, I want a simple, non-technical view of "how are things going," not raw data.

### Doctor
- As a doctor, I want to see a wearing-off pattern chart so I can evaluate whether medication timing needs adjustment.
- As a doctor, I want to see therapy engagement and progress so I can assess whether the patient is benefiting from the exercises.
- As a doctor, I want a clear distinction between gradual and sudden decline in the patient's history, so I can triage what needs my attention first.

---

## 7. Functional Requirements

### FR1 — Voice Recording & Classification
- FR1.1: System shall allow a user to record a voice sample via browser microphone (sustained vowel or short passage read-aloud).
- FR1.2: System shall extract acoustic features (jitter, shimmer, harmonics-to-noise ratio, pitch variation) from each recording.
- FR1.3: System shall classify severity/risk level from extracted features and return a confidence score.
- FR1.4: System shall store each sample's features and classification result, timestamped, linked to the patient.

### FR2 — Medication & Wearing-Off Tracking
- FR2.1: System shall allow logging of prescribed medications (name, dosage, frequency) per patient.
- FR2.2: System shall allow logging of medication intake events with timestamps.
- FR2.3: System shall correlate classification severity trends against medication intake timestamps to detect recurring "wearing-off" patterns.
- FR2.4: System shall visually present the wearing-off pattern (chart) to the doctor view.

### FR3 — Speech Therapy Coach
- FR3.1: System shall provide guided speech therapy exercises based on LSVT LOUD principles.
- FR3.2: System shall provide real-time feedback on volume, clarity, and pitch variation during an exercise.
- FR3.3: System shall store session results (scores, duration, date) linked to the patient.
- FR3.4: System shall display session history and improvement trend over time.

### FR4 — Decline Alert System
- FR4.1: System shall run change-point detection on the patient's severity trend over time.
- FR4.2: System shall classify detected changes as gradual (informational) or sudden (urgent).
- FR4.3: System shall generate an alert record when a sudden change is detected.
- FR4.4: System shall surface alerts distinctly (e.g., visually flagged/urgent banner) in caregiver and doctor views, separate from routine gradual-trend information.

### FR5 — Dashboard & Views
- FR5.1: System shall provide a patient/caregiver view showing: today's status, recent therapy progress, active alerts.
- FR5.2: System shall provide a doctor view showing: wearing-off pattern chart, severity trend over time, therapy engagement summary, alert history.
- FR5.3: System shall support multiple caregivers per patient and one doctor per patient (per the ERD's many-to-many/many-to-one relationships).

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Usability** | Patient-facing UI must be simple and low-friction — large controls, minimal text, since the target user may have motor/cognitive symptoms affecting fine interaction. |
| **Performance** | Voice feature extraction and classification should return a result within a few seconds of upload, to keep the recording flow usable. |
| **Portability** | System must run entirely on a local machine — no GPU, no paid cloud API, no external approval-gated service. |
| **Data privacy** | Patient data (voice recordings, health-related logs) should be stored locally in the project's own database, not transmitted to third parties. |
| **Honesty/Framing** | All UI copy, alerts, and reports must avoid diagnostic language; framing must consistently present the tool as a monitoring/screening support and therapy aid, never as a diagnosis. |
| **Maintainability** | Codebase should keep the 3 modules (tracking, therapy, alerting) reasonably decoupled behind clear API boundaries, consistent with the module ownership split between the 2 team members. |

---

## 9. Success Metrics

### Technical metrics
- Classifier precision/recall/F1 on held-out test data, compared against published benchmark figures for the same public datasets (UCI/Oxford Parkinson's voice datasets).
- Wearing-off detection: qualitative validation that flagged dips align with expected pre-next-dose timing in test scenarios.
- Change-point detection: correctly distinguishes injected "sudden change" test scenarios from injected "gradual change" scenarios in synthetic/test data.

### Project-delivery metrics
- All 5 increments (per PLAN.md) delivered on schedule, each independently demoable.
- End-to-end demo runs cleanly: record → classify → wearing-off chart updates; therapy exercise → real-time feedback; simulated sudden decline → alert fires.

---

## 10. Assumptions & Constraints
- Requirements are based on established, published clinical research (vocal biomarkers literature, LSVT LOUD protocol) rather than requirements gathered from real patients — this is a constraint of an 8-week academic project, not a hidden gap, and should be stated plainly in the final report.
- Test/demo users will be healthy volunteers (team members, friends, family), not diagnosed Parkinson's patients. Real patient validation is out of scope and noted as future work.
- Team size is 2, with a clear module ownership split (see PLAN.md Section 6) — this PRD's requirements assume that division of responsibility.

---

## 11. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Classifier underperforms published benchmarks | Medium | Report honestly; discuss why (smaller compute budget, different validation approach) rather than hiding the gap |
| Real recorded voice (messy, phone-mic quality) behaves differently than clean dataset audio | Medium-High | Budget explicit testing time in Week 8 for this; do not assume dataset performance transfers |
| Wearing-off correlation logic produces false positives on limited test data | Medium | Present as a proof-of-concept detection approach, not a clinically validated one |
| Scope creep from adding features beyond the 3 core modules | Medium | Treat Section 3.3 (Non-Goals) as a hard boundary for the 8-week timeline |

---

## 12. Related Documents
- `PLAN.md` — execution plan, week-by-week tasks, API contract, tech stack
- ERD (`ParkinsonsVoiceCompanion.mdj`) — full database schema
- Work Breakdown Structure (ProjectLibre) — task-level scheduling and resource assignment
