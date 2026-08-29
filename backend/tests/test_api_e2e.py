import pytest
import io
import soundfile as sf
import numpy as np
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.seed.seed_data import seed_database

def create_valid_test_wav(duration=2.5):
    t = np.linspace(0, duration, int(44100 * duration), endpoint=False)
    waveform = (0.5 * np.sin(2 * np.pi * 160.0 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, waveform, 44100, format='WAV')
    return buf.getvalue()

@pytest.mark.asyncio
async def test_api_e2e_flow():
    # Ensure test DB is initialized and seeded
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Health check & disclaimer
        health_res = await ac.get("/health")
        assert health_res.status_code == 200
        assert "DISCLAIMER" in health_res.json()["disclaimer"]

        # 2. Login as Doctor
        doc_login = await ac.post("/api/auth/login", json={"username": "doctor", "password": "doctor123"})
        assert doc_login.status_code == 200
        doc_token = doc_login.json()["access_token"]
        doc_headers = {"Authorization": f"Bearer {doc_token}"}

        # 3. Login as Patient
        pat_login = await ac.post("/api/auth/login", json={"username": "patient", "password": "patient123"})
        assert pat_login.status_code == 200
        pat_token = pat_login.json()["access_token"]
        pat_id = pat_login.json()["user"]["patient_id"]
        pat_headers = {"Authorization": f"Bearer {pat_token}"}

        # 4. Upload voice sample as Patient (Record Voice Sample -> Auto-includes Classify)
        wav_bytes = create_valid_test_wav(3.0)
        files = {"file": ("recording.wav", wav_bytes, "audio/wav")}
        data = {"task_type": "SUSTAINED_A", "patient_id": str(pat_id)}

        upload_res = await ac.post("/api/voice-samples/upload", files=files, data=data, headers=pat_headers)
        assert upload_res.status_code == 200
        upload_json = upload_res.json()
        assert upload_json["success"] is True
        assert "classification" in upload_json
        assert "risk_score" in upload_json["classification"]
        assert "DISCLAIMER" in upload_json["disclaimer"]

        # 5. Log Medication Intake as Patient (Auto-includes Track Wearing-Off Correlation)
        meds_res = await ac.get(f"/api/medications/patient/{pat_id}", headers=pat_headers)
        assert meds_res.status_code == 200
        med_list = meds_res.json()
        assert len(med_list) > 0
        target_med_id = med_list[0]["id"]

        log_data = {
            "medication_id": target_med_id,
            "status": "TAKEN",
            "scheduled_time": "2026-08-27T13:00:00Z",
            "notes": "E2E intake test"
        }
        med_log_res = await ac.post("/api/medications/log", json=log_data, headers=pat_headers)
        assert med_log_res.status_code == 200
        assert med_log_res.json()["status"] == "TAKEN"

        # 6. Save Therapy Session
        therapy_data = {
            "patient_id": pat_id,
            "exercise_type": "SUSTAINED_VOWEL_AH",
            "target_pitch_hz": 160.0,
            "target_volume_db": 75.0,
            "duration_sec": 8.5,
            "avg_volume_db": 76.2,
            "pitch_stability_pct": 89.4,
            "score": 92.0,
            "feedback_notes": "Great sustained loud vowel!"
        }
        th_res = await ac.post("/api/therapy/sessions", json=therapy_data, headers=pat_headers)
        assert th_res.status_code == 200
        assert th_res.json()["score"] == 92.0

        # 7. Doctor 90-Day Longitudinal Dashboard Query (<3s)
        dash_res = await ac.get(f"/api/dashboard/doctor/patient/{pat_id}?days=90", headers=doc_headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert "trend_90d" in dash_data
        assert len(dash_data["trend_90d"]) > 0
        assert "active_medications" in dash_data
        assert "wearing_off_summary" in dash_data
        assert "alerts" in dash_data
        assert "DISCLAIMER" in dash_data["disclaimer"]
