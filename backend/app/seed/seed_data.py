import json
import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.security import get_password_hash
from backend.app.models.models import (
    User, Doctor, Caregiver, Patient, VoiceSample,
    ExtractedFeatures, ClassificationResult, Medication,
    MedicationLog, TherapySession, Alert
)

async def seed_database(db: AsyncSession):
    """
    Seeds initial realistic clinical demo data if database is empty.
    """
    # Check if users exist
    user_check = await db.execute(select(User).limit(1))
    if user_check.scalar_one_or_none():
        print("[SEED] Database already populated. Skipping initial seed.")
        return

    print("[SEED] Generating clinical demo seed data...")

    # 1. Users
    doc_user = User(
        username="doctor",
        hashed_password=get_password_hash("doctor123"),
        full_name="Dr. Emily Vance, MD",
        email="dr.vance@neurocare.org",
        role="DOCTOR"
    )
    cg_user = User(
        username="caregiver",
        hashed_password=get_password_hash("caregiver123"),
        full_name="Sarah Jenkins",
        email="sarah.jenkins@example.com",
        role="CAREGIVER"
    )
    pat_user = User(
        username="patient",
        hashed_password=get_password_hash("patient123"),
        full_name="Robert Jenkins",
        email="robert.jenkins@example.com",
        role="PATIENT"
    )

    db.add_all([doc_user, cg_user, pat_user])
    await db.commit()
    await db.refresh(doc_user)
    await db.refresh(cg_user)
    await db.refresh(pat_user)

    # 2. Profiles
    doctor = Doctor(
        user_id=doc_user.id,
        name="Dr. Emily Vance, MD",
        email=doc_user.email,
        specialty="Movement Disorders Neurology",
        clinic_name="Advanced Neurological & Voice Center",
        phone="(555) 839-2041"
    )
    caregiver = Caregiver(
        user_id=cg_user.id,
        name="Sarah Jenkins",
        email=cg_user.email,
        phone="(555) 712-4490",
        relationship_type="Daughter / Primary Caregiver"
    )
    db.add_all([doctor, caregiver])
    await db.commit()
    await db.refresh(doctor)
    await db.refresh(caregiver)

    patient = Patient(
        user_id=pat_user.id,
        name="Robert Jenkins",
        date_of_birth="1955-04-12",
        gender="Male",
        diagnosis_year=2021,
        doctor_id=doctor.id,
        caregiver_id=caregiver.id,
        baseline_hnr=19.5,
        notes="Idiopathic Parkinson's Disease. Monitored for vocal hypophonia and afternoon wearing-off dips."
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    # 3. Medications
    med1 = Medication(
        patient_id=patient.id,
        doctor_id=doctor.id,
        name="Carbidopa / Levodopa",
        dosage="25 / 100 mg",
        frequency="3 times daily",
        scheduled_times_json=json.dumps(["08:00", "13:00", "18:00"]),
        instructions="Take with water 30 minutes before meals. Avoid high protein at dosing time.",
        is_active=True
    )
    med2 = Medication(
        patient_id=patient.id,
        doctor_id=doctor.id,
        name="Rasagiline (Azilect)",
        dosage="1 mg",
        frequency="Once daily",
        scheduled_times_json=json.dumps(["08:00"]),
        instructions="Take in the morning with breakfast.",
        is_active=True
    )
    db.add_all([med1, med2])
    await db.commit()
    await db.refresh(med1)
    await db.refresh(med2)

    # 4. Generate 90 Days of Historical Voice Samples + Longitudinal Trend
    now = datetime.datetime.now(datetime.timezone.utc)
    random.seed(42)

    # Base risk trajectory starting from 0.42 90 days ago, with wearing-off fluctuations and slight recent elevation
    samples_to_add = []
    features_to_add = []
    results_to_add = []

    for day_offset in range(90, 0, -2):
        base_time = now - datetime.timedelta(days=day_offset)
        # Create 1-2 samples per recorded day
        times_of_day = [
            base_time.replace(hour=8, minute=15, second=0),
            base_time.replace(hour=12, minute=45, second=0)  # Pre-13:00 dose (wearing-off period)
        ]

        for sample_time in times_of_day:
            is_pre_dose = sample_time.hour == 12

            # Trend progression
            progression = (90 - day_offset) / 90.0 * 0.12
            base_score = 0.40 + progression

            # Pre-dose wearing off dip adds +0.18 risk
            if is_pre_dose and day_offset < 45:
                risk_score = min(0.88, base_score + 0.18 + random.uniform(-0.03, 0.04))
            else:
                risk_score = min(0.85, base_score + random.uniform(-0.04, 0.04))

            confidence = round(random.uniform(0.84, 0.96), 3)

            if risk_score < 0.35:
                sev = "LOW_RISK"
            elif risk_score < 0.60:
                sev = "MILD"
            elif risk_score < 0.80:
                sev = "MODERATE"
            else:
                sev = "SEVERE"

            vs = VoiceSample(
                patient_id=patient.id,
                recorded_by_user_id=pat_user.id,
                timestamp=sample_time,
                task_type="SUSTAINED_A",
                file_path=f"data/uploads/synthetic_sample_p{patient.id}_{int(sample_time.timestamp())}.wav",
                audio_duration_sec=3.5,
                sample_rate=44100,
                status="CLASSIFIED"
            )
            db.add(vs)
            await db.flush()

            jitter = round(0.005 + risk_score * 0.012 + random.uniform(-0.001, 0.001), 5)
            shimmer = round(0.025 + risk_score * 0.045 + random.uniform(-0.003, 0.003), 5)
            hnr = round(24.0 - risk_score * 9.0 + random.uniform(-0.5, 0.5), 2)
            f0 = round(152.0 + random.uniform(-6.0, 6.0), 2)

            ef = ExtractedFeatures(
                voice_sample_id=vs.id,
                jitter_local=jitter,
                jitter_rap=round(jitter * 0.52, 5),
                jitter_ppq5=round(jitter * 0.55, 5),
                shimmer_local=shimmer,
                shimmer_apq3=round(shimmer * 0.5, 5),
                shimmer_apq5=round(shimmer * 0.6, 5),
                hnr=hnr,
                f0_mean=f0,
                f0_std=round(jitter * 150.0, 2),
                f0_min=round(f0 - 15.0, 2),
                f0_max=round(f0 + 20.0, 2),
                ppe=round(0.12 + risk_score * 0.18, 4),
                spread1=round(-6.5 + risk_score * 2.2, 4),
                spread2=round(0.15 + risk_score * 0.14, 4)
            )
            db.add(ef)

            cr = ClassificationResult(
                voice_sample_id=vs.id,
                risk_score=round(risk_score, 4),
                confidence=confidence,
                severity_level=sev,
                model_version="rf-gb-v1.0.0-oxford",
                inference_time_ms=12.4
            )
            db.add(cr)

    # 5. Medication Logs (Last 14 days)
    for d in range(14, 0, -1):
        log_day = now - datetime.timedelta(days=d)
        for sched_time_str in ["08:00", "13:00", "18:00"]:
            hh, mm = map(int, sched_time_str.split(":"))
            sched_dt = log_day.replace(hour=hh, minute=mm, second=0)

            # Pre-dose note for afternoon doses to simulate wearing-off correlation
            notes = "Taken on time."
            if sched_time_str == "13:00" and d < 7:
                notes = "Taken on time. | Pre-dose risk elevation detected (0.72 vs 0.49 baseline)."

            ml = MedicationLog(
                medication_id=med1.id,
                patient_id=patient.id,
                logged_by_user_id=cg_user.id if random.random() > 0.5 else pat_user.id,
                status="TAKEN",
                scheduled_time=sched_dt,
                actual_time=sched_dt + datetime.timedelta(minutes=random.randint(-5, 15)),
                notes=notes
            )
            db.add(ml)

    # 6. Therapy Sessions (Last 30 days)
    for d in range(30, 0, -3):
        th_dt = (now - datetime.timedelta(days=d)).replace(hour=10, minute=30, second=0)
        score = round(random.uniform(76.0, 95.0), 1)
        ts = TherapySession(
            patient_id=patient.id,
            exercise_type="SUSTAINED_VOWEL_AH",
            target_pitch_hz=160.0,
            target_volume_db=75.0,
            duration_sec=round(random.uniform(6.5, 11.2), 1),
            avg_volume_db=round(random.uniform(73.5, 78.8), 1),
            pitch_stability_pct=round(random.uniform(80.0, 94.0), 1),
            score=score,
            feedback_notes="Excellent sustained vocal effort with target decibel control.",
            timestamp=th_dt
        )
        db.add(ts)

    # 7. Alerts
    alert1 = Alert(
        patient_id=patient.id,
        type="WEARING_OFF_DIP",
        severity="WARNING",
        title="Medication Wearing-Off Pattern Detected",
        message="Repeated pre-dose vocal stability dips observed across 3 recent afternoon doses for Carbidopa / Levodopa. Doctor review recommended.",
        trigger_time=now - datetime.timedelta(days=1, hours=2),
        status="ACTIVE",
        recipient_roles_json=json.dumps(["DOCTOR", "CAREGIVER"])
    )
    alert2 = Alert(
        patient_id=patient.id,
        type="DECLINE_GRADUAL",
        severity="INFORMATIONAL",
        title="Gradual Vocal Stability Drift Observed",
        message="Rolling acoustic risk trend indicates a mild gradual upward drift over recent sessions (+11.8%). Continue daily speech therapy.",
        trigger_time=now - datetime.timedelta(days=3),
        status="ACTIVE",
        recipient_roles_json=json.dumps(["PATIENT", "CAREGIVER", "DOCTOR"])
    )
    db.add_all([alert1, alert2])

    await db.commit()
    print("[SEED] Database successfully seeded with rich 90-day clinical trajectory.")

if __name__ == "__main__":
    import asyncio
    from backend.app.core.database import AsyncSessionLocal, init_db
    async def main():
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_database(session)
    asyncio.run(main())
