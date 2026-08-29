import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, TokenData
from backend.app.models.models import TherapySession, Patient
from backend.app.schemas.schemas import TherapySessionCreate, TherapySessionResponse

router = APIRouter(prefix="/therapy", tags=["Speech Therapy Coach"])

@router.post("/sessions", response_model=TherapySessionResponse)
async def record_therapy_session(
    session_in: TherapySessionCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save completed therapy session score, volume/pitch metrics, and timestamp to history.
    """
    patient_id = session_in.patient_id or current_user.patient_id
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID is required")

    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Cannot save therapy session for another patient")

    session_obj = TherapySession(
        patient_id=patient_id,
        exercise_type=session_in.exercise_type,
        target_pitch_hz=session_in.target_pitch_hz,
        target_volume_db=session_in.target_volume_db,
        duration_sec=session_in.duration_sec,
        avg_volume_db=session_in.avg_volume_db,
        pitch_stability_pct=session_in.pitch_stability_pct,
        score=session_in.score,
        feedback_notes=session_in.feedback_notes,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)

    return TherapySessionResponse(
        id=session_obj.id,
        patient_id=session_obj.patient_id,
        exercise_type=session_obj.exercise_type,
        target_pitch_hz=session_obj.target_pitch_hz,
        target_volume_db=session_obj.target_volume_db,
        duration_sec=session_obj.duration_sec,
        avg_volume_db=session_obj.avg_volume_db,
        pitch_stability_pct=session_obj.pitch_stability_pct,
        score=session_obj.score,
        feedback_notes=session_obj.feedback_notes,
        timestamp=session_obj.timestamp
    )

@router.get("/patient/{patient_id}", response_model=List[TherapySessionResponse])
async def get_patient_therapy_history(
    patient_id: int,
    limit: int = 30,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    View Therapy History (Patient, Doctor).
    """
    if current_user.role == "PATIENT" and current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Access denied to therapy history")

    stmt = (
        select(TherapySession)
        .where(TherapySession.patient_id == patient_id)
        .order_by(desc(TherapySession.timestamp))
        .limit(limit)
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    return [
        TherapySessionResponse(
            id=s.id,
            patient_id=s.patient_id,
            exercise_type=s.exercise_type,
            target_pitch_hz=s.target_pitch_hz,
            target_volume_db=s.target_volume_db,
            duration_sec=s.duration_sec,
            avg_volume_db=s.avg_volume_db,
            pitch_stability_pct=s.pitch_stability_pct,
            score=s.score,
            feedback_notes=s.feedback_notes,
            timestamp=s.timestamp
        )
        for s in sessions
    ]
