import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';

export default function ClinicalDisclaimer({ compact = false }) {
  if (compact) {
    return (
      <div className="bg-amber-50 border border-amber-300 rounded-lg p-2.5 flex items-center space-x-2 text-amber-900 text-xs sm:text-sm font-medium">
        <ShieldAlert className="w-4 h-4 text-amber-700 flex-shrink-0" />
        <span>
          <strong>Monitoring Aid Only:</strong> This tool generates vocal stability risk indicators and does NOT provide medical diagnoses.
        </span>
      </div>
    );
  }

  return (
    <aside aria-label="Clinical Disclaimer" className="bg-amber-50/90 border-l-4 border-amber-500 p-3.5 sm:p-4 rounded-r-lg text-amber-950 shadow-sm">
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm leading-relaxed">
          <p className="font-semibold text-amber-900">
            Important Clinical & Regulatory Notice
          </p>
          <p className="mt-0.5 text-amber-800">
            Parkinson&apos;s Voice Companion is an experimental screening/monitoring support tool and speech therapy aid.
            It is <strong>NOT</strong> a diagnostic medical device and does not replace evaluation by a licensed physician,
            neurologist, or LSVT-certified speech-language pathologist. Acoustic risk scores represent vocal tremor/dysphonia indicators, not clinical diagnoses.
          </p>
        </div>
      </div>
    </aside>
  );
}
