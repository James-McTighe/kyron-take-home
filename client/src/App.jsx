import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { EncounterWorkspace } from './components/EncounterWorkspace';
import LoginView from './components/Login';


// Main Routing Controller that watches the Auth Context
const NavigationController = () => {
  const { token, user, logout } = useAuth();

  // If there's no valid session, isolate the user inside the Login screen
  if (!token) {
    return <LoginView />;
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* High-Trust Top Navigation Header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3 shadow-sm z-10">
        <div className="flex items-center space-x-3">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-bold text-slate-800 tracking-tight">Scribe Workstation</span>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-2xs font-mono font-bold text-slate-500 uppercase tracking-wide">
            {user?.role}
          </span>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-xs font-medium text-slate-600 font-mono">{user?.email}</span>
          <button
            onClick={logout}
            className="rounded border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Workspace Display Area */}
      <main className="flex-1 overflow-hidden">
        <EncounterWorkspace />
      </main>
    </div>
  );
};

// Root Context Wrapper
export default function App() {
  return (
    <AuthProvider>
      <NavigationController />
    </AuthProvider>
  );
}
