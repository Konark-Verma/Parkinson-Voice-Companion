import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.sms_service import validate_e164_phone

@pytest.mark.asyncio
async def test_e164_phone_validation():
    """Verify E.164 international phone number format validation logic."""
    assert validate_e164_phone("+919876543210") is True
    assert validate_e164_phone("+14155552671") is True
    assert validate_e164_phone("9876543210") is False  # missing leading +
    assert validate_e164_phone("invalid-phone") is False
    assert validate_e164_phone("") is False

@pytest.mark.asyncio
async def test_send_phone_otp_and_cooldown():
    """Verify phone OTP generation and 30-second resend cooldown rate limiting."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Invalid phone format test
        bad_resp = await client.post("/api/auth/send-otp", json={
            "phone": "invalid987",
            "channel": "PHONE"
        })
        assert bad_resp.status_code == 400

        # Valid phone request
        good_resp = await client.post("/api/auth/send-otp", json={
            "phone": "+919876543210",
            "channel": "PHONE"
        })
        assert good_resp.status_code == 200
        data = good_resp.json()
        assert data["success"] is True
        # Ensure security rule: OTP code must NEVER be exposed in API response!
        assert "otp_code" not in data
        assert "code" not in data

        # Immediate resend trigger -> Cooldown Rate Limit (429)
        cooldown_resp = await client.post("/api/auth/send-otp", json={
            "phone": "+919876543210",
            "channel": "PHONE"
        })
        assert cooldown_resp.status_code == 429
        assert "cooldown active" in cooldown_resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_verify_phone_otp_attempts_limit():
    """Verify OTP verification attempt counter rate limiting (max 5 tries)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Request OTP for new phone
        phone = "+14155559999"
        await client.post("/api/auth/send-otp", json={
            "phone": phone,
            "channel": "PHONE"
        })

        # Submit wrong code 4 times (attempts 1 to 4)
        for i in range(4):
            resp = await client.post("/api/auth/verify-otp", json={
                "phone": phone,
                "otp_code": "000000",
                "channel": "PHONE"
            })
            assert resp.status_code == 400
            assert "attempt(s) remaining" in resp.json()["detail"].lower()

        # 5th attempt -> Maximum attempts exceeded, invalidates OTP
        limit_resp = await client.post("/api/auth/verify-otp", json={
            "phone": phone,
            "otp_code": "000000",
            "channel": "PHONE"
        })
        assert limit_resp.status_code == 400
        assert "exceeded" in limit_resp.json()["detail"].lower()

        # 6th attempt -> No active OTP found (since key was invalidated)
        final_resp = await client.post("/api/auth/verify-otp", json={
            "phone": phone,
            "otp_code": "000000",
            "channel": "PHONE"
        })
        assert final_resp.status_code == 400
        assert "no active otp" in final_resp.json()["detail"].lower()
