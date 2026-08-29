import pytest
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.core.database import Base
from backend.app.models.models import User, Patient, Doctor, Medication, MedicationLog, VoiceSample, ClassificationResult
from backend.app.services.wearing_off_service import wearing_off_service

@pytest.mark.asyncio
async def test_wearing_off_correlation_detection():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        u = User(username="pat_wo_test", hashed_password="pw", full_name="Test Pat", email="two@e.com", role="PATIENT")
        doc_u = User(username="doc_wo_test", hashed_password="pw", full_name="Test Doc", email="dwo@e.com", role="DOCTOR")
        session.add_all([u, doc_u])
        await session.commit()

        d = Doctor(user_id=doc_u.id, name="Test Doc", email="dwo@e.com")
        session.add(d)
        await session.commit()

        p = Patient(user_id=u.id, name="Test Pat", doctor_id=d.id)
        session.add(p)
        await session.commit()

        med = Medication(
            patient_id=p.id, doctor_id=d.id, name="Levodopa", dosage="100mg",
            frequency="3x daily", scheduled_times_json='["13:00"]'
        )
        session.add(med)
        await session.commit()

        now = datetime.datetime.now(datetime.timezone.utc)
        for i in range(5):
            vs_base = VoiceSample(
                patient_id=p.id, recorded_by_user_id=u.id,
                timestamp=now - datetime.timedelta(days=i, hours=5),
                file_path="test.wav", status="CLASSIFIED"
            )
            session.add(vs_base)
            await session.flush()
            cr_base = ClassificationResult(
                voice_sample_id=vs_base.id, risk_score=0.40, confidence=0.90, severity_level="MILD"
            )
            session.add(cr_base)

        dose_time = now.replace(hour=13, minute=0, second=0)
        vs_predose = VoiceSample(
            patient_id=p.id, recorded_by_user_id=u.id,
            timestamp=dose_time - datetime.timedelta(minutes=30),
            file_path="test_predose.wav", status="CLASSIFIED"
        )
        session.add(vs_predose)
        await session.flush()
        cr_predose = ClassificationResult(
            voice_sample_id=vs_predose.id, risk_score=0.75, confidence=0.92, severity_level="MODERATE"
        )
        session.add(cr_predose)
        await session.commit()

        med_log = MedicationLog(
            medication_id=med.id, patient_id=p.id, logged_by_user_id=u.id,
            status="TAKEN", scheduled_time=dose_time, actual_time=dose_time
        )
        session.add(med_log)
        await session.commit()

        res = await wearing_off_service.analyze_wearing_off_correlation(session, med_log)
        assert res["is_wearing_off_dip"] is True
        assert res["pre_score"] == 0.75
        assert res["baseline_avg"] < 0.50
