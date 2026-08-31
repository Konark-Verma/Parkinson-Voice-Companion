# Design Document
## Parkinson's Voice Companion — UI/UX Specification

**Related documents:** PRD.md (requirements), TECH_STACK.md (frontend: React + Recharts)

---

## 1. Design Principles

These principles come directly from the PRD's non-functional requirements and the nature of the target users, not from generic aesthetic preference:

1. **Minimal, not sparse.** Every screen shows only what the user needs *right now* — no dashboards packed with panels. But nothing feels empty or unfinished; whitespace is intentional, not accidental.
2. **Calm over clinical.** This is a health tool used daily by someone managing a chronic condition. The tone should feel supportive, never alarming or sterile. Avoid red/warning colors except for genuinely urgent alerts (Section 4).
3. **Large, forgiving touch targets.** Per PRD's usability requirement, the target user may have motor symptoms (tremor, reduced fine motor control). Buttons and interactive elements are large, well-spaced, and forgiving of imprecise taps/clicks.
4. **One primary action per screen.** No screen asks the patient to make more than one real decision at a time (record a sample, do an exercise, log medication — never all three competing for attention on one page).
5. **No diagnostic language, ever.** Per PRD Section 8, copy must never imply diagnosis. "Your voice sounds a bit different today" — not "abnormal reading detected."

---

## 2. Design System

### Color Palette
| Role | Color | Usage |
|---|---|---|
| Primary | Soft teal `#4A9B8E` | Primary buttons, active states, brand accent |
| Background | Warm off-white `#FAF9F6` | Page background — not stark white, feels warmer |
| Surface | White `#FFFFFF` | Cards, panels |
| Text primary | Charcoal `#2E2E2E` | Body text — not pure black, softer on the eyes |
| Text secondary | Warm gray `#7A7770` | Supporting text, timestamps |
| Success/calm | Sage green `#7FA582` | "Stable," "on track" indicators |
| Attention (gradual) | Amber `#D9A441` | Gradual change — informational, not alarming |
| Urgent (sudden alert) | Muted coral red `#C4544A` | Reserved *only* for sudden-decline alerts — used sparingly so it retains meaning |

### Typography
- **Font:** System font stack (San Francisco / Segoe UI / Roboto depending on OS) — no custom web font load, keeps it fast and familiar-feeling.
- **Sizes:** Patient-facing screens use a larger base size (18px body, 28px+ headers) than typical web apps, for readability. Doctor view can use standard sizing (14-16px body) since it's a data-review context, not a daily-use context.

