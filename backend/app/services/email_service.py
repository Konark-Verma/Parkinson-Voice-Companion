import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core import config

def _send_sync_email(to_email: str, subject: str, html_body: str) -> bool:
    """Synchronous SMTP email dispatcher using Gmail App Password credentials."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Parkinson Voice Companion <{config.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=10)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USERNAME, [to_email], msg.as_string())
        server.quit()
        return True
    except Exception as err:
        print(f"[SMTP-ERROR] Failed to send email to {to_email}: {err}")
        return False

async def send_otp_email(recipient_email: str, otp_code: str, username: str = "User") -> bool:
    """Asynchronous wrapper for sending OTP verification codes via Gmail SMTP."""
    subject = f"{otp_code} is your Parkinson Voice Companion Verification Code"
    
    html_body = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; padding: 24px; color: #0f172a;">
        <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          
          <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; background-color: #2563eb; color: #ffffff; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; font-weight: bold; font-size: 20px;">
              PV
            </div>
            <h2 style="color: #0f172a; margin-top: 12px; margin-bottom: 4px; font-size: 20px;">Parkinson's Voice Companion</h2>
            <p style="color: #64748b; font-size: 13px; margin: 0;">Email Authentication & Account Verification</p>
          </div>

          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />

          <p style="font-size: 14px; color: #334155;">Hello <strong>{username}</strong>,</p>
          <p style="font-size: 14px; color: #334155;">Use the 6-digit verification code below to authenticate your account and verify your email address:</p>

          <div style="text-align: center; margin: 28px 0;">
            <span style="font-family: monospace; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #2563eb; background-color: #eff6ff; border: 1px border #bfdbfe; padding: 12px 24px; border-radius: 12px; display: inline-block;">
              {otp_code}
            </span>
            <p style="font-size: 12px; color: #94a3b8; margin-top: 8px;">This code will expire in <strong>10 minutes</strong>.</p>
          </div>

          <div style="background-color: #f1f5f9; border-radius: 12px; padding: 16px; margin-top: 24px;">
            <p style="font-size: 12px; color: #475569; margin: 0; line-height: 1.5;">
              <strong>Security Note:</strong> If you did not request this email verification, please ignore this email. Do not share your OTP code with anyone.
            </p>
          </div>

          <div style="margin-top: 32px; pt: 16px; border-top: 1px solid #f1f5f9; text-align: center; font-size: 11px; color: #94a3b8;">
            Parkinson's Voice Companion • SMTP Authentication Service • {config.SMTP_FROM_EMAIL}
          </div>

        </div>
      </body>
    </html>
    """
    
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_sync_email, recipient_email, subject, html_body)

async def send_alert_notification_email(recipient_email: str, alert_title: str, alert_message: str, severity: str, patient_name: str = "Robert Jenkins") -> bool:
    """Sends instant alert notification emails to caregivers and doctors via Gmail SMTP."""
    subject = f"[{severity} ALERT] Parkinson Companion - {patient_name}"
    
    badge_color = "#dc2626" if severity == "URGENT" else "#d97706"
    
    html_body = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; padding: 24px; color: #0f172a;">
        <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0;">
          
          <div style="margin-bottom: 20px;">
            <span style="background-color: {badge_color}; color: #ffffff; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 20px; text-transform: uppercase;">
              {severity} ALERT
            </span>
            <h2 style="color: #0f172a; margin-top: 12px; font-size: 18px;">{alert_title}</h2>
          </div>

          <div style="background-color: #f8fafc; border-left: 4px solid {badge_color}; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p style="font-size: 14px; color: #334155; margin: 0;"><strong>Patient:</strong> {patient_name}</p>
            <p style="font-size: 14px; color: #334155; margin: 6px 0 0 0;">{alert_message}</p>
          </div>

          <p style="font-size: 12px; color: #64748b;">Please log in to the Parkinson Voice Companion dashboard to review detailed acoustic trend data.</p>
        </div>
      </body>
    </html>
    """
    
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _send_sync_email, recipient_email, subject, html_body)
