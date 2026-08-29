import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.models.models import MedicationLog, Medication, VoiceSample, ClassificationResult, Alert
from backend.app.services.notification_service import notification_service

class WearingOffService:
    @staticmethod
    async def analyze_wearing_off_correlation(
        db: AsyncSession,
        medication_log: MedicationLog
    ) -> Dict[str, Any]:
        """
        Include-relationship: Track Wearing-Off Correlation.
        Triggered automatically whenever a medication intake is logged.
        Joins recent classifier severity readings against the scheduled/actual dose timestamp
        to detect pre-dose 'wearing-off' dips and alerts the Doctor when repeating patterns occur.
        """
        patient_id = medication_log.patient_id
        dose_time = medication_log.actual_time or medication_log.scheduled_time

        # Time window: pre-dose (-120 min to 0 min) and post-dose (0 min to +120 min)
        pre_window_start = dose_time - datetime.timedelta(minutes=120)
        pre_window_end = dose_time + datetime.timedelta(minutes=15)
        post_window_start = dose_time
        post_window_end = dose_time + datetime.timedelta(minutes=150)

        # 1. Fetch voice samples in the pre-dose window
        pre_stmt = (
            select(VoiceSample, ClassificationResult)
            .join(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
            .where(VoiceSample.patient_id == patient_id)
            .where(VoiceSample.timestamp >= pre_window_start)
            .where(VoiceSample.timestamp <= pre_window_end)
            .order_by(desc(VoiceSample.timestamp))
        )
        pre_res = await db.execute(pre_stmt)
        pre_samples = pre_res.all()

        # 2. Fetch voice samples in the post-dose window
        post_stmt = (
            select(VoiceSample, ClassificationResult)
            .join(ClassificationResult, VoiceSample.id == ClassificationResult.voice_sample_id)
            .where(VoiceSample.patient_id == patient_id)
            .where(VoiceSample.timestamp >= post_window_start)
            .where(VoiceSample.timestamp <= post_window_end)
            .order_by(VoiceSample.timestamp)
        )
        post_res = await db.execute(post_stmt)
        post_samples = post_res.all()

        # Fetch patient's overall baseline average risk score
        baseline_stmt = (
            select(ClassificationResult.risk_score)
            .join(VoiceSample, VoiceSample.id == ClassificationResult.voice_sample_id)
            .where(VoiceSample.patient_id == patient_id)
            .limit(20)
        )
        baseline_res = await db.execute(baseline_stmt)
        all_scores = baseline_res.scalars().all()
        baseline_avg = sum(all_scores) / len(all_scores) if all_scores else 0.40

        pre_score = pre_samples[0][1].risk_score if pre_samples else None
        post_score = post_samples[0][1].risk_score if post_samples else None

        # Check if pre-dose dip occurred
        is_wearing_off_dip = False
        notes_summary = []

        if pre_score is not None:
            elevation = pre_score - baseline_avg
            if elevation >= 0.15 or (post_score is not None and (pre_score - post_score) >= 0.15):
                is_wearing_off_dip = True
                notes_summary.append(f"Pre-dose risk elevation detected ({pre_score:.2f} vs {baseline_avg:.2f} baseline).")

        # 3. Check for repeating patterns across recent logged doses (last 5 doses)
        recent_logs_stmt = (
            select(MedicationLog)
            .where(MedicationLog.patient_id == patient_id)
            .where(MedicationLog.status == "TAKEN")
            .order_by(desc(MedicationLog.actual_time))
            .limit(5)
        )
        recent_logs_res = await db.execute(recent_logs_stmt)
        recent_logs = recent_logs_res.scalars().all()

        # Count recent pre-dose dip correlations
        dip_count = 1 if is_wearing_off_dip else 0
        for log in recent_logs:
            if log.id != medication_log.id and log.notes and "Pre-dose risk elevation" in log.notes:
                dip_count += 1

        pattern_flagged = False
        if is_wearing_off_dip and dip_count >= 2:
            pattern_flagged = True
            # Get medication details
            med_res = await db.execute(select(Medication).where(Medication.id == medication_log.medication_id))
            med = med_res.scalar_one_or_none()
            med_name = med.name if med else "Medication"

            # Check if alert already sent today
            today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            existing_alert_res = await db.execute(
                select(Alert)
                .where(Alert.patient_id == patient_id)
                .where(Alert.type == "WEARING_OFF_DIP")
                .where(Alert.trigger_time >= today_start)
            )
            if not existing_alert_res.scalar_one_or_none():
                await notification_service.deliver_alert(
                    db=db,
                    patient_id=patient_id,
                    alert_type="WEARING_OFF_DIP",
                    severity="WARNING",
                    title="Medication Wearing-Off Pattern Detected",
                    message=(
                        f"Repeated pre-dose vocal stability dips observed across {dip_count} doses for {med_name}. "
                        f"Patient experiences acoustic symptom elevation prior to scheduled dose time. "
                        f"Doctor review of dosing interval or formulation is recommended."
                    ),
                    recipient_roles=["DOCTOR", "CAREGIVER"]
                )

        # Update log notes if dip detected
        if is_wearing_off_dip:
            medication_log.notes = " | ".join(notes_summary) if not medication_log.notes else f"{medication_log.notes} | " + " | ".join(notes_summary)
            await db.commit()

        return {
            "is_wearing_off_dip": is_wearing_off_dip,
            "pattern_flagged": pattern_flagged,
            "pre_score": pre_score,
            "post_score": post_score,
            "baseline_avg": round(baseline_avg, 3),
            "dip_count_recent": dip_count
        }

wearing_off_service = WearingOffService()
