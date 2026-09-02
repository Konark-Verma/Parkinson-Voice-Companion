import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import ClinicalDisclaimer from '../components/ClinicalDisclaimer';
import AlertsList from '../components/AlertsList';
import {
  Stethoscope, Users, LineChart as ChartIcon, Pill,
  Award, Bell, Plus, Edit2, CheckCircle2, AlertTriangle,
  TrendingUp, RefreshCw, Calendar, ChevronRight, Download
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, Legend, CartesianGrid, ReferenceArea, Dot
} from 'recharts';

export default function DoctorView() {
  const { user } = useAuth();
  const [patients, setPatients] = useState([]);
  const [selectedPatientId, setSelectedPatientId] = useState(1);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadTimeMs, setLoadTimeMs] = useState(null);
  const [timeRangeDays, setTimeRangeDays] = useState(90);

  // Medication Schedule Modal state
  const [showMedModal, setShowMedModal] = useState(false);
  const [medForm, setMedForm] = useState({
    name: '',
    dosage: '',
    frequency: '3 times daily',
    scheduled_times: ['08:00', '13:00', '18:00'],
    instructions: '',
  });

  useEffect(() => {
    loadPatients();
  }, []);

  useEffect(() => {
    if (selectedPatientId) {
      loadDoctorDashboard(selectedPatientId, timeRangeDays);
    }
  }, [selectedPatientId, timeRangeDays]);

  const loadPatients = async () => {
    try {
      const data = await api.getPatients();
      setPatients(data || []);
      if (data && data.length > 0 && !selectedPatientId) {
        setSelectedPatientId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load patient list:', err);
    }
  };

  const loadDoctorDashboard = async (patientId, days) => {
    setLoading(true);
    const start = performance.now();
    try {
      const data = await api.getDoctorDashboard(patientId, days);
      setDashboardData(data);
      const elapsed = Math.round(performance.now() - start);
      setLoadTimeMs(elapsed);
    } catch (err) {
      console.error('Failed to load doctor dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMedication = async (e) => {
    e.preventDefault();
    try {
      await api.createMedication({
        patient_id: selectedPatientId,
        ...medForm,
      });
      setShowMedModal(false);
      setMedForm({
        name: '',
        dosage: '',
        frequency: '3 times daily',
        scheduled_times: ['08:00', '13:00', '18:00'],
        instructions: '',
      });
      loadDoctorDashboard(selectedPatientId, timeRangeDays);
    } catch (err) {
      console.error('Failed to save medication:', err);
    }
  };

  // Custom Dot renderer for Recharts to highlight Pre-Dose Wearing-Off Dips
  const renderCustomDot = (props) => {
    const { cx, cy, payload } = props;
    if (payload.is_pre_dose_dip) {
      return (
        <svg x={cx - 6} y={cy - 6} width={12} height={12} fill="#DC2626" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="#FFFFFF" strokeWidth="2" />
        </svg>
      );
    }
    return <circle cx={cx} cy={cy} r={3} fill="#1E3A8A" />;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <ClinicalDisclaimer />

      {/* Clinical Dashboard Header */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <span className="text-xs uppercase tracking-wider text-blue-400 font-semibold flex items-center gap-1.5">
            <Stethoscope className="w-4 h-4 text-blue-400" />
            Neurology Clinical Command Center
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-0.5">
            {user?.full_name || 'Dr. Emily Vance, MD'}
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Specialty: Movement Disorders & Neuro-Acoustic Monitoring
          </p>
        </div>

        {/* 90-Day Query Performance Badge */}
        {loadTimeMs !== null && (
          <div className="bg-slate-800 border border-slate-700 p-3 rounded-xl text-right">
            <span className="text-[11px] text-slate-400 block uppercase font-medium">
              90-Day Longitudinal Load Time
            </span>
            <div className="text-xl font-mono font-bold text-emerald-400">
              {loadTimeMs} ms <span className="text-xs text-slate-400 font-normal">(&le;3.0s SLA)</span>
            </div>
          </div>
        )}
      </div>
      {/* Header controls & Patient selector */}
      <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center text-blue-700">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Neurologist Longitudinal Dashboard</h2>
            <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
              <span>Selecting Patient:</span>
              <select
                value={selectedPatientId}
                onChange={(e) => setSelectedPatientId(Number(e.target.value))}
                className="bg-slate-100 font-bold text-slate-900 px-2.5 py-1 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-600"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (DOB: {p.date_of_birth || '1955'} • Dx: {p.diagnosis_year || '2021'})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Time range switcher & Export CSV Button */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl">
            <span className="text-xs font-semibold text-slate-500 uppercase px-2">Window:</span>
            {[14, 30, 60, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRangeDays(days)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                  timeRangeDays === days
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>

          <button
            onClick={handleExportCSV}
            disabled={!dashboardData}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-bold transition shadow-sm flex items-center space-x-1.5 disabled:opacity-50"
            title="Download 90-day clinical trajectory CSV report"
          >
            <Download className="w-4 h-4 text-teal-400" />
            <span>Export CSV Report</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-500 border border-slate-200 flex flex-col items-center justify-center">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mb-3" />
          <span className="font-semibold text-base">Aggregating 90-day clinical longitudinal trajectories...</span>
        </div>
      )}

      {dashboardData && !loading && (
        <>
          {/* Key Clinical Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Current Acoustic Risk */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                Latest Voice Risk Score
              </span>
              <div className="text-3xl font-extrabold text-blue-700 mt-1">
                {dashboardData.patient.latest_risk_score
                  ? `${(dashboardData.patient.latest_risk_score * 100).toFixed(1)}%`
                  : '48.2%'}
              </div>
              <span className="text-xs text-slate-500 font-medium block mt-1">
                Severity: <strong>{dashboardData.patient.latest_severity_level}</strong>
              </span>
            </div>

            {/* Wearing-Off Rate */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                Pre-Dose Wearing-Off Rate
              </span>
              <div className="text-3xl font-extrabold text-amber-600 mt-1">
                {dashboardData.wearing_off_summary.wearing_off_rate_pct}%
              </div>
              <span className="text-xs text-slate-500 font-medium block mt-1">
                {dashboardData.wearing_off_summary.pre_dose_dips_detected} dips / {dashboardData.wearing_off_summary.total_monitored_doses} doses
              </span>
            </div>

            {/* Active Clinical Alerts */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                Active Decline Alerts
              </span>
              <div className="text-3xl font-extrabold text-red-600 mt-1">
                {dashboardData.patient.active_alerts_count}
              </div>
              <span className="text-xs text-slate-500 font-medium block mt-1">
                {dashboardData.patient.wearing_off_pattern_flagged ? 'Pattern Flagged' : 'Stable'}
              </span>
            </div>

            {/* Therapy Adherence */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                Speech Therapy Sessions
              </span>
              <div className="text-3xl font-extrabold text-emerald-600 mt-1">
                {dashboardData.recent_therapy_sessions.length}
              </div>
              <span className="text-xs text-slate-500 font-medium block mt-1">
                Avg Score: {dashboardData.recent_therapy_sessions.length > 0 ? Math.round(dashboardData.recent_therapy_sessions.reduce((a, b) => a + b.score, 0) / dashboardData.recent_therapy_sessions.length) : 85} / 100
              </span>
            </div>
          </div>

          {/* Module 1 & 3: 90-Day Longitudinal Severity & Trend Chart */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-lg sm:text-xl font-bold text-slate-900 flex items-center gap-2">
                  <ChartIcon className="w-5 h-5 text-blue-600" />
                  {timeRangeDays}-Day Longitudinal Voice Risk & Medication Correlation
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Red indicators mark detected pre-dose wearing-off acoustic dips.
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-blue-600 inline-block" /> Acoustic Risk
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-red-600 inline-block" /> Pre-Dose Dip
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> HNR (dB)
                </span>
              </div>
            </div>

            {/* Recharts Multi-line Trend Chart */}
            <div className="w-full h-80 sm:h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={dashboardData.trend_90d.map((p) => ({
                    ...p,
                    risk_pct: Math.round(p.risk_score * 100),
                    jitter_pct: p.jitter ? Math.round(p.jitter * 100) / 100 : null,
                    hnr_db: p.hnr ? Math.round(p.hnr * 10) / 10 : null,
                  }))}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} />
                  <YAxis
                    yAxisId="left"
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: '#64748B' }}
                    label={{ value: 'Risk Score (%)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#64748B' }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    domain={[10, 30]}
                    tick={{ fontSize: 11, fill: '#64748B' }}
                    label={{ value: 'HNR (dB)', angle: 90, position: 'insideRight', fontSize: 11, fill: '#64748B' }}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const d = payload[0].payload;
                        return (
                          <div className="bg-slate-900 text-white p-3 rounded-xl text-xs shadow-xl space-y-1">
                            <p className="font-bold text-blue-300">{label}</p>
                            <p>Acoustic Risk: <strong className="text-white">{d.risk_pct}%</strong> ({d.severity_level})</p>
                            <p>HNR: <strong>{d.hnr_db} dB</strong> | Jitter: <strong>{d.jitter}%</strong></p>
                            {d.is_pre_dose_dip && (
                              <p className="text-red-400 font-bold">⚠️ Pre-Dose Wearing-Off Dip Detected</p>
                            )}
                            {d.medication_taken && (
                              <p className="text-emerald-300 font-semibold">💊 Dose Taken: {d.medication_name}</p>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="risk_pct"
                    name="Acoustic Risk (%)"
                    stroke="#2563EB"
                    strokeWidth={2.5}
                    dot={renderCustomDot}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="hnr_db"
                    name="Harmonics-to-Noise Ratio (dB)"
                    stroke="#10B981"
                    strokeWidth={1.8}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Module 1: Medication Schedule Management (Doctor Only) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
              <div>
                <h3 className="text-lg sm:text-xl font-bold text-slate-900 flex items-center gap-2">
                  <Pill className="w-5 h-5 text-blue-600" />
                  Medication Regimen & Dosing Schedule (Doctor Only)
                </h3>
                <p className="text-sm text-slate-500 mt-0.5">
                  Update dosage, dosing frequency, and intake times to address wearing-off dips.
                </p>
              </div>

              <button
                onClick={() => setShowMedModal(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm flex items-center space-x-1.5 transition min-h-[44px]"
              >
                <Plus className="w-4 h-4 stroke-[3]" />
                <span>Add Medication</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboardData.active_medications.map((med) => (
                <div key={med.id} className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex justify-between items-start">
                  <div>
                    <span className="font-bold text-slate-900 text-base">{med.name}</span>
                    <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                      {med.dosage}
                    </span>
                    <div className="text-xs text-slate-600 mt-1">
                      Frequency: <strong>{med.frequency}</strong> • Scheduled Times: <strong>{med.scheduled_times.join(', ')}</strong>
                    </div>
                    {med.instructions && (
                      <p className="text-xs text-slate-500 italic mt-1">&quot;{med.instructions}&quot;</p>
                    )}
                  </div>
                  <span className="bg-emerald-100 text-emerald-800 text-[11px] font-bold px-2 py-0.5 rounded">
                    Active
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Module 2 & 3: Therapy History & Decline Alerts Panels */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Speech Therapy Adherence Panel */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100">
                <Award className="w-5 h-5 text-blue-600" />
                Speech Therapy History & Loudness Adherence
              </h3>
              {dashboardData.recent_therapy_sessions.length === 0 ? (
                <p className="text-sm text-slate-400">No therapy sessions recorded.</p>
              ) : (
                <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                  {dashboardData.recent_therapy_sessions.slice(0, 8).map((th) => (
                    <div key={th.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-bold text-slate-900 text-sm">{new Date(th.timestamp).toLocaleDateString()}</span>
                        <div className="text-slate-500 mt-0.5">
                          Avg: <strong>{th.avg_volume_db} dB</strong> • Pitch Stability: <strong>{th.pitch_stability_pct}%</strong>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-extrabold text-blue-700">{th.score} / 100</span>
                        <span className="block text-[10px] text-slate-400 font-mono">{th.duration_sec}s duration</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Decline Alerts Review Panel */}
            <AlertsList
              alerts={dashboardData.alerts}
              patientId={selectedPatientId}
              onAlertAcknowledged={() => loadDoctorDashboard(selectedPatientId, timeRangeDays)}
              allowTesting={true}
            />
          </div>
        </>
      )}

      {/* Medication Create Modal */}
      {showMedModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 animate-fadeIn">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Pill className="w-5 h-5 text-blue-600" />
              Prescribe / Update Medication Schedule
            </h3>
            <form onSubmit={handleCreateMedication} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Medication Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Carbidopa / Levodopa ER"
                  value={medForm.name}
                  onChange={(e) => setMedForm({ ...medForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Dosage</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 50 / 200 mg"
                    value={medForm.dosage}
                    onChange={(e) => setMedForm({ ...medForm, dosage: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Frequency</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 3x daily"
                    value={medForm.frequency}
                    onChange={(e) => setMedForm({ ...medForm, frequency: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Scheduled Times (Comma-separated HH:MM)</label>
                <input
                  type="text"
                  required
                  placeholder="08:00, 13:00, 18:00"
                  value={medForm.scheduled_times.join(', ')}
                  onChange={(e) => setMedForm({
                    ...medForm,
                    scheduled_times: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Clinical Instructions</label>
                <textarea
                  placeholder="Take 30 minutes before mealtime..."
                  value={medForm.instructions}
                  onChange={(e) => setMedForm({ ...medForm, instructions: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowMedModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-sm"
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
