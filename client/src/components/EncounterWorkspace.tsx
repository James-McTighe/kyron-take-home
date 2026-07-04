import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Icd10SearchWidget } from './Icd10SearchWidget';

export const EncounterWorkspace: React.FC = () => {
  const { token } = useAuth();
  const [encounterId, setEncounterId] = useState<number | null>(null);
  const [patient, setPatient] = useState({ firstName: '', lastName: '', dob: '' });
  const [transcript, setTranscript] = useState('');
  const [soapNote, setSoapNote] = useState({ subjective: '', objective: '', assessment: '', plan: '' });
  const [isGenerating, setIsGenerating] = useState(false);

  // Debounced Auto-Save Logic (Runs every 3 seconds if data changes)
  useEffect(() => {
    if (!encounterId || !transcript) return;
    const delayDebounceFn = setTimeout(async () => {
      await fetch(`/api/encounters/${encounterId}/draft`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ transcript, soap_note: soapNote }),
      });
    }, 3000);

    return () => clearTimeout(delayDebounceFn);
  }, [transcript, soapNote, encounterId, token]);

  // Server-Sent Events (SSE) Processing Loop
  const triggerSoapGeneration = async () => {
    if (!transcript) return alert("Transcript can't be empty");
    setIsGenerating(true);
    setSoapNote({ subjective: '', objective: '', assessment: '', plan: '' });

    // 1. Establish the EventSource connection
    const response = await fetch(`/api/encounters/${encounterId}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ patient, transcript })
    });

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    // 2. Stream chunk reader loop
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      
      // SSE formats chunks with data: prefices. Let's parse incoming payload blocks
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.replace('data: ', ''));
            // Progressively append data incoming fields
            if (parsed.section === 'subjective') setSoapNote(prev => ({ ...prev, subjective: prev.subjective + parsed.text }));
            if (parsed.section === 'objective') setSoapNote(prev => ({ ...prev, objective: prev.objective + parsed.text }));
            if (parsed.section === 'assessment') setSoapNote(prev => ({ ...prev, assessment: prev.assessment + parsed.text }));
            if (parsed.section === 'plan') setSoapNote(prev => ({ ...prev, plan: prev.plan + parsed.text }));
          } catch (e) {
            // End of stream marker handling
          }
        }
      }
    }
    setIsGenerating(false);
  };

  const appendIcd10Code = (item: { code: string; description: string }) => {
    setSoapNote(prev => ({
      ...prev,
      assessment: prev.assessment + `\n- [ICD-10] ${item.code}: ${item.description}`
    }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 h-screen bg-white">
      {/* LEFT SIDE PANEL: Input and Clinical Metrics */}
      <div className="flex flex-col space-y-4 overflow-y-auto pr-2">
        <h2 className="text-lg font-bold text-slate-800 border-b pb-2">Encounter Inputs</h2>
        <div className="grid grid-cols-3 gap-2">
          <input type="text" placeholder="First Name" value={patient.firstName} onChange={e => setPatient({...patient, firstName: e.target.value})} className="border p-2 text-sm rounded"/>
          <input type="text" placeholder="Last Name" value={patient.lastName} onChange={e => setPatient({...patient, lastName: e.target.value})} className="border p-2 text-sm rounded"/>
          <input type="date" value={patient.dob} onChange={e => setPatient({...patient, dob: e.target.value})} className="border p-2 text-sm rounded"/>
        </div>
        
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Paste medical transcript or raw observational strings here..."
          className="w-full flex-grow h-64 border p-3 text-sm rounded font-sans focus:ring-1 focus:ring-slate-400 focus:outline-none"
        />

        <button 
          onClick={triggerSoapGeneration}
          disabled={isGenerating}
          className="bg-slate-800 hover:bg-slate-900 text-white font-medium py-2 rounded text-sm transition-all disabled:opacity-50"
        >
          {isGenerating ? 'Streaming Narrative Context...' : 'Generate Note'}
        </button>

        <Icd10SearchWidget onSelectCode={appendIcd10Code} />
      </div>

      {/* RIGHT SIDE PANEL: Live Progressive SOAP Modules */}
      <div className="flex flex-col space-y-4 bg-slate-50 border border-slate-200 rounded-lg p-5 overflow-y-auto">
        <h2 className="text-lg font-bold text-slate-800 border-b pb-2">Structured SOAP Record</h2>
        
        {['subjective', 'objective', 'assessment', 'plan'].map((section) => (
          <div key={section} className="bg-white p-3 rounded border border-slate-200 shadow-sm">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">{section}</h3>
            <textarea
              value={(soapNote as any)[section]}
              onChange={(e) => setSoapNote(prev => ({ ...prev, [section]: e.target.value }))}
              className="w-full text-sm text-slate-700 min-h-[80px] focus:outline-none resize-y"
              placeholder={`Waiting for ${section} streaming sequence...`}
            />
          </div>
        ))}
      </div>
    </div>
  );
};
