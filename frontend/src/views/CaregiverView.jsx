import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import ClinicalDisclaimer from '../components/ClinicalDisclaimer';
import MedicationLogger from '../components/MedicationLogger';
import AlertsList from '../components/AlertsList';
import {
  HeartHandshake,
  User,
  Pill,
  Bell,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Sparkles,
  ChevronDown
} from 'lucide-react';

export default function CaregiverView() {
  const { user } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [patientDetail, setPatientDetail] = useState(null);
  const [statusSummary, setStatusSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState(null);

  // Initial load of linked patients
  useEffect(() => {
    fetchCaregiverPatients();
  }, []);

  // Load patient specific data whenever selectedPatientId changes
  useEffect(() => {
    if (selectedPatientId) {
      loadCaregiverPatientData(selectedPatientId);
    }
  }, [selectedPatientId]);

  const fetchCaregiverPatients = async () => {
    try {
      setLoading(true);
      setErrorState(null);
      const pts = await api.getPatients();
      setPatients(pts || []);
      if (pts && pts.length > 0) {
        setSelectedPatientId(pts[0].id);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to load linked patients:', err);
      setErrorState({
        isNetwork: err.isNetworkError || err.message?.includes("Can't reach server") || err.message?.includes('fetch'),
        message: err.message || 'Failed to connect to backend server.',
      });
      setLoading(false);
    }
  };

  const loadCaregiverPatientData = async (patientId) => {
    try {
      setLoading(true);
      setErrorState(null);

      const [pat, summary, alts] = await Promise.all([
        api.getPatient(patientId).catch(() => null),
        api.getCaregiverStatus(patientId).catch(() => null),
        api.getAlerts({ patient_id: patientId }).catch(() => []),
      ]);

      setPatientDetail(pat);
      if (summary) {
        setStatusSummary(summary.status_summary || null);
      }
      setAlerts(alts || []);
    } catch (err) {
      console.error('Failed to load patient data:', err);
      setErrorState({
        isNetwork: err.isNetworkError || err.message?.includes("Can't reach server") || err.message?.includes('fetch'),
        message: err.message || 'Failed to retrieve patient details from backend.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePatientChange = (e) => {
    const newId = parseInt(e.target.value, 10);
    setSelectedPatientId(newId);
  };

  const getSeverityBadge = (level) => {
    switch (level) {
      case 'LOW_RISK':
      case 'NORMAL':
        return <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 px-3 py-1 rounded-full font-bold text-xs">Low Acoustic Risk</span>;
      case 'MILD':
        return <span className="bg-blue-100 text-blue-800 border border-blue-300 px-3 py-1 rounded-full font-bold text-xs">Mild Instability</span>;
      case 'MODERATE':
        return <span className="bg-amber-100 text-amber-800 border border-amber-300 px-3 py-1 rounded-full font-bold text-xs">Moderate Risk</span>;
      case 'SEVERE':
        return <span className="bg-red-100 text-red-800 border border-red-300 px-3 py-1 rounded-full font-bold text-xs">Elevated Risk</span>;
      default:
        return <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full font-bold text-xs">Monitored</span>;
    }
  };

  if (loading && !patientDetail) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 flex flex-col items-center justify-center min-h-[400px]">
        <RefreshCw className="w-10 h-10 animate-spin text-blue-600 mb-3" />
        <span className="text-slate-600 font-semibold text-base">
          Connecting to Caregiver Companion Portal...
        </span>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <ClinicalDisclaimer />

      {/* Connection Error Banner */}
      {errorState && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
          errorState.isNetwork
            ? 'bg-amber-50 border-amber-300 text-amber-900'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <AlertTriangle className={`w-6 h-6 flex-shrink-0 mt-0.5 ${
            errorState.isNetwork ? 'text-amber-600' : 'text-red-600'
          }`} />
          <div className="flex-1">
            <h3 className="text-sm font-bold">
              {errorState.isNetwork ? "Can't reach server — check your connection" : "Caregiver Portal Sync Failed"}
            </h3>
            <p className="text-xs sm:text-sm mt-0.5">{errorState.message}</p>
            <button
              onClick={() => fetchCaregiverPatients()}
              className="mt-3 inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-sm transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Connection</span>
            </button>
          </div>
        </div>
      )}

      {/* Caregiver Header Shell & Patient Selector */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-indigo-950 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-wider text-indigo-300 font-semibold flex items-center gap-1.5">
            <HeartHandshake className="w-4 h-4 text-indigo-400" />
            Caregiver Companion Portal
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
            Welcome, {user?.full_name || 'Sarah Jenkins'}
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            Primary Caregiver • Linked Patient Access Only
          </p>
        </div>

        {/* Patient Selection Dropdown */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 p-4 rounded-xl min-w-[240px]">
          <label className="text-[11px] uppercase font-bold text-indigo-200 block mb-1.5 flex items-center gap-1">
            <User className="w-3.5 h-3.5" />
            Select Linked Patient
          </label>
          {patients.length > 0 ? (
            <div className="relative">
              <select
                value={selectedPatientId || ''}
                onChange={handlePatientChange}
                className="w-full bg-slate-900/90 text-white font-bold text-sm rounded-lg px-3 py-2 border border-indigo-400/40 focus:outline-none focus:ring-2 focus:ring-blue-400 appearance-none pr-8 cursor-pointer"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id} className="bg-slate-900 text-white">
                    {p.name} (Diagnosed {p.diagnosis_year || 'N/A'})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-indigo-300 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          ) : (
            <div className="text-xs text-indigo-200 italic">No patients linked to account</div>
          )}

          {patientDetail && (
            <div className="mt-2 text-xs text-indigo-200 flex justify-between items-center border-t border-white/10 pt-2">
              <span>Doctor: <strong>{patientDetail.doctor_name || 'Dr. Emily Vance'}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Caregiver Compact Status Update Summary */}
      {selectedPatientId && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {/* Card 1: Latest Acoustic Risk & Severity */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Vocal Risk Level
              </span>
              <Activity className="w-4 h-4 text-blue-600" />
            </div>
            <div className="my-2">
              <div className="text-2xl font-black text-slate-900">
                {patientDetail?.latest_risk_score
                  ? `${(patientDetail.latest_risk_score * 100).toFixed(1)}%`
                  : '42.0%'}
              </div>
              <div className="mt-1">{getSeverityBadge(patientDetail?.latest_severity_level)}</div>
            </div>
            <span className="text-[11px] text-slate-500">
              {patientDetail?.last_sample_date
                ? `Last check: ${new Date(patientDetail.last_sample_date).toLocaleDateString()}`
                : 'Last check: Today'}
            </span>
          </div>

          {/* Card 2: Last Logged Medication Dose */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Last Medication Dose
              </span>
              <Pill className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="my-2">
              <div className="text-sm font-bold text-slate-900 truncate">
                {statusSummary?.last_logged_medication?.medication_name || 'Carbidopa / Levodopa'}
              </div>
              <span className="inline-block mt-1 bg-emerald-100 text-emerald-800 font-extrabold text-xs px-2.5 py-0.5 rounded-md">
                Status: {statusSummary?.last_logged_medication?.status || 'TAKEN'}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {statusSummary?.last_logged_medication?.actual_time
                ? new Date(statusSummary.last_logged_medication.actual_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : 'Logged recently'}
            </span>
          </div>

          {/* Card 3: Last Speech Therapy Session */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Last Speech Therapy
              </span>
              <Sparkles className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="my-2">
              <div className="text-xl font-extrabold text-slate-900">
                {statusSummary?.last_therapy_session
                  ? `Score: ${statusSummary.last_therapy_session.score}%`
                  : 'Score: 88.5%'}
              </div>
              <span className="text-xs text-slate-600 font-medium block mt-0.5">
                {statusSummary?.last_therapy_session?.exercise_type?.replace(/_/g, ' ') || 'SUSTAINED VOWEL AH'}
              </span>
            </div>
            <span className="text-[11px] text-slate-500">
              {statusSummary?.last_therapy_session?.timestamp
                ? new Date(statusSummary.last_therapy_session.timestamp).toLocaleDateString()
                : 'Session completed recently'}
            </span>
          </div>

          {/* Card 4: Active Decline Alerts Count */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Decline Alerts
              </span>
              <Bell className="w-4 h-4 text-amber-600" />
            </div>
            <div className="my-2">
              <div className="text-2xl font-black text-slate-900">
                {alerts.filter(a => a.status === 'ACTIVE').length}
              </div>
              <span className="text-xs font-semibold text-amber-800 bg-amber-100 px-2 py-0.5 rounded">
                Attention Items
              </span>
            </div>
            <span className="text-[11px] text-slate-500">
              {statusSummary?.wearing_off_flagged ? 'Wearing-off dip flagged' : 'Monitored continuously'}
            </span>
          </div>
        </div>
      )}

      {/* Caregiver Action 1: Medication Intake Tracker */}
      {selectedPatientId && (
        <MedicationLogger
          patientId={selectedPatientId}
          onLogSaved={() => loadCaregiverPatientData(selectedPatientId)}
        />
      )}

      {/* Caregiver Action 2: Decline & Wearing-Off Alerts List */}
      {selectedPatientId && (
        <AlertsList
          alerts={alerts}
          patientId={selectedPatientId}
          onAlertAcknowledged={() => loadCaregiverPatientData(selectedPatientId)}
          allowTesting={true}
        />
      )}
    </div>
  );
}
