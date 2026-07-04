
import { AuthProvider, useAuth } from '../context/AuthContext';
import { useState } from 'react';

const LoginView = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid clinical credentials');
      }

      const data = await response.json();
      // Expects: { access_token: "...", user: { email: "...", role: "Provider" } }
      login(data.access_token, data.user);
    } catch (err) {
      setError(err.message || 'Authentication failed server-side');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-md">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-bold tracking-tight text-slate-900">AI Clinical Scribe</h1>
          <p className="text-xs text-slate-500 mt-1">Physician Portal Secure Access</p>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-600">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
              Clinical Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dr.smith@scribe.com"
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-slate-800 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-900 disabled:opacity-50"
          >
            {loading ? 'Verifying Session...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginView;
