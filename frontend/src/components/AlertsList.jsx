import React, { useState } from 'react';
import { Bell, AlertTriangle, AlertCircle, Info, Check, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function AlertsList({ alerts, patientId, onAlertAcknowledged, allowTesting = false }) {
  const [triggering, setTriggering] = useState(false);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      if (onAlertAcknowledged) {
        onAlertAcknowledged(alertId);
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleTestTrigger = async (type, severity) => {
    if (!patientId) return;
    setTriggering(true);
    try {
      await api.triggerTestAlert(patientId, type, severity);
      if (onAlertAcknowledged) {
        onAlertAcknowledged(null); // triggers reload
      }
    } catch (err) {
      console.error('Failed to trigger test alert:', err);
    } finally {
      setTriggering(false);
    }
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'URGENT':
        return <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />;
      case 'WARNING':
        return <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />;
      default:
        return <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'URGENT':
        return <span className="bg-red-100 text-red-800 border border-red-300 px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase">Urgent Alert</span>;
      case 'WARNING':
        return <span className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase">Warning</span>;
      default:
        return <span className="bg-blue-100 text-blue-800 border border-blue-300 px-2.5 py-0.5 rounded-full text-xs font-medium uppercase">Informational</span>;
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-100 mb-5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-6 h-6 text-blue-600" />
            Decline & Symptom Monitoring Alerts
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Statistical change-point detection and wearing-off pattern notifications.
          </p>
        </div>

        {allowTesting && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTestTrigger('DECLINE_SUDDEN', 'URGENT')}
              disabled={triggering}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold shadow-sm transition flex items-center gap-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Simulate Sudden Shift (Urgent)</span>
            </button>
            <button
              onClick={() => handleTestTrigger('DECLINE_GRADUAL', 'INFORMATIONAL')}
              disabled={triggering}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
            >
              Simulate Gradual Drift
            </button>
          </div>
        )}
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          No active alerts. Vocal biomarkers and medication intake are within expected baseline parameters.
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const isActive = alert.status === 'ACTIVE';
            return (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${
                  isActive
                    ? alert.severity === 'URGENT'
                      ? 'bg-red-50/70 border-red-200'
                      : alert.severity === 'WARNING'
                      ? 'bg-amber-50/70 border-amber-200'
                      : 'bg-blue-50/70 border-blue-200'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {getAlertIcon(alert.severity)}
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-bold text-slate-900 text-sm sm:text-base">
                        {alert.title}
                      </span>
                      {getSeverityBadge(alert.severity)}
                      <span className="text-[11px] text-slate-500 font-mono">
                        {new Date(alert.trigger_time).toLocaleDateString()} {new Date(alert.trigger_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                      {alert.message}
                    </p>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Recipients: <strong>{alert.recipient_roles ? alert.recipient_roles.join(', ') : 'All linked care team'}</strong>
                    </div>
                  </div>
                </div>

                {/* Acknowledge Button */}
                {isActive && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="self-end sm:self-center px-4 py-2 bg-white hover:bg-slate-100 border border-slate-300 text-slate-800 rounded-lg text-xs font-bold shadow-sm transition flex items-center space-x-1 min-h-[40px]"
                  >
                    <Check className="w-4 h-4 text-emerald-600 stroke-[3]" />
                    <span>Acknowledge</span>
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
