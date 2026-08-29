import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import ClinicalDisclaimer from '../components/ClinicalDisclaimer';
import VoiceRecorder from '../components/VoiceRecorder';
import TherapyCoach from '../components/TherapyCoach';
import MedicationLogger from '../components/MedicationLogger';
import AlertsList from '../components/AlertsList';
import { Mic, Zap, Pill, Bell, History, Award, CheckCircle2, Heart } from 'lucide-react';

export default function PatientView() {
  const { user } = useAuth();
  const patientId = user?.patient_id || 1;

  const [activeTab, setActiveTab] = useState('record'); // 'record', 'therapy', 'meds', 'alerts', 'history'
  const [patientData, setPatientData] = useState(null);
  const [recentSamples, setRecentSamples] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [therapySessions, setTherapySessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatientOverview();
  }, [patientId]);

  const loadPatientOverview = async () => {
    try {
      setLoading(false);
      const [pat, samples, alts, th] = await Promise.all([
        api.getPatient(patientId).catch(() => null),
        api.getPatientVoiceSamples(patientId).catch(() => []),
        api.getAlerts({ patient_id: patientId }).catch(() => []),
        api.getTherapyHistory(patientId).catch(() => []),
      ]);
      setPatientData(pat);
      setRecentSamples(samples || []);
      setAlerts(alts || []);
      setTherapySessions(th || []);
    } catch (err) {
      console.error('Failed to load patient overview:', err);
    }
  };

  const navButtons = [
    { id: 'record', label: '1. Voice Check', icon: Mic, color: 'bg-blue-700 hover:bg-blue-800' },
    { id: 'therapy', label: '2. Speech Coach', icon: Zap, color: 'bg-indigo-700 hover:bg-indigo-800' },
    { id: 'meds', label: '3. Log Medication', icon: Pill, color: 'bg-emerald-700 hover:bg-emerald-800' },
    { id: 'alerts', label: '4. View Alerts', icon: Bell, badge: alerts.filter(a => a.status === 'ACTIVE').length, color: 'bg-amber-700 hover:bg-amber-800' },
    { id: 'history', label: '5. My Progress', icon: History, color: 'bg-slate-700 hover:bg-slate-800' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      {/* Prominent Clinical Disclaimer */}
      <ClinicalDisclaimer />

      {/* Welcome & Patient Status Bar */}
      <div className="bg-gradient-to-r from-blue-900 to-slate-900 text-white rounded-2xl p-6 shadow-md flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-blue-300 font-semibold">
            Patient Companion Dashboard
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-0.5">
            Hello, {user?.full_name || 'Robert Jenkins'}
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            Tap any large action below to record your voice, do your loud speech exercise, or log medication.
          </p>
        </div>

        {/* Quick Voice Risk Summary Badge */}
        {recentSamples.length > 0 && recentSamples[0].classification && (
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 p-3.5 rounded-xl text-center min-w-[150px]">
            <span className="text-[11px] text-blue-200 uppercase font-semibold block">
              Latest Risk Indicator
            </span>
            <div className="text-2xl font-black text-white mt-0.5">
              {(recentSamples[0].classification.risk_score * 100).toFixed(1)}%
            </div>
            <span className="text-xs text-blue-100 font-medium">
              {recentSamples[0].classification.severity_level}
            </span>
          </div>
        )}
      </div>

      {/* Large-Touch Accessible Navigation Bar (≤2 Taps Core Flow) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        {navButtons.map((btn) => {
          const Icon = btn.icon;
          const isSelected = activeTab === btn.id;
          return (
            <button
              key={btn.id}
              onClick={() => setActiveTab(btn.id)}
              className={`p-3.5 sm:p-4 rounded-xl flex flex-col items-center justify-center text-center font-bold transition-all shadow-sm min-h-[72px] relative ${
                isSelected
                  ? 'bg-blue-600 text-white ring-4 ring-blue-300 scale-102 shadow-lg shadow-blue-600/30'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
              }`}
              aria-pressed={isSelected}
            >
              {btn.badge > 0 && (
                <span className="absolute top-1.5 right-2 bg-red-600 text-white text-xs px-1.5 py-0.5 rounded-full font-extrabold animate-pulse">
                  {btn.badge}
                </span>
              )}
              <Icon className={`w-6 h-6 mb-1 ${isSelected ? 'text-white' : 'text-blue-600'}`} />
              <span className="text-xs sm:text-sm leading-tight">{btn.label}</span>
            </button>
          );
        })}
      </div>

      {/* Active Tab View Content */}
      <div className="space-y-6">
        {activeTab === 'record' && (
          <VoiceRecorder
            patientId={patientId}
            onSampleClassified={() => loadPatientOverview()}
          />
        )}

        {activeTab === 'therapy' && (
          <TherapyCoach
            patientId={patientId}
            onSessionCompleted={() => loadPatientOverview()}
          />
        )}

        {activeTab === 'meds' && (
          <MedicationLogger
            patientId={patientId}
            onLogSaved={() => loadPatientOverview()}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsList
            alerts={alerts}
            patientId={patientId}
            onAlertAcknowledged={() => loadPatientOverview()}
            allowTesting={true}
          />
        )}

        {activeTab === 'history' && (
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 space-y-6">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
              <History className="w-6 h-6 text-blue-600" />
              Recent Voice & Therapy History
            </h2>

            {/* Voice Samples Log */}
            <div>
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">
                Recent Voice Stability Samples
              </h3>
              {recentSamples.length === 0 ? (
                <p className="text-sm text-slate-400">No voice recordings yet.</p>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {recentSamples.slice(0, 5).map((s) => (
                    <div key={s.id} className="p-3.5 bg-slate-50 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-slate-900 text-sm">
                          {new Date(s.timestamp).toLocaleDateString()} at {new Date(s.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        <div className="text-xs text-slate-500">Task: {s.task_type} • Duration: {s.audio_duration_sec}s</div>
                      </div>
                      {s.classification && (
                        <div className="text-right">
                          <span className="font-bold text-blue-700 text-sm">
                            {(s.classification.risk_score * 100).toFixed(1)}% Risk
                          </span>
                          <span className="block text-[11px] text-slate-500 font-medium">
                            {s.classification.severity_level}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Therapy Sessions Log */}
            <div>
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3">
                Completed Speech Therapy Sessions
              </h3>
              {therapySessions.length === 0 ? (
                <p className="text-sm text-slate-400">No therapy sessions recorded yet.</p>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {therapySessions.slice(0, 5).map((th) => (
                    <div key={th.id} className="p-3.5 bg-slate-50 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-slate-900 text-sm flex items-center gap-1.5">
                          <Award className="w-4 h-4 text-emerald-600" />
                          Score: {th.score} / 100
                        </div>
                        <div className="text-xs text-slate-500">
                          {new Date(th.timestamp).toLocaleDateString()} • Avg Vol: {th.avg_volume_db} dB • Pitch Stability: {th.pitch_stability_pct}%
                        </div>
                      </div>
                      <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-1 rounded-full">
                        {th.score >= 80 ? 'Pass' : 'Practice'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
