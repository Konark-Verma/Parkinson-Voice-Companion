import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Activity, User, HeartHandshake, Stethoscope, Bell } from 'lucide-react';

export default function Header() {
  const { user, activeRole, switchRole, activeToast, dismissToast } = useAuth();

  const roles = [
    { id: 'PATIENT', label: 'Patient View', icon: User, desc: 'Large-touch & Voice' },
    { id: 'CAREGIVER', label: 'Caregiver View', icon: HeartHandshake, desc: 'Meds & Alerts' },
    { id: 'DOCTOR', label: 'Doctor View', icon: Stethoscope, desc: '90-Day Trends' },
  ];

  return (
    <header className="bg-slate-900 text-white shadow-md border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Parkinson&apos;s Voice Companion
                <span className="text-[10px] font-medium bg-blue-900/80 text-blue-300 px-2 py-0.5 rounded-full uppercase tracking-wider border border-blue-700">
                  Prototype
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Voice-Based Monitoring, Therapy Aid & Correlation Tracker
              </p>
            </div>
          </div>
        </div>

        {/* Role Switcher Toolbar */}
        <div className="flex items-center justify-between md:justify-end gap-2 bg-slate-800/80 p-1.5 rounded-xl border border-slate-700">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 hidden lg:inline">
            Active Role:
          </span>
          <div className="flex space-x-1">
            {roles.map((r) => {
              const Icon = r.icon;
              const isActive = activeRole === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => switchRole(r.id)}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 min-h-[44px] ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 ring-1 ring-blue-400'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700/60'
                  }`}
                  aria-pressed={isActive}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Real-Time Alert Toast Notification Banner */}
      {activeToast && (
        <div
          className={`border-b px-4 py-2.5 transition-all flex items-center justify-between shadow-inner ${
            activeToast.severity === 'URGENT'
              ? 'bg-red-600 text-white border-red-700 font-medium'
              : activeToast.severity === 'WARNING'
              ? 'bg-amber-500 text-slate-950 border-amber-600 font-medium'
              : 'bg-blue-700 text-white border-blue-800'
          }`}
        >
          <div className="max-w-7xl mx-auto flex items-center justify-between w-full">
            <div className="flex items-center space-x-3">
              <span className="flex h-3 w-3 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
              </span>
              <Bell className="w-5 h-5 flex-shrink-0" />
              <div className="text-xs sm:text-sm">
                <strong>[{activeToast.severity} ALERT - {activeToast.patientName}]:</strong> {activeToast.title} — {activeToast.message}
              </div>
            </div>
            <button
              onClick={dismissToast}
              className="ml-4 px-2 py-1 bg-black/20 hover:bg-black/30 rounded text-xs uppercase tracking-wider font-bold transition"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
