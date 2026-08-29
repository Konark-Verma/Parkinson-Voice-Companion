import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.models.models import VoiceSample, ClassificationResult, Alert
from backend.app.services.notification_service import notification_service

class DeclineDetectionService:
    @staticmethod
    async def evaluate_change_point(
        db: AsyncSession,
        patient_id: int,
        latest_sample_id: int,
        latest_risk_score: float
    ) -> Optional[Alert]:
        """
        Extension point 'OnSeverityChange'.
        Runs statistical change-point detection (rolling mean/variance shift) over the patient's
        historical classifications to detect gradual or sudden acoustic vocal degradation.
        """
        # Fetch historical classifications for this patient (most recent 30 samples)
        stmt = (
            select(VoiceSample.timestamp, ClassificationResult.risk_score)
            .join(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
            .where(VoiceSample.patient_id == patient_id)
            .where(VoiceSample.status == "CLASSIFIED")
            .order_by(desc(VoiceSample.timestamp))
            .limit(30)
        )
        res = await db.execute(stmt)
        rows = res.all()

        if len(rows) < 3:
            # Need at least 3 samples to evaluate baseline and shift
            return None

        # Sort chronologically
        history = list(reversed(rows))
        scores = np.array([r[1] for r in history])
        timestamps = [r[0] for r in history]

        current_score = latest_risk_score

        # Check for duplicate recent active alert within last 24h to prevent spamming
        recent_alert_stmt = (
            select(Alert)
            .where(Alert.patient_id == patient_id)
            .where(Alert.status == "ACTIVE")
            .where(Alert.type.in_(["DECLINE_SUDDEN", "DECLINE_GRADUAL"]))
            .order_by(desc(Alert.trigger_time))
            .limit(1)
        )
        recent_alert_res = await db.execute(recent_alert_stmt)
        recent_alert = recent_alert_res.scalar_one_or_none()

        if recent_alert:
            # If an alert was generated in the last 12 hours, avoid duplicates unless it's sudden
            if (datetime.now(timezone.utc) - recent_alert.trigger_time.replace(tzinfo=timezone.utc)).total_seconds() < 43200:
                if recent_alert.severity == "URGENT":
                    return None

        # 1. Sudden Shift Check (Window: last 2-3 samples vs baseline)
        if len(scores) >= 3:
            baseline_window = scores[:-2] if len(scores) > 4 else scores[:-1]
            baseline_mean = float(np.mean(baseline_window))
            baseline_std = float(np.std(baseline_window)) if np.std(baseline_window) > 0.02 else 0.05

            recent_jump = current_score - baseline_mean
            z_score = recent_jump / baseline_std

            # Check sudden jump: delta >= 0.22 or z_score >= 2.8
            if recent_jump >= 0.20 or z_score >= 2.8:
                alert = await notification_service.deliver_alert(
                    db=db,
                    patient_id=patient_id,
                    alert_type="DECLINE_SUDDEN",
                    severity="URGENT",
                    title="Sudden Vocal Stability Shift Detected",
                    message=(
                        f"Significant sudden increase in acoustic risk score ({baseline_mean:.2f} -> {current_score:.2f}, "
                        f"+{recent_jump*100:.1f}%, z={z_score:.1f}) detected. Immediate clinical review recommended."
                    ),
                    recipient_roles=["PATIENT", "CAREGIVER", "DOCTOR"]
                )
                return alert

        # 2. Gradual Drift Check (Window: 7-30 days rolling mean slope / shift)
        if len(scores) >= 6:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            mean_first = float(np.mean(first_half))
            mean_second = float(np.mean(second_half))
            gradual_shift = mean_second - mean_first

            if gradual_shift >= 0.12:
                alert = await notification_service.deliver_alert(
                    db=db,
                    patient_id=patient_id,
                    alert_type="DECLINE_GRADUAL",
                    severity="WARNING",
                    title="Gradual Vocal Stability Decline Observed",
                    message=(
                        f"Rolling acoustic risk trend indicates a gradual upward drift over recent sessions "
                        f"({mean_first:.2f} baseline -> {mean_second:.2f} current average, +{gradual_shift*100:.1f}%). "
                        f"Consider reviewing speech therapy exercise adherence."
                    ),
                    recipient_roles=["PATIENT", "CAREGIVER", "DOCTOR"]
                )
                return alert

        return None

decline_detection_service = DeclineDetectionService()
