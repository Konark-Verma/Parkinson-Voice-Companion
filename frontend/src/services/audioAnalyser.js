/**
 * Real-time Web Audio API Pitch & Decibel Volume Analyser
 * Provides low-latency (<100ms) audio metrics for Speech Therapy Coaching.
 */

export class RealtimeAudioAnalyser {
  constructor() {
    this.audioCtx = null;
    this.analyser = null;
    this.micStream = null;
    this.sourceNode = null;
    this.animationFrameId = null;
    this.isRunning = false;
    this.onMetricsCallback = null;
    this.buffer = null;
  }

  async start(onMetricsCallback) {
    this.onMetricsCallback = onMetricsCallback;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioCtx = new AudioContextClass();

    if (this.audioCtx.state === 'suspended') {
      await this.audioCtx.resume();
    }

    this.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
      },
    });

    this.sourceNode = this.audioCtx.createMediaStreamSource(this.micStream);
    this.analyser = this.audioCtx.createAnalyser();
    this.analyser.fftSize = 2048;
    this.buffer = new Float32Array(this.analyser.fftSize);

    this.sourceNode.connect(this.analyser);
    this.isRunning = true;
    this._analyzeLoop();
  }

  _analyzeLoop() {
    if (!this.isRunning) return;

    this.analyser.getFloatTimeDomainData(this.buffer);

    // 1. Calculate RMS Volume (Decibels proxy)
    let sumSquares = 0;
    for (let i = 0; i < this.buffer.length; i++) {
      sumSquares += this.buffer[i] * this.buffer[i];
    }
    const rms = Math.sqrt(sumSquares / this.buffer.length);
    // Convert RMS to calibrated dB scale (30 dB background to 95 dB loud)
    const dbValue = rms > 0.0001 ? Math.min(100, Math.max(30, Math.round(20 * Math.log10(rms) + 95))) : 30;

    // 2. Calculate Pitch (F0) using Autocorrelation
    const pitchHz = this._autoCorrelate(this.buffer, this.audioCtx.sampleRate);

    if (this.onMetricsCallback) {
      this.onMetricsCallback({
        volumeDb: dbValue,
        pitchHz: pitchHz > 0 ? Math.round(pitchHz) : null,
        isVoiced: pitchHz > 0 && dbValue >= 50,
        rawRms: rms,
      });
    }

    this.animationFrameId = requestAnimationFrame(() => this._analyzeLoop());
  }

  _autoCorrelate(buf, sampleRate) {
    const SIZE = buf.length;
    let rms = 0;
    for (let i = 0; i < SIZE; i++) {
      const val = buf[i];
      rms += val * val;
    }
    rms = Math.sqrt(rms / SIZE);
    // Low energy threshold for unvoiced sound
    if (rms < 0.01) return -1;

    let r1 = 0, r2 = SIZE - 1;
    const thres = 0.2;
    for (let i = 0; i < SIZE / 2; i++) {
      if (Math.abs(buf[i]) < thres) {
        r1 = i;
        break;
      }
    }
    for (let i = 1; i < SIZE / 2; i++) {
      if (Math.abs(buf[SIZE - i]) < thres) {
        r2 = SIZE - i;
        break;
      }
    }

    buf = buf.slice(r1, r2);
    const c = new Array(buf.length).fill(0);
    for (let i = 0; i < buf.length; i++) {
      for (let j = 0; j < buf.length - i; j++) {
        c[i] = c[i] + buf[j] * buf[j + i];
      }
    }

    let d = 0;
    while (c[d] > c[d + 1]) d++;
    let maxval = -1, maxpos = -1;
    for (let i = d; i < buf.length; i++) {
      if (c[i] > maxval) {
        maxval = c[i];
        maxpos = i;
      }
    }
    let T0 = maxpos;

    // Pitch range filter (75 Hz to 500 Hz standard human voice range)
    const pitch = sampleRate / T0;
    if (pitch >= 75 && pitch <= 500) {
      return pitch;
    }
    return -1;
  }

  stop() {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.micStream) {
      this.micStream.getTracks().forEach((track) => track.stop());
      this.micStream = null;
    }
    if (this.audioCtx) {
      this.audioCtx.close();
      this.audioCtx = null;
    }
  }
}
