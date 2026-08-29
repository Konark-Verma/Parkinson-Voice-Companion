import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship as orm_relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(20), nullable=False)  # "PATIENT", "CAREGIVER", "DOCTOR", "ADMIN"
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    doctor_profile = orm_relationship("Doctor", back_populates="user", uselist=False)
    caregiver_profile = orm_relationship("Caregiver", back_populates="user", uselist=False)
    patient_profile = orm_relationship("Patient", back_populates="user", uselist=False)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    specialty = Column(String(100), default="Neurology / Movement Disorders")
    clinic_name = Column(String(150), default="Movement Disorders Center")
    phone = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = orm_relationship("User", back_populates="doctor_profile")
    patients = orm_relationship("Patient", back_populates="doctor")
    medications_prescribed = orm_relationship("Medication", back_populates="prescribing_doctor")

class Caregiver(Base):
    __tablename__ = "caregivers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    relationship_type = Column(String(50), default="Family Member")  # e.g., Spouse, Child, Primary Aide
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = orm_relationship("User", back_populates="caregiver_profile")
    patients = orm_relationship("Patient", back_populates="caregiver")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    date_of_birth = Column(String(20), nullable=True)  # YYYY-MM-DD
    gender = Column(String(20), nullable=True)
    diagnosis_year = Column(Integer, nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    caregiver_id = Column(Integer, ForeignKey("caregivers.id"), nullable=True)
    baseline_hnr = Column(Float, default=20.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = orm_relationship("User", back_populates="patient_profile")
    doctor = orm_relationship("Doctor", back_populates="patients")
    caregiver = orm_relationship("Caregiver", back_populates="patients")
    voice_samples = orm_relationship("VoiceSample", back_populates="patient", cascade="all, delete-orphan")
    medications = orm_relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    medication_logs = orm_relationship("MedicationLog", back_populates="patient", cascade="all, delete-orphan")
    therapy_sessions = orm_relationship("TherapySession", back_populates="patient", cascade="all, delete-orphan")
    alerts = orm_relationship("Alert", back_populates="patient", cascade="all, delete-orphan")

class VoiceSample(Base):
    __tablename__ = "voice_samples"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    task_type = Column(String(50), default="SUSTAINED_A")  # SUSTAINED_A, PHRASE_READING, FREE_SPEECH
    file_path = Column(String(255), nullable=False)
    audio_duration_sec = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=44100)
    status = Column(String(30), default="PENDING")  # PENDING, PROCESSING, CLASSIFIED, REJECTED_QUALITY, FAILED
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    patient = orm_relationship("Patient", back_populates="voice_samples")
    extracted_features = orm_relationship("ExtractedFeatures", back_populates="voice_sample", uselist=False, cascade="all, delete-orphan")
    classification_result = orm_relationship("ClassificationResult", back_populates="voice_sample", uselist=False, cascade="all, delete-orphan")

class ExtractedFeatures(Base):
    __tablename__ = "extracted_features"

    id = Column(Integer, primary_key=True, index=True)
    voice_sample_id = Column(Integer, ForeignKey("voice_samples.id"), unique=True, nullable=False)
    jitter_local = Column(Float, nullable=True)  # MDVP:Jitter(%)
    jitter_rap = Column(Float, nullable=True)    # MDVP:RAP
    jitter_ppq5 = Column(Float, nullable=True)   # MDVP:PPQ
    shimmer_local = Column(Float, nullable=True) # MDVP:Shimmer(%)
    shimmer_apq3 = Column(Float, nullable=True)  # MDVP:APQ3
    shimmer_apq5 = Column(Float, nullable=True)  # MDVP:APQ5
    hnr = Column(Float, nullable=True)           # Harmonics-to-Noise Ratio (dB)
    f0_mean = Column(Float, nullable=True)       # Mean fundamental frequency (Hz)
    f0_std = Column(Float, nullable=True)        # Pitch standard deviation
    f0_min = Column(Float, nullable=True)        # Pitch min
    f0_max = Column(Float, nullable=True)        # Pitch max
    ppe = Column(Float, nullable=True)           # Pitch Period Entropy
    spread1 = Column(Float, nullable=True)       # Nonlinear measures
    spread2 = Column(Float, nullable=True)
    raw_features_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    voice_sample = orm_relationship("VoiceSample", back_populates="extracted_features")

class ClassificationResult(Base):
    __tablename__ = "classification_results"

    id = Column(Integer, primary_key=True, index=True)
    voice_sample_id = Column(Integer, ForeignKey("voice_samples.id"), unique=True, nullable=False)
    risk_score = Column(Float, nullable=False)       # 0.0 - 1.0
    confidence = Column(Float, nullable=False)       # 0.0 - 1.0
    severity_level = Column(String(30), nullable=False)  # LOW_RISK, MILD, MODERATE, SEVERE
    model_version = Column(String(50), default="rf-gb-v1.0.0-oxford")
    inference_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    voice_sample = orm_relationship("VoiceSample", back_populates="classification_result")

class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    name = Column(String(100), nullable=False)          # e.g., Levodopa / Carbidopa
    dosage = Column(String(50), nullable=False)        # e.g., 100/25 mg
    frequency = Column(String(50), nullable=False)     # e.g., 3x daily
    scheduled_times_json = Column(String(255), default='["08:00", "13:00", "18:00"]') # JSON array of HH:MM
    instructions = Column(String(255), nullable=True)  # e.g., Take 30 mins before meals
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    patient = orm_relationship("Patient", back_populates="medications")
    prescribing_doctor = orm_relationship("Doctor", back_populates="medications_prescribed")
    logs = orm_relationship("MedicationLog", back_populates="medication", cascade="all, delete-orphan")

class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    logged_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), nullable=False)  # TAKEN, SKIPPED, DELAYED
    scheduled_time = Column(DateTime, nullable=False)
    actual_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    medication = orm_relationship("Medication", back_populates="logs")
    patient = orm_relationship("Patient", back_populates="medication_logs")

class TherapySession(Base):
    __tablename__ = "therapy_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    exercise_type = Column(String(50), nullable=False)  # SUSTAINED_VOWEL_AH, PITCH_GLIDE, LOUD_PHRASE
    target_pitch_hz = Column(Float, default=160.0)
    target_volume_db = Column(Float, default=75.0)
    duration_sec = Column(Float, nullable=False)
    avg_volume_db = Column(Float, nullable=False)
    pitch_stability_pct = Column(Float, nullable=False)
    score = Column(Float, nullable=False)  # 0 - 100
    feedback_notes = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    patient = orm_relationship("Patient", back_populates="therapy_sessions")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    type = Column(String(50), nullable=False)        # DECLINE_GRADUAL, DECLINE_SUDDEN, WEARING_OFF_DIP, MEDICATION_MISSED, AUDIO_QUALITY
    severity = Column(String(30), nullable=False)    # INFORMATIONAL, WARNING, URGENT
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    trigger_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    status = Column(String(30), default="ACTIVE")    # ACTIVE, ACKNOWLEDGED, RESOLVED
    recipient_roles_json = Column(String(255), default='["PATIENT", "CAREGIVER", "DOCTOR"]')
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    patient = orm_relationship("Patient", back_populates="alerts")
