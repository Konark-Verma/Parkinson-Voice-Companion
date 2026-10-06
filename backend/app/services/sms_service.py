import os
import re
import asyncio
import logging
from backend.app.core import config

logger = logging.getLogger("sms_service")

# E.164 International Phone Number Regex Pattern (e.g., +919876543210, +14155552671: 7 to 15 digits total)
E164_PHONE_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")

def format_e164_phone(phone_number: str) -> str:
    """Formats phone number into standard E.164 international format (+91 for 10-digit India numbers)."""
    if not phone_number or not isinstance(phone_number, str):
        return ""
    clean = re.sub(r"[^\d+]", "", phone_number.strip())
    if not clean:
        return ""
    if not clean.startswith("+"):
        if len(clean) == 10:
            clean = "+91" + clean
        elif len(clean) == 11 and clean.startswith("0"):
            clean = "+91" + clean[1:]
        else:
            clean = "+" + clean
    return clean

def validate_e164_phone(phone_number: str) -> bool:
    """Validates international E.164 phone number format directly."""
    if not phone_number or not isinstance(phone_number, str):
        return False
    return bool(E164_PHONE_REGEX.match(phone_number.strip()))

def _send_twilio_sms_sync(to_phone: str, message_body: str) -> bool:
    """Synchronous Twilio SMS dispatcher with dev fallback."""
    account_sid = config.TWILIO_ACCOUNT_SID
    auth_token = config.TWILIO_AUTH_TOKEN
    from_phone = config.TWILIO_PHONE_NUMBER

    if account_sid and auth_token and from_phone:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )
            logger.info(f"[TWILIO-SMS] Message sent to {to_phone}. SID: {message.sid}")
            return True
        except Exception as err:
            logger.error(f"[TWILIO-ERROR] Failed to send SMS via Twilio to {to_phone}: {err}")
            return False
    else:
        # Development / Testing Mode Fallback
        logger.info(f"[SMS-DEV-MODE] Twilio keys not set in env. Simulated SMS to {to_phone}: '{message_body}'")
        print(f"\n[SMS-SIMULATOR] Outbound SMS to {to_phone}: {message_body}\n")
        return True

async def send_phone_otp_sms(to_phone: str, otp_code: str) -> bool:
    """Asynchronous wrapper for dispatching phone OTP SMS."""
    if not validate_e164_phone(to_phone):
        logger.warning(f"[SMS-INVALID-PHONE] Rejected non-E.164 phone number: {to_phone}")
        return False

    message_body = (
        f"{otp_code} is your Parkinson Voice Companion OTP code. "
        f"Valid for 5 minutes. Do not share this code with anyone."
    )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_twilio_sms_sync, to_phone, message_body)
