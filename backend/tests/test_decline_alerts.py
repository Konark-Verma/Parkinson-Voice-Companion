import pytest
import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.core.database import Base
from backend.app.models.models import User, Patient, Doctor, VoiceSample, ClassificationResult
from backend.app.services.decline_detection_service import decline_detection_service

@pytest.mark.asyncio
async def test_sudden_decline_detection():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        u = User(username="pat_sudden_t", hashed_password="pw", full_name="Pat Sudden", email="st@e.com", role="PATIENT")
        doc_u = User(username="doc_sudden_t", hashed_password="pw", full_name="Doc Sudden", email="dst@e.com", role="DOCTOR")
        session.add_all([u, doc_u])
        await session.commit()

        d = Doctor(user_id=doc_u.id, name="Doc Sudden", email="dst@e.com")
        session.add(d)
        await session.commit()

        p = Patient(user_id=u.id, name="Pat Sudden", doctor_id=d.id)
        session.add(p)
        await session.commit()

        now = datetime.datetime.now(datetime.timezone.utc)
        for i in range(5, 0, -1):
            vs = VoiceSample(
                patient_id=p.id, recorded_by_user_id=u.id,
                timestamp=now - datetime.timedelta(days=i),
                file_path="sample.wav", status="CLASSIFIED"
            )
            session.add(vs)
            await session.flush()
            cr = ClassificationResult(
                voice_sample_id=vs.id, risk_score=0.30, confidence=0.90, severity_level="LOW_RISK"
            )
            session.add(cr)

        # Sudden spike: jumps to 0.78
        vs_spike = VoiceSample(
            patient_id=p.id, recorded_by_user_id=u.id,
            timestamp=now, file_path="spike.wav", status="CLASSIFIED"
        )
        session.add(vs_spike)
        await session.flush()
        cr_spike = ClassificationResult(
            voice_sample_id=vs_spike.id, risk_score=0.78, confidence=0.95, severity_level="MODERATE"
        )
        session.add(cr_spike)
        await session.commit()

        alert = await decline_detection_service.evaluate_change_point(
            db=session,
            patient_id=p.id,
            latest_sample_id=vs_spike.id,
            latest_risk_score=0.78
        )

        assert alert is not None
        assert alert.type == "DECLINE_SUDDEN"
        assert alert.severity == "URGENT"
        assert "Sudden Vocal Stability Shift" in alert.title
