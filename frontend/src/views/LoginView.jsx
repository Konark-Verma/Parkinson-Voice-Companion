import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import {
  Activity, ShieldCheck, Stethoscope, HeartHandshake, User,
  Lock, Mail, Phone, UserPlus, LogIn, Sparkles, ArrowRight, ShieldAlert,
  CheckCircle2, Send, RefreshCw, KeyRound, Clock
} from 'lucide-react';

export default function LoginView() {
  const { loginUser, registerUser, switchRole } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [authChannel, setAuthChannel] = useState('EMAIL'); // 'EMAIL' | 'PHONE'
  
  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  
  // Register Form State
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('+91');
  const [regRole, setRegRole] = useState('PATIENT');

  // OTP Verification & Cooldown State
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpMessage, setOtpMessage] = useState(null);

  // 30-Second Resend Cooldown Timer
  const [cooldown, setCooldown] = useState(0);
  const cooldownRef = useRef(null);

  useEffect(() => {
    if (cooldown > 0) {
      cooldownRef.current = setTimeout(() => setCooldown(cooldown - 1), 1000);
    } else {
      clearTimeout(cooldownRef.current);
    }
    return () => clearTimeout(cooldownRef.current);
  }, [cooldown]);

  const handleSendOTP = async () => {
    setError(null);
    setOtpMessage(null);

    const target = authChannel === 'PHONE' ? regPhone.trim() : regEmail.trim();
    if (!target) {
      setError(authChannel === 'PHONE' ? 'Please enter a valid phone number in E.164 format (+91...)' : 'Please enter a valid email address.');
      return;
    }

    if (authChannel === 'PHONE' && !target.startsWith('+')) {
      setError('Phone number must start with + and country code (e.g. +919876543210 for India).');
      return;
    }

    setOtpSending(true);

    try {
      const res = await api.sendOTP(target, regFullName || regUsername || 'User', authChannel);
      setOtpSent(true);
      setOtpMessage(res.message);
      setCooldown(30); // 30s resend cooldown timer
    } catch (err) {
      setError(err.message || 'Failed to send OTP. Please try again.');
    } finally {
      setOtpSending(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otpCode || otpCode.length < 5) {
      setError('Please enter the 6-digit verification code.');
      return;
    }
    setError(null);
    setOtpMessage(null);
    setOtpVerifying(true);

    const target = authChannel === 'PHONE' ? regPhone.trim() : regEmail.trim();

    try {
      const res = await api.verifyOTP(target, otpCode, authChannel);
      setOtpVerified(true);
      setOtpMessage(res.message);
      if (res.token) {
        // If phone verification returned session token, trigger app refresh
        window.location.reload();
      }
    } catch (err) {
      setError(err.message || 'Verification code invalid or expired.');
    } finally {
      setOtpVerifying(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await loginUser(loginUsername, loginPassword);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!otpVerified) {
      setError(`Please verify your ${authChannel === 'PHONE' ? 'phone number via SMS' : 'email via Gmail SMTP'} OTP code first.`);
      return;
    }

    setSubmitting(true);
    try {
      await registerUser({
        username: regUsername,
        password: regPassword,
        full_name: regFullName,
        email: regEmail || `${regUsername}@companion.local`,
        role: regRole,
        otp_code: otpCode,
      });
    } catch (err) {
      setError(err.message || 'Registration failed. Please check input fields.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-6 px-4 sm:px-6">
      <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden">
        
        {/* Left Side: Brand & Clinical Overview */}
        <div className="lg:col-span-5 bg-gradient-to-br from-slate-900 via-slate-800 to-blue-950 p-8 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-teal-500/20 rounded-full blur-3xl" />
          
          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="font-extrabold text-xl leading-tight">Parkinson's</h1>
                <p className="text-xs text-blue-400 font-semibold uppercase tracking-wider">Voice Companion</p>
              </div>
            </div>

            <h2 className="text-2xl font-bold text-slate-100 mt-6 leading-snug">
              Integrated Monitoring, Speech Therapy & Clinical Alerts
            </h2>
            <p className="text-slate-300 text-sm mt-3 leading-relaxed">
              Non-invasive acoustic vocal biomarkers tracking Parkinson's symptom severity, levodopa wearing-off correlation, and live LSVT-style speech coaching.
            </p>

            <div className="mt-8 space-y-3">
              <div className="flex items-start space-x-3 bg-white/5 border border-white/10 p-3.5 rounded-2xl backdrop-blur-sm">
                <ShieldCheck className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-slate-200">
                  <strong className="block text-white font-semibold">Dual Email & Phone OTP Auth</strong>
                  Supports Gmail SMTP Email OTP and Twilio SMS Phone OTP with E.164 validation & 30s resend cooldown.
                </div>
              </div>

              <div className="flex items-start space-x-3 bg-white/5 border border-white/10 p-3.5 rounded-2xl backdrop-blur-sm">
                <Sparkles className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-slate-200">
                  <strong className="block text-white font-semibold">Oxford ML Ensemble v2.0.0</strong>
                  81.09% CV accuracy trained on 3,141 authentic clinical voice recordings.
                </div>
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-8 pt-4 border-t border-slate-700/60 text-xs text-slate-400 flex items-center justify-between">
            <span>Dual Auth System</span>
            <span className="text-blue-400 font-medium">SMTP + Twilio SMS</span>
          </div>
        </div>

        {/* Right Side: Auth Forms */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-center">
          
          {/* Mode Switcher Tabs */}
          <div className="flex items-center justify-center p-1.5 bg-slate-100 rounded-2xl mb-6">
            <button
              onClick={() => { setMode('login'); setError(null); setOtpMessage(null); }}
              className={`flex-1 py-2.5 text-sm font-bold rounded-xl transition flex items-center justify-center space-x-2 ${
                mode === 'login'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <LogIn className="w-4 h-4" />
              <span>Log In</span>
            </button>
            <button
              onClick={() => { setMode('register'); setError(null); setOtpMessage(null); }}
              className={`flex-1 py-2.5 text-sm font-bold rounded-xl transition flex items-center justify-center space-x-2 ${
                mode === 'register'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              <span>Create Account</span>
            </button>
          </div>

          {error && (
            <div className="mb-5 bg-red-50 border border-red-200 text-red-700 text-xs sm:text-sm p-3.5 rounded-2xl flex items-start space-x-2">
              <ShieldAlert className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {otpMessage && (
            <div className="mb-5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs sm:text-sm p-3.5 rounded-2xl flex items-start space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>{otpMessage}</span>
            </div>
          )}

          {/* LOGIN FORM */}
          {mode === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Username
                </label>
                <div className="relative">
                  <User className="w-5 h-5 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-5 h-5 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full pl-11 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2 mt-2"
              >
                {submitting ? (
                  <span>Signing In...</span>
                ) : (
                  <>
                    <span>Sign In to Companion</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* REGISTER FORM WITH DUAL EMAIL / PHONE OTP SELECTION */
            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              
              {/* Account Role Selector */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Select Your Account Role
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setRegRole('PATIENT')}
                    className={`py-2 px-2 rounded-xl text-xs font-bold border transition flex flex-col items-center justify-center space-y-1 ${
                      regRole === 'PATIENT'
                        ? 'bg-blue-50 border-blue-600 text-blue-700'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <User className="w-4 h-4" />
                    <span>Patient</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRegRole('CAREGIVER')}
                    className={`py-2 px-2 rounded-xl text-xs font-bold border transition flex flex-col items-center justify-center space-y-1 ${
                      regRole === 'CAREGIVER'
                        ? 'bg-blue-50 border-blue-600 text-blue-700'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <HeartHandshake className="w-4 h-4" />
                    <span>Caregiver</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setRegRole('DOCTOR')}
                    className={`py-2 px-2 rounded-xl text-xs font-bold border transition flex flex-col items-center justify-center space-y-1 ${
                      regRole === 'DOCTOR'
                        ? 'bg-blue-50 border-blue-600 text-blue-700'
                        : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    <Stethoscope className="w-4 h-4" />
                    <span>Doctor</span>
                  </button>
                </div>
              </div>

              {/* Full Name & Username */}
              <div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      placeholder="Full name"
                      className="w-full px-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Username</label>
                    <input
                      type="text"
                      required
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="Username"
                      className="w-full px-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                    />
                  </div>
                </div>
              </div>

              {/* Channel Option Selector (Email OTP vs Phone SMS OTP) */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Choose Verification Channel
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthChannel('EMAIL');
                      setOtpSent(false);
                      setOtpVerified(false);
                      setError(null);
                    }}
                    className={`py-1.5 text-xs font-bold rounded-lg transition flex items-center justify-center space-x-1.5 ${
                      authChannel === 'EMAIL'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Mail className="w-3.5 h-3.5" />
                    <span>Gmail Email OTP</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setAuthChannel('PHONE');
                      setOtpSent(false);
                      setOtpVerified(false);
                      setError(null);
                    }}
                    className={`py-1.5 text-xs font-bold rounded-lg transition flex items-center justify-center space-x-1.5 ${
                      authChannel === 'PHONE'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Phone className="w-3.5 h-3.5" />
                    <span>SMS Phone OTP</span>
                  </button>
                </div>
              </div>

              {/* Target Input Field (Email or Phone Number) */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  {authChannel === 'PHONE' ? 'Phone Number (E.164 format: +91...)' : 'Email Address'}
                </label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    {authChannel === 'PHONE' ? (
                      <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    ) : (
                      <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    )}
                    <input
                      type={authChannel === 'PHONE' ? 'tel' : 'email'}
                      required
                      disabled={otpVerified}
                      value={authChannel === 'PHONE' ? regPhone : regEmail}
                      onChange={(e) => {
                        if (authChannel === 'PHONE') {
                          setRegPhone(e.target.value);
                        } else {
                          setRegEmail(e.target.value);
                        }
                        setOtpSent(false);
                        setOtpVerified(false);
                      }}
                      placeholder={authChannel === 'PHONE' ? '+919876543210' : 'name@example.com'}
                      className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900 disabled:opacity-60"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={otpSending || otpVerified || cooldown > 0}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 disabled:opacity-50 flex-shrink-0 min-w-[110px] justify-center"
                  >
                    {otpSending ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : otpVerified ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : cooldown > 0 ? (
                      <Clock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                    ) : (
                      <Send className="w-3.5 h-3.5 text-blue-400" />
                    )}
                    <span>
                      {otpVerified
                        ? 'Verified'
                        : cooldown > 0
                        ? `Wait ${cooldown}s`
                        : otpSent
                        ? 'Resend'
                        : 'Send OTP'}
                    </span>
                  </button>
                </div>
              </div>

              {/* Enter & Verify 6-digit OTP Code */}
              {otpSent && !otpVerified && (
                <div className="bg-blue-50 border border-blue-200 p-3 rounded-2xl">
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs font-bold text-blue-950 uppercase tracking-wider flex items-center gap-1">
                      <KeyRound className="w-3.5 h-3.5 text-blue-600" />
                      <span>Enter 6-Digit Code</span>
                    </label>
                    <span className="text-[10px] text-blue-700 font-semibold">5-min expiry</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      placeholder="e.g. 123456"
                      className="flex-1 px-3.5 py-1.5 bg-white border border-blue-300 rounded-xl text-sm font-mono tracking-widest text-center font-bold text-blue-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyOTP}
                      disabled={otpVerifying || otpCode.length < 5}
                      className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition shadow-sm disabled:opacity-50"
                    >
                      {otpVerifying ? 'Verifying...' : 'Verify Code'}
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Create strong password"
                  className="w-full px-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2 mt-2 disabled:opacity-50"
              >
                {submitting ? (
                  <span>Registering...</span>
                ) : (
                  <>
                    <span>Create Account & Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          )}

          {/* Quick Demo Instant Logins */}
          <div className="mt-5 pt-4 border-t border-slate-100">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2.5">
              1-Click Instant Demo Access
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => switchRole('PATIENT')}
                className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
              >
                <User className="w-3.5 h-3.5 text-blue-600" />
                <span>Patient</span>
              </button>
              <button
                type="button"
                onClick={() => switchRole('CAREGIVER')}
                className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
              >
                <HeartHandshake className="w-3.5 h-3.5 text-rose-500" />
                <span>Caregiver</span>
              </button>
              <button
                type="button"
                onClick={() => switchRole('DOCTOR')}
                className="py-1.5 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
              >
                <Stethoscope className="w-3.5 h-3.5 text-emerald-600" />
                <span>Doctor</span>
              </button>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
