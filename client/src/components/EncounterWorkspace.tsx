import React, { useState } from 'react';

export default function EncounterWorkspace() {
  // 1. Manage form state for the patient data and raw transcript
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [transcript, setTranscript] = useState('');
  
  // UI and tracking states
  const [isSaving, setIsSaving] = useState(false);
  const [savedEncounterId, setSavedEncounterId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // 2. Form submission handler
  const handleSaveEncounter = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage('');

    // Quick validation guard before making the network request
    if (!firstName || !lastName || !dob || !transcript) {
      setErrorMessage('Please fill out all patient fields and provide a transcript.');
      setIsSaving(false);
      return;
    }

    try {
      // Pack the payload exactly as your Pydantic EncounterCreate schema expects
      const payload = {
        patient: {
          first_name: firstName,
          last_name: lastName,
          dob: dob
        },
        transcript: transcript,
        template_id: null // Fallback to null or add a default configuration selector later
      };

      // Issue the request using the Vite local development proxy routing path
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

      // Success: Capture your relational transaction metrics
      setSavedEncounterId(data.encounter_id);
      alert(`Success! Saved Encounter ID: ${data.encounter_id} (Version: ${data.version})`);
      
    } catch (err) {
      console.error('Save error:', err);
      setErrorMessage(err.message || 'Network connectivity error.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto bg-white shadow-md rounded-md mt-6">
      <h2 className="text-xl font-bold mb-4 text-slate-800">New Clinical Encounter</h2>
      
      {errorMessage && (
        <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-md">
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSaveEncounter} className="space-y-4">
        {/* Patient Metadata Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">First Name</label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="John"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Last Name</label>
            <input
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
            <input
              type="date"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Clinical Notes Workspace Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Encounter Transcript / Observations</label>
          <textarea
            rows={6}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            className="mt-1 block w-full p-2 border border-gray-300 rounded-md shadow-sm font-sans focus:ring-blue-500 focus:border-blue-500"
            placeholder="Patient presents with a 3-day history of scratchy throat, worsening dry cough..."
          />
        </div>

        {/* Action Button Segment */}
        <div className="flex justify-between items-center pt-2">
          {savedEncounterId && (
            <span className="text-xs text-green-600 font-medium">
              Active Record: ID #{savedEncounterId}
            </span>
          )}
          <button
            type="submit"
            disabled={isSaving}
            className={`ml-auto px-4 py-2 text-white font-medium rounded-md shadow-sm ${
              isSaving ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isSaving ? 'Saving to Database...' : 'Save Initial Encounter'}
          </button>
        </div>
      </form>
    </div>
  );
}
