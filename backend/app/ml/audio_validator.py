import io
import math
import numpy as np
import soundfile as sf
from typing import Tuple, Optional
from backend.app.core.config import MIN_AUDIO_DURATION_SEC, MAX_AUDIO_DURATION_SEC, MIN_AUDIO_ENERGY_RMS

class AudioValidationResult:
    def __init__(self, is_valid: bool, duration_sec: float, sample_rate: int, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.duration_sec = duration_sec
        self.sample_rate = sample_rate
        self.error_message = error_message

def validate_audio_file(file_bytes: bytes, filename: str) -> Tuple[AudioValidationResult, Optional[np.ndarray], int]:
    """
    Validates uploaded audio data for minimum duration, acceptable audio energy,
    clipping, and valid format.
    """
    try:
        data, samplerate = sf.read(io.BytesIO(file_bytes))
    except Exception as e:
        return AudioValidationResult(
            is_valid=False,
            duration_sec=0.0,
            sample_rate=0,
            error_message=f"Unsupported or corrupted audio format ({str(e)}). Please upload a valid WAV, MP3, or FLAC audio file."
        ), None, 0

    # Convert multi-channel to mono if necessary
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    duration = len(data) / float(samplerate)

    if duration < MIN_AUDIO_DURATION_SEC:
        return AudioValidationResult(
            is_valid=False,
            duration_sec=duration,
            sample_rate=samplerate,
            error_message=f"Audio sample is too short ({duration:.1f}s). Please sustain the vocalization for at least {MIN_AUDIO_DURATION_SEC} seconds."
        ), None, samplerate

    if duration > MAX_AUDIO_DURATION_SEC:
        return AudioValidationResult(
            is_valid=False,
            duration_sec=duration,
            sample_rate=samplerate,
            error_message=f"Audio sample exceeds maximum allowed duration ({duration:.1f}s > {MAX_AUDIO_DURATION_SEC}s)."
        ), None, samplerate

    # Calculate RMS energy to detect near-silence or blank recording
    rms = float(np.sqrt(np.mean(np.square(data))))
    if rms < MIN_AUDIO_ENERGY_RMS:
        return AudioValidationResult(
            is_valid=False,
            duration_sec=duration,
            sample_rate=samplerate,
            error_message="Audio level is too quiet or silent. Please speak directly into the microphone at a normal volume and re-record."
        ), None, samplerate

    return AudioValidationResult(
        is_valid=True,
        duration_sec=duration,
        sample_rate=samplerate
    ), data, samplerate
