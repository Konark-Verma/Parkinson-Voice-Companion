import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
MODELS_DIR = BASE_DIR / "app" / "ml" / "models"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'parkinson_companion.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "parkinson-voice-companion-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days for prototype convenience

# Gmail SMTP Configuration for Email Authentication & Verification
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "e.admin26@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "haucmgimtppmdnwz")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "e.admin26@gmail.com")

# Clinical Disclaimer text required on relevant outputs
CLINICAL_SAFETY_DISCLAIMER = (
    "DISCLAIMER: Parkinson's Voice Companion is an experimental screening/monitoring support "
    "tool and therapy aid. It is NOT a diagnostic device and does not replace evaluation by a "
    "licensed medical doctor, neurologist, or LSVT-certified speech therapist. Scores represent "
    "acoustic vocal risk indicators, not definitive medical diagnoses."
)

# Audio Quality Thresholds
MIN_AUDIO_DURATION_SEC = 2.0
MAX_AUDIO_DURATION_SEC = 30.0
MIN_SAMPLE_RATE = 16000
MIN_AUDIO_ENERGY_RMS = 0.005  # below this is considered silence / excessive distance from mic
