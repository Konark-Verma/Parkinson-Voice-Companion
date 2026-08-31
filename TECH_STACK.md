# Tech Stack Document
## Parkinson's Voice Companion — Integrated Monitoring, Therapy & Alert System

**Related documents:** PRD.md (requirements), PLAN.md (execution plan), ERD (database schema)

---

## 1. Guiding Principles Behind These Choices

- **Zero external approval dependency** — everything below is open source, free, and requires no sandbox access, API key application, or waiting period, so neither team member can get blocked mid-project waiting on a third party.
- **Runs on a laptop** — no GPU, no paid cloud compute required anywhere in the stack.
- **One primary language (Python) across ML and backend** — reduces context-switching for whoever owns the ML/core module, and keeps the backend and ML pipeline in the same ecosystem.
- **Boring, well-documented, mainstream tools over novel/niche ones** — the novelty in this project is in the system integration (see PRD Section 4), not the tooling; picking exotic libraries would add risk for no benefit.

---

## 2. Backend

| Component | Choice | Why |
|---|---|---|
| Framework | **FastAPI** (Python) | Async-capable, automatic OpenAPI docs (useful for the two of you to agree on the API contract without manual doc-writing), minimal boilerplate compared to Django, and keeps the backend in Python alongside the ML code. |
| Server | **Uvicorn** | Standard ASGI server for FastAPI; no separate deployment complexity needed for a local/academic project. |
| Validation | **Pydantic** (ships with FastAPI) | Request/response schema validation matching the API contract in PLAN.md Section 7. |

**Install:**
```bash
pip install fastapi uvicorn[standard] pydantic
```

---

## 3. Database

| Component | Choice | Why |
|---|---|---|
| Database engine | **SQLite** | Zero setup — no server process, no credentials, just a file. Fully sufficient for a single-machine academic demo with a handful of test patients. |
| ORM | **SQLAlchemy** | Maps directly onto the ERD entities (PATIENT, VOICE_SAMPLE, etc.); works with SQLite now and Postgres later with minimal code change if ever needed. |
| Migrations | **Alembic** (optional, only if schema changes get frequent enough to be painful to hand-edit) | Skip this initially — for an 8-week project, manually adjusting the schema is likely faster than learning Alembic. Revisit only if schema churn becomes a real problem. |

**Install:**
```bash
pip install sqlalchemy
```

**Note:** Implement tables exactly matching the ERD (`ParkinsonsVoiceCompanion.mdj`) — column names, types, and PK/FK relationships should be identical across the diagram, this stack, and the actual code, so there's no drift between documentation and implementation.

---

## 4. ML / Signal Processing (Person A's primary toolkit)

| Component | Choice | Why |
|---|---|---|
| Voice feature extraction | **parselmouth** (Python wrapper for Praat) | Purpose-built for exactly this task (jitter, shimmer, HNR, pitch extraction) — this is the standard tool in published vocal biomarker research, not something built from scratch. |
| Classical ML | **scikit-learn** | SVM and Random Forest baselines; well-documented, runs on CPU, matches what the published Parkinson's voice literature typically uses for comparable results. |
| Gradient boosting (if baseline underperforms) | **XGBoost** | Optional upgrade path from the scikit-learn baseline if more predictive power is needed — not required to start. |
| Numerical/data handling | **NumPy, pandas** | Standard data manipulation for feature tables and evaluation. |
| Change-point detection | **scipy** (rolling statistics) or **ruptures** (dedicated change-point detection library) | Start with a simple rolling mean/variance shift approach using scipy before reaching for a dedicated library — per PRD, this is intentionally not meant to be a novel algorithm, so don't over-engineer it. |
| Model evaluation | **scikit-learn metrics** (precision, recall, F1, confusion matrix) | Matches the honest evaluation approach specified in PRD Section 9 — never report accuracy alone on what may be an imbalanced dataset. |

**Install:**
```bash
pip install praat-parselmouth scikit-learn xgboost numpy pandas scipy ruptures
```

---

## 5. Frontend

| Component | Choice | Why |
|---|---|---|
| Framework | **React** | Standard, well-documented, matches what was already used for prior artifacts in this project (dashboard mockups) — no new learning curve. |
| Audio recording | **Web Audio API** (native browser API, no extra library needed for basic recording) | Built into every modern browser — no dependency, no compatibility risk. |
| Charts | **Recharts** | For the wearing-off pattern chart, severity trend, and therapy progress visualizations in the dashboard — lightweight, React-native charting. |
| HTTP client | **fetch** (native) or **axios** | Either is fine; axios is slightly more ergonomic for error handling if the team prefers it. |
| Styling | Plain CSS or a lightweight utility approach (e.g., Tailwind if the team is comfortable with it) | Keep this simple — the demo needs to look clean and usable, not visually elaborate; don't spend build time on a design system. |

**Install:**
```bash
npm install react react-dom recharts axios
```

---

## 6. Project Structure (suggested)

```
parkinsons-voice-companion/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── models/                  # SQLAlchemy models (matches ERD)
│   ├── routers/                 # API route handlers (patients, voice-samples, medications, therapy, alerts)
│   ├── ml/
│   │   ├── feature_extraction.py   # parselmouth-based feature extraction
│   │   ├── classifier.py           # trained model load/predict
│   │   ├── wearing_off.py          # correlation logic
│   │   └── change_point.py         # decline alert detection
│   ├── database.py               # DB session/engine setup
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # RecordingWidget, TherapyExercise, DashboardChart, AlertBanner, etc.
│   │   ├── pages/                 # PatientView, DoctorView
│   │   ├── api/                   # API client functions matching the contract in PLAN.md
│   │   └── App.jsx
│   └── package.json
├── notebooks/                    # Weeks 2-3 EDA and model evaluation (Jupyter, not part of the shipped app)
├── data/                         # Local storage for downloaded public datasets (gitignored)
├── PRD.md
├── PLAN.md
└── README.md
```

---

## 7. Development Environment

| Tool | Purpose |
|---|---|
| Python 3.10+ | Backend and ML |
| Node.js 18+ / npm | Frontend |
| Jupyter Notebook | Weeks 2-3 exploratory data analysis and model evaluation (not shipped in the final app, used for the report's evaluation section) |
| Git | Version control — even for a 2-person team, use feature branches per increment to avoid stepping on each other's module code |

---

## 8. Explicitly Not Using (and why)

| Rejected option | Reason |
|---|---|
| Cloud-hosted database (e.g., managed Postgres) | Adds an external dependency and possible cost/approval delay for no benefit at this scale — SQLite is sufficient. |
| Deep learning frameworks (PyTorch/TensorFlow) for the classifier | Published Parkinson's voice literature shows classical ML (SVM/Random Forest/XGBoost) performs well on this task; deep learning would add complexity and GPU dependency without a clear benefit for an 8-week timeline. |
| Paid transcription/audio APIs | Feature extraction here is signal-level (jitter/shimmer/pitch), not speech-to-text — no transcription service is needed at all. |
| Native mobile app frameworks | Out of scope per PRD Section 3.3 — web-based only. |
| Kubernetes/Docker orchestration | Unnecessary operational complexity for a local academic demo; a plain `venv` + `npm start` setup is sufficient. |

---

## 9. Module-to-Owner Mapping (for reference)

| Stack layer | Primary owner |
|---|---|
| ML/feature extraction/classifier/wearing-off/change-point | Person A |
| Speech therapy module, frontend dashboard, backend API wiring | Person B |
| Database schema, API contract | Joint (agree upfront in Week 1, avoid unilateral changes later) |
