import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.models import Alert, Patient, Doctor, Caregiver, User
from backend.app.websocket.ws_manager import ws_manager

logger = logging.getLogger("notification_service")

class AlertNotificationService:
    @staticmethod
    async def deliver_alert(
        db: AsyncSession,
        patient_id: int,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        recipient_roles: Optional[List[str]] = None
    ) -> Alert:
        """
        Creates an alert in the database and dispatches it via real-time WebSocket
        and notification channels to relevant recipients.
        """
        if recipient_roles is None:
            if severity == "URGENT":
                recipient_roles = ["PATIENT", "CAREGIVER", "DOCTOR"]
            elif severity == "WARNING":
                recipient_roles = ["PATIENT", "CAREGIVER", "DOCTOR"]
            else:
                recipient_roles = ["PATIENT", "CAREGIVER"]

        # 1. Save Alert entity
        alert = Alert(
            patient_id=patient_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            trigger_time=datetime.now(timezone.utc),
            status="ACTIVE",
            recipient_roles_json=json.dumps(recipient_roles)
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        # 2. Lookup recipient User IDs
        patient_stmt = select(Patient).where(Patient.id == patient_id)
        res = await db.execute(patient_stmt)
        patient = res.scalar_one_or_none()

        target_user_ids = []
        patient_name = patient.name if patient else "Patient"

        if patient:
            if "PATIENT" in recipient_roles and patient.user_id:
                target_user_ids.append(patient.user_id)
            if "CAREGIVER" in recipient_roles and patient.caregiver_id:
                cg_res = await db.execute(select(Caregiver).where(Caregiver.id == patient.caregiver_id))
                cg = cg_res.scalar_one_or_none()
                if cg and cg.user_id:
                    target_user_ids.append(cg.user_id)
            if "DOCTOR" in recipient_roles and patient.doctor_id:
                doc_res = await db.execute(select(Doctor).where(Doctor.id == patient.doctor_id))
                doc = doc_res.scalar_one_or_none()
                if doc and doc.user_id:
                    target_user_ids.append(doc.user_id)

        # 3. Payload for Real-Time Dispatch
        payload = {
            "event": "NEW_ALERT",
            "alert": {
                "id": alert.id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "type": alert_type,
                "severity": severity,
                "title": title,
                "message": message,
                "trigger_time": alert.trigger_time.isoformat(),
                "status": "ACTIVE",
                "recipient_roles": recipient_roles
            }
        }

        # 4. WebSocket Delivery
        for uid in target_user_ids:
            await ws_manager.send_to_user(uid, payload)

        # If urgent, also ensure all active doctors get notified
        if severity == "URGENT":
            await ws_manager.broadcast_to_role("DOCTOR", payload)

        # 5. External Channel Simulation (SMS/Email/Push)
        logger.info(
            f"[ALERT NOTIFICATION] Dispatched {severity} Alert #{alert.id} ({alert_type}) "
            f"for Patient {patient_name} to roles={recipient_roles} via WebSocket & Mock-SMS/Push gateway."
        )

        return alert

notification_service = AlertNotificationService()
