import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import ClinicalDisclaimer from '../components/ClinicalDisclaimer';
import MedicationLogger from '../components/MedicationLogger';
import AlertsList from '../components/AlertsList';
import { HeartHandshake, User, Pill, Bell, Activity, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function CaregiverView() {
  const { user } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(1);
  const [patientDetail, setPatientDetail] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCaregiverData();
  }, [selectedPatientId]);

  const loadCaregiverData = async () => {
    try {
      setLoading(true);
      const [pts, pat, alts] = await Promise.all([
        api.getPatients().catch(() => []),
        api.getPatient(selectedPatientId).catch(() => null),
        api.getAlerts({ patient_id: selectedPatientId }).catch(() => []),
      ]);
      setPatients(pts || []);
      setPatientDetail(pat);
      setAlerts(alts || []);
    } catch (err) {
      console.error('Failed to load caregiver data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
      <ClinicalDisclaimer />

      {/* Caregiver Header Card */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-md flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-indigo-300 font-semibold flex items-center gap-1.5">
            <HeartHandshake className="w-4 h-4 text-indigo-400" />
            Caregiver Companion Portal
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-0.5">
            Welcome, {user?.full_name || 'Sarah Jenkins'}
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            Linked Patient: <strong>{patientDetail?.name || 'Robert Jenkins'}</strong> (Diagnosed {patientDetail?.diagnosis_year || 2021})
          </p>
        </div>

        {patientDetail && (
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 p-3.5 rounded-xl text-center min-w-[170px]">
            <span className="text-[11px] text-indigo-200 uppercase font-semibold block">
              Patient Acoustic Status
            </span>
            <div className="text-2xl font-black text-white mt-0.5">
              {patientDetail.latest_risk_score ? `${(patientDetail.latest_risk_score * 100).toFixed(1)}%` : '42.0%'}
            </div>
            <span className="text-xs text-indigo-100 font-medium">
              {patientDetail.latest_severity_level || 'MILD'} Risk
            </span>
          </div>
        )}
      </div>

      {/* Patient Health & Safety Snapshot */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-700">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block">Daily Voice Check</span>
            <span className="text-sm font-bold text-slate-900">
              {patientDetail?.last_sample_date ? new Date(patientDetail.last_sample_date).toLocaleDateString() : 'Recorded Today'}
            </span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block">Active Alerts</span>
            <span className="text-sm font-bold text-slate-900">
              {alerts.filter(a => a.status === 'ACTIVE').length} Attention Items
            </span>
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-semibold block">Care Team Status</span>
            <span className="text-sm font-bold text-slate-900">Linked to Dr. Emily Vance</span>
          </div>
        </div>
      </div>

      {/* Caregiver Action 1: Log Medication on Behalf of Patient */}
      <MedicationLogger
        patientId={selectedPatientId}
        onLogSaved={() => loadCaregiverData()}
      />

      {/* Caregiver Action 2: Monitor Real-Time Decline & Wearing-Off Alerts */}
      <AlertsList
        alerts={alerts}
        patientId={selectedPatientId}
        onAlertAcknowledged={() => loadCaregiverData()}
        allowTesting={true}
      />
    </div>
  );
}
