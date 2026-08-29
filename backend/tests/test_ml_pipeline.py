import pytest
import numpy as np
import io
import soundfile as sf
from backend.app.ml.audio_validator import validate_audio_file
from backend.app.ml.feature_extractor import extract_acoustic_features
from backend.app.ml.classifier import classifier

def create_synthetic_sine_wav(duration_sec=3.0, sample_rate=44100, freq=160.0):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Add fundamental frequency + harmonic + slight modulation
    waveform = 0.5 * np.sin(2 * np.pi * freq * t) + 0.1 * np.sin(2 * np.pi * freq * 2 * t)
    # Add gentle envelope
    envelope = np.ones_like(waveform)
    fade_len = int(sample_rate * 0.1)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    waveform = (waveform * envelope).astype(np.float32)

    buf = io.BytesIO()
    sf.write(buf, waveform, sample_rate, format='WAV')
    return buf.getvalue()

def test_audio_validator_valid():
    wav_bytes = create_synthetic_sine_wav(duration_sec=3.0)
    result, data, sr = validate_audio_file(wav_bytes, "test.wav")
    assert result.is_valid is True
    assert result.duration_sec >= 2.9
    assert result.sample_rate == 44100
    assert data is not None

def test_audio_validator_too_short():
    wav_bytes = create_synthetic_sine_wav(duration_sec=1.0)
    result, _, _ = validate_audio_file(wav_bytes, "short.wav")
    assert result.is_valid is False
    assert "too short" in result.error_message.lower()

def test_audio_validator_silent():
    # 3 seconds of near-absolute zero
    silent_data = np.zeros(44100 * 3, dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, silent_data, 44100, format='WAV')
    result, _, _ = validate_audio_file(buf.getvalue(), "silent.wav")
    assert result.is_valid is False
    assert "quiet or silent" in result.error_message.lower()

def test_acoustic_feature_extraction():
    wav_bytes = create_synthetic_sine_wav(duration_sec=3.0, freq=165.0)
    _, audio_data, sr = validate_audio_file(wav_bytes, "test.wav")
    features = extract_acoustic_features(audio_data)

    assert "MDVP:Fo(Hz)" in features
    assert "MDVP:Jitter(%)" in features
    assert "MDVP:Shimmer" in features
    assert "HNR" in features
    assert "PPE" in features
    # Pitch should be close to 165Hz
    assert 140.0 <= features["MDVP:Fo(Hz)"] <= 190.0

def test_classifier_inference():
    wav_bytes = create_synthetic_sine_wav(duration_sec=3.0, freq=150.0)
    _, audio_data, _ = validate_audio_file(wav_bytes, "test.wav")
    features = extract_acoustic_features(audio_data)

    prediction = classifier.predict_features(features)
    assert "risk_score" in prediction
    assert 0.0 <= prediction["risk_score"] <= 1.0
    assert 0.0 <= prediction["confidence"] <= 1.0
    assert prediction["severity_level"] in ["LOW_RISK", "MILD", "MODERATE", "SEVERE"]
    assert "DISCLAIMER" in prediction["disclaimer"]
    assert prediction["inference_time_ms"] > 0
