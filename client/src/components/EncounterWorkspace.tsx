import React, { useState } from 'react';

type SoapSection = 'subjective' | 'objective' | 'assessment' | 'plan';

const soapSectionMeta: Record<SoapSection, { label: string; placeholder: string; rows: number }> = {
  subjective: {
    label: 'Subjective',
    placeholder: 'History of present illness, patient-reported symptoms, and relevant context...',
    rows: 5,
  },
  objective: {
    label: 'Objective',
    placeholder: 'Observed exam findings, vitals, testing, and measurable clinical data...',
    rows: 5,
  },
  assessment: {
    label: 'Assessment',
    placeholder: 'Working diagnosis, differential, and any ICD-10 codes or impressions...',
    rows: 6,
  },
  plan: {
    label: 'Plan',
    placeholder: 'Treatment plan, medications, follow-up, education, and return precautions...',
    rows: 6,
  },
};

const emptySoapDraft = {
  subjective: '',
  objective: '',
  assessment: '',
  plan: '',
};

export default function EncounterWorkspace() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [transcript, setTranscript] = useState('');
  const [soapDraft, setSoapDraft] = useState(emptySoapDraft);

  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingSoap, setIsGeneratingSoap] = useState(false);
  const [savedEncounterId, setSavedEncounterId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const updateSoapField = (field: SoapSection, value: string) => {
    setSoapDraft((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleGenerateSoap = async () => {
    setIsGeneratingSoap(true);
    setErrorMessage('');
    setSuccessMessage('');

    if (!transcript.trim()) {
      setErrorMessage('Enter a transcript or clinical observation before generating SOAP fields.');
      setIsGeneratingSoap(false);
      return;
    }

    try {
      const response = await fetch('/api/encounters/generate-soap', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: transcript.trim(),
          template_id: null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate SOAP note.');
      }

      setSoapDraft({
        subjective: data.subjective ?? '',
        objective: data.objective ?? '',
        assessment: data.assessment ?? '',
        plan: data.plan ?? '',
      });
      setSuccessMessage('SOAP draft generated from transcript. Review and edit as needed.');
    } catch (err) {
      console.error('SOAP generation error:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Unable to generate SOAP note.');
    } finally {
      setIsGeneratingSoap(false);
    }
  };

  const handleSaveEncounter = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage('');
    setSuccessMessage('');

    if (!firstName || !lastName || !dob || !transcript.trim()) {
      setErrorMessage('Please fill out the patient fields and provide a transcript or observations.');
      setIsSaving(false);
      return;
    }

    try {
      const payload = {
        patient: {
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          dob,
        },
        transcript: transcript.trim(),
        template_id: null,
        soap_note_json: {
          subjective: soapDraft.subjective.trim(),
          objective: soapDraft.objective.trim(),
          assessment: soapDraft.assessment.trim(),
          plan: soapDraft.plan.trim(),
        },
      };

      const response = await fetch('/api/encounters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to save encounter to the database.');
      }

      setSavedEncounterId(data.encounter_id);
      setSuccessMessage(`Encounter saved. Record ID #${data.encounter_id} is ready for SOAP finalization.`);
    } catch (err) {
      console.error('Save error:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Network connectivity error.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-slate-50 px-4 py-6 sm:px-6 lg:px-8">
      <div className="rounded-2xl border border-slate-200 bg-white shadow-[0_18px_60px_rgba(15,23,42,0.08)]">
        <div className="border-b border-slate-200 bg-blue-950 px-6 py-5 text-white sm:px-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Provider Workspace</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight">New Clinical Encounter</h2>
              <p className="mt-2 max-w-3xl text-sm text-slate-300">
                Enter the encounter transcript, then manually author or edit the SOAP note sections before finalizing.
              </p>
            </div>
            {savedEncounterId && (
              <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-200">
                Active Record #{savedEncounterId}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6 p-6 sm:p-8">
          {errorMessage && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
              {errorMessage}
            </div>
          )}

          {successMessage && !errorMessage && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              {successMessage}
            </div>
          )}

          <form onSubmit={handleSaveEncounter} className="space-y-6 grid grid-cols-2 gap-5">
            <div>
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-600">Patient</h3>
                    <p className="mt-1 text-sm text-slate-500">Demographics required to bind the encounter to a chart.</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">First Name</label>
                    <input
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Last Name</label>
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                      placeholder="Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Date of Birth</label>
                    <input
                      type="date"
                      value={dob}
                      onChange={(e) => setDob(e.target.value)}
                      className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                    />
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-600">Transcript</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Paste the encounter transcript or freeform clinical observations here.
                  </p>
                </div>

                <textarea
                  rows={8}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="block w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-500 focus:bg-white focus:ring-2 focus:ring-slate-200"
                  placeholder="Patient presents with a 3-day history of scratchy throat, worsening dry cough..."
                />
              </section>
            </div>

            <div>
              <section className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-600">SOAP Draft</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Manually enter or edit each section. These fields remain editable before final SOAP versioning.
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  {(Object.keys(soapSectionMeta) as SoapSection[]).map((section) => {
                    const meta = soapSectionMeta[section];

                    return (
                      <div key={section} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <label className="text-sm font-semibold text-slate-800">{meta.label}</label>
                          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Editable</span>
                        </div>
                        <textarea
                          rows={meta.rows}
                          value={soapDraft[section]}
                          onChange={(e) => updateSoapField(section, e.target.value)}
                          className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm leading-6 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                          placeholder={meta.placeholder}
                        />
                      </div>
                    );
                  })}
                </div>
              </section>

              <div className="flex flex-col gap-3 border-t border-slate-200 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-slate-500">
                  SOAP content can be entered now and finalized separately after review.
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <button
                    type="button"
                    onClick={handleGenerateSoap}
                    disabled={isGeneratingSoap || isSaving}
                    className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold shadow-sm transition ${isGeneratingSoap || isSaving
                        ? 'cursor-not-allowed border border-slate-300 bg-slate-100 text-slate-400'
                        : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                  >
                    {isGeneratingSoap ? 'Generating SOAP...' : 'Generate SOAP from Transcript'}
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving || isGeneratingSoap}
                    className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-sm transition ${isSaving || isGeneratingSoap ? 'cursor-not-allowed bg-slate-400' : 'bg-slate-950 hover:bg-slate-800'
                      }`}
                  >
                    {isSaving ? 'Saving encounter...' : 'Save Encounter'}
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
