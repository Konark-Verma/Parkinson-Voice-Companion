import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, TokenData, require_roles
from backend.app.models.models import Medication, MedicationLog, Patient, Doctor, Caregiver
from backend.app.schemas.schemas import (
    MedicationCreate, MedicationUpdate, MedicationResponse,
    MedicationLogCreate, MedicationLogResponse
)
from backend.app.services.wearing_off_service import wearing_off_service

router = APIRouter(prefix="/medications", tags=["Medications"])

@router.post("", response_model=MedicationResponse)
async def create_medication_schedule(
    med_in: MedicationCreate,
    current_user: TokenData = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Manage Medication Schedule (Doctor only).
    Creates a new medication schedule for a patient.
    """
    # Verify patient belongs to doctor
    p_stmt = select(Patient).where(Patient.id == med_in.patient_id)
    p_res = await db.execute(p_stmt)
    patient = p_res.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if current_user.role == "DOCTOR" and patient.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Cannot prescribe medication for a patient not assigned to your clinic")

    med = Medication(
        patient_id=med_in.patient_id,
        doctor_id=current_user.doctor_id or 1,
        name=med_in.name,
        dosage=med_in.dosage,
        frequency=med_in.frequency,
        scheduled_times_json=json.dumps(med_in.scheduled_times),
        instructions=med_in.instructions,
        is_active=True
    )
    db.add(med)
    await db.commit()
    await db.refresh(med)

    return MedicationResponse(
        id=med.id,
        patient_id=med.patient_id,
        doctor_id=med.doctor_id,
        name=med.name,
        dosage=med.dosage,
        frequency=med.frequency,
        scheduled_times=json.loads(med.scheduled_times_json) if med.scheduled_times_json else [],
        instructions=med.instructions,
        is_active=med.is_active,
        created_at=med.created_at
    )

@router.put("/{medication_id}", response_model=MedicationResponse)
async def update_medication_schedule(
    medication_id: int,
    med_update: MedicationUpdate,
    current_user: TokenData = Depends(require_roles(["DOCTOR", "ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update medication schedule (Doctor only).
    """
    stmt = select(Medication).where(Medication.id == medication_id)
    res = await db.execute(stmt)
    med = res.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    if med_update.name is not None:
        med.name = med_update.name
    if med_update.dosage is not None:
        med.dosage = med_update.dosage
    if med_update.frequency is not None:
        med.frequency = med_update.frequency
    if med_update.scheduled_times is not None:
        med.scheduled_times_json = json.dumps(med_update.scheduled_times)
    if med_update.instructions is not None:
        med.instructions = med_update.instructions
    if med_update.is_active is not None:
        med.is_active = med_update.is_active

    await db.commit()
    await db.refresh(med)

    return MedicationResponse(
        id=med.id,
        patient_id=med.patient_id,
        doctor_id=med.doctor_id,
        name=med.name,
        dosage=med.dosage,
        frequency=med.frequency,
        scheduled_times=json.loads(med.scheduled_times_json) if med.scheduled_times_json else [],
        instructions=med.instructions,
        is_active=med.is_active,
        created_at=med.created_at
    )

@router.get("/patient/{patient_id}", response_model=List[MedicationResponse])
async def list_patient_medications(
    patient_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List active/all medications for a patient.
    """
    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "CAREGIVER":
        p_res = await db.execute(select(Patient).where(Patient.id == patient_id))
        pat = p_res.scalar_one_or_none()
        if not pat or pat.caregiver_id != current_user.caregiver_id:
            raise HTTPException(status_code=403, detail="You are not linked as caregiver for this patient")

    stmt = select(Medication).where(Medication.patient_id == patient_id).order_by(desc(Medication.created_at))
    res = await db.execute(stmt)
    meds = res.scalars().all()

    return [
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
        for m in meds
    ]

@router.post("/log", response_model=MedicationLogResponse)
@router.post("/medication-logs", response_model=MedicationLogResponse)
async def log_medication_intake(
    log_in: MedicationLogCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Log Medication Intake (Patient or linked Caregiver).
    Auto-includes Track Wearing-Off Correlation.
    """
    # Fetch medication
    m_stmt = select(Medication).where(Medication.id == log_in.medication_id)
    m_res = await db.execute(m_stmt)
    med = m_res.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    patient_id = med.patient_id

    # Verify authorization (Patient or linked Caregiver only)
    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Cannot log medication for another patient")
    if current_user.role == "CAREGIVER":
        # Check caregiver link
        p_res = await db.execute(select(Patient).where(Patient.id == patient_id))
        pat = p_res.scalar_one_or_none()
        if not pat or pat.caregiver_id != current_user.caregiver_id:
            raise HTTPException(status_code=403, detail="You are not linked as caregiver for this patient")

    actual_time = log_in.actual_time or datetime.datetime.now(datetime.timezone.utc)

    log_entry = MedicationLog(
        medication_id=med.id,
        patient_id=patient_id,
        logged_by_user_id=current_user.user_id,
        status=log_in.status,
        scheduled_time=log_in.scheduled_time,
        actual_time=actual_time,
        notes=log_in.notes
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    # Base Flow Include: Track Wearing-Off Correlation
    correlation_result = await wearing_off_service.analyze_wearing_off_correlation(
        db=db,
        medication_log=log_entry
    )

    wearing_off_summary = None
    if correlation_result.get("is_wearing_off_dip"):
        wearing_off_summary = (
            f"Wearing-off acoustic dip detected (Pre-dose Risk: {correlation_result.get('pre_score')}). "
            f"{'Repeating pattern notified to Doctor.' if correlation_result.get('pattern_flagged') else 'Monitored for pattern replication.'}"
        )

    return MedicationLogResponse(
        id=log_entry.id,
        medication_id=log_entry.medication_id,
        medication_name=med.name,
        patient_id=log_entry.patient_id,
        logged_by_user_id=log_entry.logged_by_user_id,
        status=log_entry.status,
        scheduled_time=log_entry.scheduled_time,
        actual_time=log_entry.actual_time,
        notes=log_entry.notes,
        created_at=log_entry.created_at,
        wearing_off_detected=correlation_result.get("is_wearing_off_dip", False),
        wearing_off_summary=wearing_off_summary
    )

@router.get("/logs/patient/{patient_id}", response_model=List[MedicationLogResponse])
async def list_medication_logs(
    patient_id: int,
    limit: int = 30,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "CAREGIVER":
        p_res = await db.execute(select(Patient).where(Patient.id == patient_id))
        pat = p_res.scalar_one_or_none()
        if not pat or pat.caregiver_id != current_user.caregiver_id:
            raise HTTPException(status_code=403, detail="You are not linked as caregiver for this patient")

    stmt = (
        select(MedicationLog, Medication.name)
        .join(Medication, MedicationLog.medication_id == Medication.id)
        .where(MedicationLog.patient_id == patient_id)
        .order_by(desc(MedicationLog.scheduled_time))
        .limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
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
        for log, med_name in rows
    ]
