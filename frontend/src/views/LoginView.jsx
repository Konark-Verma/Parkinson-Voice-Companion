import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Activity, ShieldCheck, Stethoscope, HeartHandshake, User,
  Lock, Mail, UserPlus, LogIn, Sparkles, ArrowRight, ShieldAlert
} from 'lucide-react';

export default function LoginView() {
  const { loginUser, registerUser, switchRole } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  
  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  
  // Register Form State
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regFullName, setRegFullName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regRole, setRegRole] = useState('PATIENT');

  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

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
    setSubmitting(true);
    try {
      await registerUser({
        username: regUsername,
        password: regPassword,
        full_name: regFullName,
        email: regEmail,
        role: regRole,
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
                  <strong className="block text-white font-semibold">Oxford Voice ML Engine</strong>
                  81.09% CV accuracy ensemble trained on 3,141 authentic clinical voice samples.
                </div>
              </div>

              <div className="flex items-start space-x-3 bg-white/5 border border-white/10 p-3.5 rounded-2xl backdrop-blur-sm">
                <Sparkles className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-slate-200">
                  <strong className="block text-white font-semibold">Sub-100ms Biofeedback</strong>
                  Real-time Web Audio volume dB and pitch stability tracking during exercises.
                </div>
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-8 pt-4 border-t border-slate-700/60 text-xs text-slate-400 flex items-center justify-between">
            <span>Research & Clinical Aid v1.0</span>
            <span className="text-blue-400 font-medium">FastAPI + React</span>
          </div>
        </div>

        {/* Right Side: Auth Forms */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-center">
          
          {/* Mode Switcher Tabs */}
          <div className="flex items-center justify-center p-1.5 bg-slate-100 rounded-2xl mb-6">
            <button
              onClick={() => { setMode('login'); setError(null); }}
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
              onClick={() => { setMode('register'); setError(null); }}
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
            /* REGISTER FORM */
            <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
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

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  placeholder="e.g. Robert Jenkins"
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    required
                    value={regUsername}
                    onChange={(e) => setRegUsername(e.target.value)}
                    placeholder="Choose username"
                    className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                  />
                </div>
              </div>

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
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2 mt-2"
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
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider text-center mb-3">
              1-Click Demo Accounts
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => switchRole('PATIENT')}
                className="py-2 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
              >
                <User className="w-3.5 h-3.5 text-blue-600" />
                <span>Patient</span>
              </button>
              <button
                type="button"
                onClick={() => switchRole('CAREGIVER')}
                className="py-2 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
              >
                <HeartHandshake className="w-3.5 h-3.5 text-rose-500" />
                <span>Caregiver</span>
              </button>
              <button
                type="button"
                onClick={() => switchRole('DOCTOR')}
                className="py-2 px-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5"
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
