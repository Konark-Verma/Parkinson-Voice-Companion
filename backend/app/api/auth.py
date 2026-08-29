from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token, get_current_user, TokenData
from backend.app.models.models import User, Patient, Doctor, Caregiver
from backend.app.schemas.schemas import UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
