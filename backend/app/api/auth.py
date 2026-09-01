import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token, get_current_user, TokenData
from backend.app.models.models import User, Patient, Doctor, Caregiver
import random
import time
from backend.app.schemas.schemas import (
    UserLogin, UserRegister, UserResponse, TokenResponse,
    SendOTPRequest, VerifyOTPRequest, OTPResponse
)
from backend.app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory OTP storage: email -> { "code": "123456", "expires_at": timestamp }
ACTIVE_OTPS = {}

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(req: SendOTPRequest):
    email_clean = req.email.strip().lower()
    if not email_clean or "@" not in email_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address format."
        )

    # Generate 6-digit random numeric code
    code = f"{random.randint(100000, 999999)}"
    expires_at = time.time() + 600  # 10 minutes

    ACTIVE_OTPS[email_clean] = {
        "code": code,
        "expires_at": expires_at
    }

    # Dispatch email asynchronously via Gmail SMTP
    sent = await send_otp_email(
        recipient_email=email_clean,
        otp_code=code,
        username=req.username or "User"
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email via Gmail SMTP. Please check credentials or try again."
        )

    return OTPResponse(
        success=True,
        message=f"Verification code sent to {email_clean}. Please check your email inbox."
    )

@router.post("/verify-otp", response_model=OTPResponse)
async def verify_otp(req: VerifyOTPRequest):
    email_clean = req.email.strip().lower()
    record = ACTIVE_OTPS.get(email_clean)

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code was sent to this email. Please click 'Send OTP' first."
        )

    if time.time() > record["expires_at"]:
        ACTIVE_OTPS.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired (10 min limit). Please request a new code."
        )

    if record["code"] != req.otp_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check your email and try again."
        )

    # Valid OTP -> clear record
    ACTIVE_OTPS.pop(email_clean, None)
    return OTPResponse(
        success=True,
        message="Email successfully verified via SMTP OTP!"
    )

@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if username exists
    stmt = select(User).where(User.username == req.username)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken. Please choose another."
        )

    # Normalize role
    role = req.role.upper()
    if role not in ["PATIENT", "CAREGIVER", "DOCTOR"]:
        role = "PATIENT"

    # Create User
    new_user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        email=req.email,
        role=role
    )
    db.add(new_user)
    await db.flush()

    patient_id = None
    doctor_id = None
    caregiver_id = None

    if role == "PATIENT":
        # Link to default doctor (id=1) if exists
        p = Patient(
            user_id=new_user.id,
            date_of_birth=datetime.date(1955, 1, 1),
            diagnosis_year=2022,
            baseline_hnr=20.0,
            doctor_id=1
        )
        db.add(p)
        await db.flush()
        patient_id = p.id
    elif role == "DOCTOR":
        d = Doctor(
            user_id=new_user.id,
            specialty="Neurology & Movement Disorders",
            clinic_name="Parkinson Companion Virtual Center",
            phone="555-0199"
        )
        db.add(d)
        await db.flush()
        doctor_id = d.id
    elif role == "CAREGIVER":
        c = Caregiver(
            user_id=new_user.id,
            relationship="Family Caregiver"
        )
        db.add(c)
        await db.flush()
        caregiver_id = c.id
        # Link caregiver to patient 1 for demo visibility
        p_res = await db.execute(select(Patient).where(Patient.id == 1))
        p = p_res.scalar_one_or_none()
        if p:
            p.caregiver_id = c.id
            patient_id = p.id

    await db.commit()

    token_payload = {
        "user_id": new_user.id,
        "sub": new_user.username,
        "role": role,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "caregiver_id": caregiver_id
    }
    token = create_access_token(token_payload)

    user_resp = UserResponse(
        id=new_user.id,
        username=new_user.username,
        full_name=new_user.full_name,
        email=new_user.email,
        role=role,
        patient_id=patient_id,
        doctor_id=doctor_id,
        caregiver_id=caregiver_id
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == credentials.username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    patient_id = None
    doctor_id = None
    caregiver_id = None

    if user.role == "PATIENT":
        p_res = await db.execute(select(Patient).where(Patient.user_id == user.id))
        p = p_res.scalar_one_or_none()
        patient_id = p.id if p else None
    elif user.role == "DOCTOR":
        d_res = await db.execute(select(Doctor).where(Doctor.user_id == user.id))
        d = d_res.scalar_one_or_none()
        doctor_id = d.id if d else None
    elif user.role == "CAREGIVER":
        c_res = await db.execute(select(Caregiver).where(Caregiver.user_id == user.id))
        c = c_res.scalar_one_or_none()
        caregiver_id = c.id if c else None
        # Caregivers also need their linked patient ID if available
        if c:
            p_res = await db.execute(select(Patient).where(Patient.caregiver_id == c.id))
            p = p_res.first()
            if p:
                patient_id = p[0].id

    token_payload = {
        "user_id": user.id,
        "sub": user.username,
        "role": user.role,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "caregiver_id": caregiver_id
    }
    token = create_access_token(token_payload)

    user_resp = UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        patient_id=patient_id,
        doctor_id=doctor_id,
        caregiver_id=caregiver_id
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == current_user.user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        patient_id=current_user.patient_id,
        doctor_id=current_user.doctor_id,
        caregiver_id=current_user.caregiver_id
    )
