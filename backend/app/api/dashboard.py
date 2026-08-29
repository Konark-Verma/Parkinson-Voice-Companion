import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, TokenData
from backend.app.core.config import CLINICAL_SAFETY_DISCLAIMER
from backend.app.models.models import (
    Patient, Doctor, Caregiver, VoiceSample, ExtractedFeatures,
    ClassificationResult, Medication, MedicationLog, TherapySession, Alert
)
from backend.app.schemas.schemas import (
    DoctorPatientDetailDashboard, PatientSummary, LongitudinalTrendPoint,
    MedicationResponse, MedicationLogResponse, TherapySessionResponse, AlertResponse
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Clinical Reporting"])

@router.get("/doctor/patient/{patient_id}", response_model=DoctorPatientDetailDashboard)
async def get_doctor_patient_dashboard(
    patient_id: int,
    days: int = Query(90, ge=7, le=365),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated clinical dashboard for a patient.
    Optimized to return 90-day longitudinal trends, medication correlations,
    therapy history, and decline alerts in < 1 second.
    """
    # 1. Fetch Patient
    p_stmt = select(Patient).where(Patient.id == patient_id)
    p_res = await db.execute(p_stmt)
    patient = p_res.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Doctor and Caregiver link checks
    if current_user.role == "DOCTOR" and patient.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Patient is not assigned to your clinic")
    if current_user.role == "CAREGIVER" and patient.caregiver_id != current_user.caregiver_id:
        raise HTTPException(status_code=403, detail="Access restricted to linked caregiver")
    if current_user.role == "PATIENT" and patient.id != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    # 2. Fetch Voice Samples + Features + Classifications (90 Days)
    samples_stmt = (
        select(VoiceSample, ExtractedFeatures, ClassificationResult)
        .outerjoin(ExtractedFeatures, VoiceSample.id == ExtractedFeatures.voice_sample_id)
        .outerjoin(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
        .where(VoiceSample.patient_id == patient_id)
        .where(VoiceSample.timestamp >= cutoff_date)
        .where(VoiceSample.status == "CLASSIFIED")
        .order_by(VoiceSample.timestamp)
    )
    samples_res = await db.execute(samples_stmt)
    sample_rows = samples_res.all()

    # 3. Fetch Medication Logs (90 Days)
    med_logs_stmt = (
        select(MedicationLog, Medication.name)
        .join(Medication, MedicationLog.medication_id == Medication.id)
        .where(MedicationLog.patient_id == patient_id)
        .where(MedicationLog.scheduled_time >= cutoff_date)
        .order_by(desc(MedicationLog.scheduled_time))
    )
    med_logs_res = await db.execute(med_logs_stmt)
    med_log_rows = med_logs_res.all()

    # Map logs by date string for quick correlation
    meds_by_date = {}
    for log, med_name in med_log_rows:
        d_str = log.scheduled_time.strftime("%Y-%m-%d")
        if d_str not in meds_by_date:
            meds_by_date[d_str] = []
        meds_by_date[d_str].append((log, med_name))

    # Construct Longitudinal Trend Points
    trend_points = []
    for s, f, c in sample_rows:
        d_str = s.timestamp.strftime("%Y-%m-%d %H:%M")
        day_str = s.timestamp.strftime("%Y-%m-%d")
        med_day_logs = meds_by_date.get(day_str, [])

        is_med_taken = any(l.status == "TAKEN" for l, _ in med_day_logs)
        m_name = med_day_logs[0][1] if med_day_logs else None
        is_pre_dip = any(bool(l.notes and "Pre-dose risk elevation" in l.notes) for l, _ in med_day_logs)

        trend_points.append(LongitudinalTrendPoint(
            date=d_str,
            risk_score=c.risk_score if c else 0.0,
            confidence=c.confidence if c else 0.85,
            severity_level=c.severity_level if c else "NORMAL",
            jitter=f.jitter_local if f else None,
            shimmer=f.shimmer_local if f else None,
            hnr=f.hnr if f else None,
            f0_mean=f.f0_mean if f else None,
            medication_taken=is_med_taken,
            medication_name=m_name,
            is_pre_dose_dip=is_pre_dip
        ))

    # 4. Fetch Active Medications
    meds_stmt = select(Medication).where(Medication.patient_id == patient_id).order_by(Medication.name)
    meds_res = await db.execute(meds_stmt)
    medications = [
        MedicationResponse(
            id=m.id,
            patient_id=m.patient_id,
            doctor_id=m.doctor_id,
            name=m.name,
            dosage=m.dosage,
            frequency=m.frequency,
            scheduled_times=json.loads(m.scheduled_times_json) if m.scheduled_times_json else [],
            instructions=m.instructions,
            is_active=m.is_active,
            created_at=m.created_at
        )
        for m in meds_res.scalars().all()
    ]

    # 5. Fetch Recent Medication Logs
    recent_med_logs = [
        MedicationLogResponse(
            id=log.id,
            medication_id=log.medication_id,
            medication_name=med_name,
            patient_id=log.patient_id,
            logged_by_user_id=log.logged_by_user_id,
            status=log.status,
            scheduled_time=log.scheduled_time,
            actual_time=log.actual_time,
            notes=log.notes,
            created_at=log.created_at,
            wearing_off_detected=bool(log.notes and "Pre-dose risk elevation" in log.notes),
            wearing_off_summary=log.notes
        )
        for log, med_name in med_log_rows[:20]
    ]

    # 6. Fetch Therapy Sessions
    therapy_stmt = (
        select(TherapySession)
        .where(TherapySession.patient_id == patient_id)
        .order_by(desc(TherapySession.timestamp))
        .limit(20)
    )
    therapy_res = await db.execute(therapy_stmt)
    therapy_sessions = [
        TherapySessionResponse(
            id=th.id,
            patient_id=th.patient_id,
            exercise_type=th.exercise_type,
            target_pitch_hz=th.target_pitch_hz,
            target_volume_db=th.target_volume_db,
            duration_sec=th.duration_sec,
            avg_volume_db=th.avg_volume_db,
            pitch_stability_pct=th.pitch_stability_pct,
            score=th.score,
            feedback_notes=th.feedback_notes,
            timestamp=th.timestamp
        )
        for th in therapy_res.scalars().all()
    ]

    # 7. Fetch Alerts
    alerts_stmt = (
        select(Alert)
        .where(Alert.patient_id == patient_id)
        .order_by(desc(Alert.trigger_time))
        .limit(20)
    )
    alerts_res = await db.execute(alerts_stmt)
    alerts = [
        AlertResponse(
            id=a.id,
            patient_id=a.patient_id,
            patient_name=patient.name,
            type=a.type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            trigger_time=a.trigger_time,
            status=a.status,
            recipient_roles=json.loads(a.recipient_roles_json) if a.recipient_roles_json else [],
            acknowledged_at=a.acknowledged_at
        )
        for a in alerts_res.scalars().all()
    ]

    # Wearing-Off Summary statistics
    wearing_off_dips_count = sum(1 for l in recent_med_logs if l.wearing_off_detected)
    wearing_off_summary = {
        "total_monitored_doses": len(recent_med_logs),
        "pre_dose_dips_detected": wearing_off_dips_count,
        "wearing_off_rate_pct": round((wearing_off_dips_count / max(1, len(recent_med_logs))) * 100.0, 1),
        "pattern_flagged": wearing_off_dips_count >= 2
    }

    # Latest severity & risk
    latest_risk = trend_points[-1].risk_score if trend_points else None
    latest_sev = trend_points[-1].severity_level if trend_points else "NORMAL"
    active_alerts_cnt = sum(1 for a in alerts if a.status == "ACTIVE")

    patient_summary = PatientSummary(
        id=patient.id,
        name=patient.name,
        date_of_birth=patient.date_of_birth,
        diagnosis_year=patient.diagnosis_year,
        latest_risk_score=latest_risk,
        latest_severity_level=latest_sev,
        active_alerts_count=active_alerts_cnt,
        wearing_off_pattern_flagged=wearing_off_summary["pattern_flagged"],
        last_sample_date=sample_rows[-1][0].timestamp if sample_rows else None
    )

    return DoctorPatientDetailDashboard(
        patient=patient_summary,
        trend_90d=trend_points,
        active_medications=medications,
        recent_medication_logs=recent_med_logs,
        recent_therapy_sessions=therapy_sessions,
        alerts=alerts,
        wearing_off_summary=wearing_off_summary,
        disclaimer=CLINICAL_SAFETY_DISCLAIMER
    )
