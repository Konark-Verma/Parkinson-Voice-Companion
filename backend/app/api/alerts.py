import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, TokenData
from backend.app.models.models import Alert, Patient
from backend.app.schemas.schemas import AlertResponse, AlertAcknowledgeRequest
from backend.app.services.notification_service import notification_service

router = APIRouter(prefix="/alerts", tags=["Decline Alerts"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    patient_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    View Decline Alerts (Patient, Caregiver, Doctor).
    Filters alerts based on RBAC and target patient.
    """
    stmt = (
        select(Alert, Patient.name)
        .join(Patient, Alert.patient_id == Patient.id)
        .order_by(desc(Alert.trigger_time))
    )

    if patient_id:
        stmt = stmt.where(Alert.patient_id == patient_id)
    elif current_user.role == "PATIENT":
        stmt = stmt.where(Alert.patient_id == current_user.patient_id)
    elif current_user.role == "CAREGIVER":
        # Linked patients only
        stmt = stmt.where(Patient.caregiver_id == current_user.caregiver_id)
    elif current_user.role == "DOCTOR":
        stmt = stmt.where(Patient.doctor_id == current_user.doctor_id)

    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)

    res = await db.execute(stmt)
    rows = res.all()

    output = []
    for alert, pat_name in rows:
        roles = json.loads(alert.recipient_roles_json) if alert.recipient_roles_json else ["PATIENT", "CAREGIVER", "DOCTOR"]
        output.append(AlertResponse(
            id=alert.id,
            patient_id=alert.patient_id,
            patient_name=pat_name,
            type=alert.type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            trigger_time=alert.trigger_time,
            status=alert.status,
            recipient_roles=roles,
            acknowledged_at=alert.acknowledged_at
        ))

    return output

@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    ack_req: AlertAcknowledgeRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge a decline or medication alert.
    """
    stmt = select(Alert).where(Alert.id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = ack_req.status or "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.datetime.now(datetime.timezone.utc)
    alert.acknowledged_by_user_id = current_user.user_id
    await db.commit()
    await db.refresh(alert)

    # Get patient name
    p_res = await db.execute(select(Patient.name).where(Patient.id == alert.patient_id))
    pat_name = p_res.scalar_one_or_none()

    roles = json.loads(alert.recipient_roles_json) if alert.recipient_roles_json else []
    return AlertResponse(
        id=alert.id,
        patient_id=alert.patient_id,
        patient_name=pat_name,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        trigger_time=alert.trigger_time,
        status=alert.status,
        recipient_roles=roles,
        acknowledged_at=alert.acknowledged_at
    )

@router.post("/test-trigger", response_model=AlertResponse)
async def trigger_test_alert(
    patient_id: int,
    alert_type: str = "DECLINE_SUDDEN",
    severity: str = "URGENT",
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint for demonstration & testing of the Alert Notification Service.
    """
    title = "Test Sudden Vocal Stability Decline" if alert_type == "DECLINE_SUDDEN" else "Test Informational Decline Alert"
    msg = "Simulated sudden vocal biomarker fluctuation detected for demonstration purposes."
    alert = await notification_service.deliver_alert(
        db=db,
        patient_id=patient_id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=msg
    )

    p_res = await db.execute(select(Patient.name).where(Patient.id == patient_id))
    pat_name = p_res.scalar_one_or_none()

    return AlertResponse(
        id=alert.id,
        patient_id=alert.patient_id,
        patient_name=pat_name,
        type=alert.type,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        trigger_time=alert.trigger_time,
        status=alert.status,
        recipient_roles=json.loads(alert.recipient_roles_json),
        acknowledged_at=alert.acknowledged_at
    )