### Components
- **Cards** with generous padding (24px+), soft rounded corners (12px), subtle shadow — never harsh borders.
- **Buttons:** Primary action = filled teal, rounded, minimum 48px height. Secondary actions = outlined, same size. No more than one filled/primary button visible per screen.
- **Icons:** Simple, outline-style, used sparingly to support text labels — never icon-only for primary actions (accessibility: users shouldn't have to guess what an icon means).

---

## 3. Screen Map

```
Patient/Caregiver App
├── Home (Today)
├── Record Voice Sample
├── Therapy Exercise
│   └── Session Complete (results)
├── Medication Log
└── History (simple trend view)

Doctor View
├── Patient Overview
├── Wearing-Off Pattern (chart)
├── Severity Trend (chart)
├── Therapy Engagement Summary
└── Alert History
```

---

## 4. Screen-by-Screen Specification

### 4.1 Patient/Caregiver — Home ("Today")
**Purpose:** The single landing screen. Answers "how are things today" at a glance, then offers the day's actions.

**Contents (top to bottom):**
- Greeting + date ("Good morning, [Name]")
- One calm status line: "Everything looks steady" (default) or, if an alert exists, a gently-worded prompt to check it — never the raw alert data on this screen, just a nudge to open it.
- Two large primary action cards, side by side or stacked on mobile:
  - **"Record today's check-in"** (voice sample)
  - **"Start today's exercise"** (therapy session)
- A small, unobtrusive "Log medication" link/button below — frequent but secondary action.
- If therapy streak exists: a small, warm encouragement line ("5 days in a row!") — motivational, not gamified/pressuring.

**Explicitly NOT on this screen:** charts, numeric scores, technical severity levels. Those belong in History/Doctor view, not the daily-use screen.

### 4.2 Record Voice Sample
**Purpose:** Guide the user through recording without ambiguity about what to do.

**Contents:**
- Clear instruction text: "Say 'ahhh' for as long and steady as you can" (or the passage-reading task, depending on which is active)
- One large, obvious record button (press to start, press to stop — no complex controls)
- Simple visual feedback while recording (e.g., a gentle pulsing indicator, not a technical waveform)
- After recording: a plain confirmation ("Got it, thank you") — **do not show the raw risk score or severity label directly to the patient.** Per PRD's framing constraint, raw classification output is dashboard/doctor-facing data, not something to present starkly to a patient who may misread "high risk" as a diagnosis. Caregivers/doctors see the numbers; patients see reassurance.

### 4.3 Therapy Exercise
**Purpose:** Guided LSVT LOUD-style exercise with real-time feedback.

**Contents:**
- Exercise instruction ("Say 'AHHH' as loud and clear as you can")
- Large, simple real-time feedback — a single visual bar or meter for volume (not multiple competing metrics on screen at once during the exercise itself, to avoid overwhelming the user mid-task)
- Encouraging, non-judgmental micro-copy ("Nice and strong!" rather than a raw decibel number)
- **Session Complete screen** afterward: simple summary ("Great session — a bit louder than yesterday!") with an optional "see details" link for those who want the numbers (mainly caregivers)

### 4.4 Medication Log
**Purpose:** Quick, low-friction logging — this needs to be fast since it happens multiple times daily.
- List of scheduled medications with a single-tap "Taken" button per dose
- Ability to add a new medication (name, dosage, frequency) — this is a secondary, less-frequent flow, so it can be tucked behind a smaller "+ Add medication" link rather than being prominent

### 4.5 History (Patient/Caregiver-facing)
**Purpose:** A gentle, simplified trend view for those who want more than "today."
- Simple weekly/monthly view — a soft line trend, not a dense multi-series chart
- Plain-language summaries alongside the chart ("Your check-ins have been steady this week")

### 4.6 Doctor View — Overview
**Purpose:** Data-dense, efficient — this user wants information quickly, not warmth.
- Patient summary header (name, age, diagnosis date, current medications)
- Quick-glance cards: latest severity score, wearing-off status, active alerts, therapy adherence %

### 4.7 Doctor View — Wearing-Off Pattern Chart
- Line/scatter chart: severity score over time, with medication intake times overlaid as markers, so recurring pre-dose dips are visually obvious
- Built with Recharts per TECH_STACK.md

### 4.8 Doctor View — Severity Trend & Alert History
- Full severity trend line, with change-point-flagged events marked distinctly (gradual = amber marker, sudden = coral marker, matching the palette in Section 2)
- Alert history as a simple chronological list below the chart, each entry showing type, timestamp, and gradual/urgent classification

---

## 5. Accessibility Notes
- Minimum text size 16px anywhere in the patient-facing app (18px+ preferred for primary content).
- Color is never the only signal — alerts also carry a text label ("Urgent" / "Routine"), not just a red/amber dot, for colorblind users.
- All primary actions reachable via keyboard navigation, not just mouse/touch.
- No auto-playing audio, no flashing/rapid animation (avoid triggering discomfort for users who may be sensitive to visual motion).

---

## 6. What "Minimalistic" Means Here (to avoid ambiguity during build)
Minimalism in this project means **reduced cognitive load per screen**, not reduced functionality and not a stripped-down "empty" aesthetic. Every screen should feel complete and considered — generous spacing, clear hierarchy, one obvious next action — rather than cramming every feature onto fewer screens. Where there's tension between "fewer screens" and "less to think about per screen," this project always chooses the latter, per PRD's usability requirement for a user who may have motor/cognitive symptoms.
