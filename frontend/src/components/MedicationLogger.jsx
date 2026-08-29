import React, { useState, useEffect } from 'react';
import { Pill, Check, Clock, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function MedicationLogger({ patientId, onLogSaved }) {
  const [medications, setMedications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loggingId, setLoggingId] = useState(null);
  const [recentLogResult, setRecentLogResult] = useState(null);

  useEffect(() => {
    loadMedications();
  }, [patientId]);

  const loadMedications = async () => {
    if (!patientId) return;
    try {
      setLoading(true);
      const data = await api.getPatientMedications(patientId);
      setMedications(data.filter((m) => m.is_active));
    } catch (err) {
      console.error('Failed to load medications:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogIntake = async (med, status = 'TAKEN') => {
    setLoggingId(med.id);
    setRecentLogResult(null);

    // Current scheduled or actual time
    const nowIso = new Date().toISOString();
    const payload = {
      medication_id: med.id,
      status: status,
      scheduled_time: nowIso,
      actual_time: nowIso,
      notes: `Logged via 1-Tap quick companion (${status})`,
    };

    try {
      const resp = await api.logMedicationIntake(payload);
      setRecentLogResult(resp);
      if (onLogSaved) {
        onLogSaved(resp);
      }
    } catch (err) {
      console.error('Failed to log intake:', err);
    } finally {
      setLoggingId(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center justify-center min-h-[160px]">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-2" />
        <span className="text-slate-600 font-medium">Loading medication schedule...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-6 h-6 text-blue-600" />
            Medication Intake Tracker
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            1-Tap logging auto-correlates voice stability for pre-dose wearing-off dips.
          </p>
        </div>
      </div>

      {medications.length === 0 ? (
        <div className="text-center py-6 text-slate-500 text-sm">
          No active medication schedules configured by your neurologist yet.
        </div>
      ) : (
        <div className="space-y-4">
          {medications.map((med) => (
            <div
              key={med.id}
              className="bg-slate-50 rounded-xl p-4 sm:p-5 border border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
            >
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-lg text-slate-900">{med.name}</span>
                  <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                    {med.dosage}
                  </span>
                </div>
                <div className="text-xs sm:text-sm text-slate-500 mt-1 flex flex-wrap gap-2 items-center">
                  <span>Frequency: <strong>{med.frequency}</strong></span>
                  <span>•</span>
                  <span>Times: <strong>{med.scheduled_times.join(', ')}</strong></span>
                </div>
                {med.instructions && (
                  <div className="text-xs text-slate-600 italic mt-1 bg-white p-1.5 rounded border border-slate-200">
                    &quot;{med.instructions}&quot;
                  </div>
                )}
              </div>

              {/* 1-Tap Action Buttons */}
              <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
                <button
                  onClick={() => handleLogIntake(med, 'TAKEN')}
                  disabled={loggingId === med.id}
                  className="flex-1 sm:flex-initial px-4 py-3 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-xl font-bold text-xs sm:text-sm shadow-md shadow-emerald-600/30 flex items-center justify-center space-x-1.5 transition min-h-[44px]"
                >
                  <Check className="w-4 h-4 stroke-[2.5]" />
                  <span>{loggingId === med.id ? 'Logging...' : 'Taken'}</span>
                </button>

                <button
                  onClick={() => handleLogIntake(med, 'SKIPPED')}
                  disabled={loggingId === med.id}
                  className="px-3 py-3 bg-rose-100 hover:bg-rose-200 text-rose-800 rounded-xl font-semibold text-xs sm:text-sm transition min-h-[44px]"
                  title="Mark as Skipped"
                >
                  Skipped
                </button>

                <button
                  onClick={() => handleLogIntake(med, 'DELAYED')}
                  disabled={loggingId === med.id}
                  className="px-3 py-3 bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-xl font-semibold text-xs sm:text-sm transition min-h-[44px]"
                  title="Mark as Delayed"
                >
                  Delayed
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Real-time Wearing-Off Feedback */}
      {recentLogResult && (
        <div className="mt-5 p-4 rounded-xl border animate-fadeIn bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span className="font-bold text-slate-900 text-sm">
              Intake Logged Successfully for {recentLogResult.medication_name} ({recentLogResult.status})
            </span>
          </div>

          {recentLogResult.wearing_off_detected ? (
            <div className="mt-2 text-xs sm:text-sm text-amber-900 bg-amber-100/80 p-2.5 rounded-lg border border-amber-300 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Wearing-Off Correlation Detected:</strong> Voice stability readings prior to this dose showed elevated acoustic risk compared to baseline. Logged in clinical audit trail.
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-600 mt-1">
              Voice stability in pre-dose window is within normal baseline range.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
