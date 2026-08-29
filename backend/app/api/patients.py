from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, TokenData
from backend.app.models.models import Patient, Doctor, Caregiver, VoiceSample, ClassificationResult, Alert, Medication, MedicationLog, TherapySession
from backend.app.schemas.schemas import PatientSummary

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[PatientSummary])
async def list_patients(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns patients accessible to the current user according to RBAC.
    """
    if current_user.role == "DOCTOR":
        stmt = select(Patient).where(Patient.doctor_id == current_user.doctor_id)
    elif current_user.role == "CAREGIVER":
        stmt = select(Patient).where(Patient.caregiver_id == current_user.caregiver_id)
    elif current_user.role == "PATIENT":
        stmt = select(Patient).where(Patient.id == current_user.patient_id)
    else:
        stmt = select(Patient)

    res = await db.execute(stmt)
    patients = res.scalars().all()

    summaries = []
    for p in patients:
        # Fetch latest classification
        sample_stmt = (
            select(VoiceSample, ClassificationResult)
            .outerjoin(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
            .where(VoiceSample.patient_id == p.id)
            .where(VoiceSample.status == "CLASSIFIED")
            .order_by(desc(VoiceSample.timestamp))
            .limit(1)
        )
        sample_res = await db.execute(sample_stmt)
        latest_sample = sample_res.first()

        latest_risk = latest_sample[1].risk_score if latest_sample and latest_sample[1] else None
        latest_sev = latest_sample[1].severity_level if latest_sample and latest_sample[1] else "NORMAL"
        last_date = latest_sample[0].timestamp if latest_sample else None

        # Fetch active alerts count
        alert_stmt = (
            select(Alert)
            .where(Alert.patient_id == p.id)
            .where(Alert.status == "ACTIVE")
        )
        alert_res = await db.execute(alert_stmt)
        active_alerts = alert_res.scalars().all()
        has_wearing_off = any(a.type == "WEARING_OFF_DIP" for a in active_alerts)

        # Lookup doctor & caregiver names
        doc_name = None
        if p.doctor_id:
            d_res = await db.execute(select(Doctor).where(Doctor.id == p.doctor_id))
            d = d_res.scalar_one_or_none()
            if d:
                doc_name = d.name

        cg_name = None
        if p.caregiver_id:
            c_res = await db.execute(select(Caregiver).where(Caregiver.id == p.caregiver_id))
            c = c_res.scalar_one_or_none()
            if c:
                cg_name = c.name

        summaries.append(PatientSummary(
            id=p.id,
            name=p.name,
            date_of_birth=p.date_of_birth,
            diagnosis_year=p.diagnosis_year,
            doctor_name=doc_name,
            caregiver_name=cg_name,
            latest_risk_score=latest_risk,
            latest_severity_level=latest_sev,
            active_alerts_count=len(active_alerts),
            wearing_off_pattern_flagged=has_wearing_off,
            last_sample_date=last_date
        ))

    return summaries

@router.get("/{patient_id}", response_model=PatientSummary)
async def get_patient(
    patient_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # RBAC check
    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied to patient profile")

    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "DOCTOR" and p.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Patient is not assigned to your clinic")
    if current_user.role == "CAREGIVER" and p.caregiver_id != current_user.caregiver_id:
        raise HTTPException(status_code=403, detail="Patient is not linked to your caregiver account")

    # Fetch latest status
    sample_stmt = (
        select(VoiceSample, ClassificationResult)
        .outerjoin(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
        .where(VoiceSample.patient_id == p.id)
        .where(VoiceSample.status == "CLASSIFIED")
        .order_by(desc(VoiceSample.timestamp))
        .limit(1)
    )
    sample_res = await db.execute(sample_stmt)
    latest_sample = sample_res.first()

    latest_risk = latest_sample[1].risk_score if latest_sample and latest_sample[1] else None
    latest_sev = latest_sample[1].severity_level if latest_sample and latest_sample[1] else "NORMAL"
    last_date = latest_sample[0].timestamp if latest_sample else None

    alert_stmt = select(Alert).where(Alert.patient_id == p.id).where(Alert.status == "ACTIVE")
    alert_res = await db.execute(alert_stmt)
    active_alerts = alert_res.scalars().all()

    # Lookup doctor & caregiver names
    doc_name = None
    if p.doctor_id:
        d_res = await db.execute(select(Doctor).where(Doctor.id == p.doctor_id))
        d = d_res.scalar_one_or_none()
        if d:
            doc_name = d.name

    cg_name = None
    if p.caregiver_id:
        c_res = await db.execute(select(Caregiver).where(Caregiver.id == p.caregiver_id))
        c = c_res.scalar_one_or_none()
        if c:
            cg_name = c.name

    return PatientSummary(
        id=p.id,
        name=p.name,
        date_of_birth=p.date_of_birth,
        diagnosis_year=p.diagnosis_year,
        doctor_name=doc_name,
        caregiver_name=cg_name,
        latest_risk_score=latest_risk,
        latest_severity_level=latest_sev,
        active_alerts_count=len(active_alerts),
        wearing_off_pattern_flagged=any(a.type == "WEARING_OFF_DIP" for a in active_alerts),
        last_sample_date=last_date
    )

@router.get("/{patient_id}/caregiver-status")
async def get_caregiver_patient_status(
    patient_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns compact status update summary for the Caregiver view:
    - Latest acoustic risk & severity
    - Last logged medication intake
    - Last speech therapy session date & score
    - Active alerts summary
    """
    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "CAREGIVER" and p.caregiver_id != current_user.caregiver_id:
        raise HTTPException(status_code=403, detail="Patient is not linked to your caregiver account")
    if current_user.role == "PATIENT" and p.id != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 1. Latest Voice Sample Classification
    sample_stmt = (
        select(VoiceSample, ClassificationResult)
        .outerjoin(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
        .where(VoiceSample.patient_id == p.id)
        .where(VoiceSample.status == "CLASSIFIED")
        .order_by(desc(VoiceSample.timestamp))
        .limit(1)
    )
    sample_res = await db.execute(sample_stmt)
    latest_sample = sample_res.first()

    latest_risk = latest_sample[1].risk_score if latest_sample and latest_sample[1] else None
    latest_sev = latest_sample[1].severity_level if latest_sample and latest_sample[1] else "NORMAL"
    last_sample_date = latest_sample[0].timestamp if latest_sample else None

    # 2. Last Logged Medication Dose
    med_log_stmt = (
        select(MedicationLog, Medication.name)
        .join(Medication, MedicationLog.medication_id == Medication.id)
        .where(MedicationLog.patient_id == p.id)
        .order_by(desc(MedicationLog.created_at))
        .limit(1)
    )
    med_log_res = await db.execute(med_log_stmt)
    last_med_row = med_log_res.first()

    last_med_info = None
    if last_med_row:
        mlog, mname = last_med_row
        last_med_info = {
            "id": mlog.id,
            "medication_name": mname,
            "status": mlog.status,
            "scheduled_time": mlog.scheduled_time.isoformat() if mlog.scheduled_time else None,
            "actual_time": mlog.actual_time.isoformat() if mlog.actual_time else None,
            "notes": mlog.notes
        }

    # 3. Last Speech Therapy Session
    therapy_stmt = (
        select(TherapySession)
        .where(TherapySession.patient_id == p.id)
        .order_by(desc(TherapySession.timestamp))
        .limit(1)
    )
    therapy_res = await db.execute(therapy_stmt)
    last_th = therapy_res.scalar_one_or_none()

    last_therapy_info = None
    if last_th:
        last_therapy_info = {
            "id": last_th.id,
            "exercise_type": last_th.exercise_type,
            "score": last_th.score,
            "timestamp": last_th.timestamp.isoformat() if last_th.timestamp else None
        }

    # 4. Active Alerts Count
    alert_stmt = select(Alert).where(Alert.patient_id == p.id).where(Alert.status == "ACTIVE")
    alert_res = await db.execute(alert_stmt)
    active_alerts = alert_res.scalars().all()

    # Doctor name
    doc_name = None
    if p.doctor_id:
        d_res = await db.execute(select(Doctor).where(Doctor.id == p.doctor_id))
        d = d_res.scalar_one_or_none()
        if d:
            doc_name = d.name

    return {
        "patient": {
            "id": p.id,
            "name": p.name,
            "diagnosis_year": p.diagnosis_year,
            "doctor_name": doc_name,
            "latest_risk_score": latest_risk,
            "latest_severity_level": latest_sev,
            "last_sample_date": last_sample_date.isoformat() if last_sample_date else None,
        },
        "status_summary": {
            "active_alerts_count": len(active_alerts),
            "wearing_off_flagged": any(a.type == "WEARING_OFF_DIP" for a in active_alerts),
            "last_logged_medication": last_med_info,
            "last_therapy_session": last_therapy_info,
        }
    }

