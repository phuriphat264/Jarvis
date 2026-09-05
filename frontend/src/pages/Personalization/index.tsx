import React, { useEffect, useState, useCallback } from 'react';
import api from '../../services/api';

// ─────────────── Types ───────────────
interface Preference {
  id: number;
  key: string;
  value: string;
  scope: string;
  source: string;
  confidence: number;
  priority: number;
  created_at: string;
}

interface Suggestion {
  id: number;
  key: string;
  value: string;
  confidence: number;
  evidence_count: number;
  created_at: string;
}

// ─────────────── Helpers ───────────────
const sourceColor = (source: string) =>
  source === 'USER_EXPLICIT'
    ? 'bg-blue-100 text-blue-700'
    : 'bg-purple-100 text-purple-700';

const confidenceBar = (conf: number) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 bg-gray-200 rounded-full h-1.5">
      <div
        className="bg-blue-500 h-1.5 rounded-full"
        style={{ width: `${Math.round(conf * 100)}%` }}
      />
    </div>
    <span className="text-xs text-gray-500 w-8 text-right">{Math.round(conf * 100)}%</span>
  </div>
);

// ─────────────── Main Component ───────────────
const PersonalizationPage: React.FC = () => {
  const [profile, setProfile] = useState<any>({});
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [resetConfirm, setResetConfirm] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const flash = (msg: string) => {
    setStatusMsg(msg);
    setTimeout(() => setStatusMsg(''), 3000);
  };

  const load = useCallback(async () => {
    try {
      const [profRes, prefRes, sugRes] = await Promise.all([
        api.get('/api/v1/personalization/profile'),
        api.get('/api/v1/personalization/preferences'),
        api.get('/api/v1/personalization/suggestions'),
      ]);
      setProfile(profRes.data.data || {});
      setPreferences(prefRes.data.data || []);
      setSuggestions(sugRes.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const createPref = async () => {
    if (!newKey.trim() || !newValue.trim()) return;
    await api.post('/api/v1/personalization/preferences', { key: newKey.trim(), value: newValue.trim() });
    setNewKey('');
    setNewValue('');
    flash('Preference saved.');
    load();
  };

  const deletePref = async (id: number) => {
    await api.delete(`/api/v1/personalization/preferences/${id}`);
    flash('Preference removed.');
    load();
  };

  const approveSuggestion = async (id: number) => {
    await api.post(`/api/v1/personalization/suggestions/${id}/approve`);
    flash('Suggestion approved and applied!');
    load();
  };

  const rejectSuggestion = async (id: number) => {
    await api.post(`/api/v1/personalization/suggestions/${id}/reject`);
    flash('Suggestion rejected.');
    load();
  };

  const resetLearned = async () => {
    const res = await api.post('/api/v1/personalization/reset');
    flash(`Reset ${res.data.data.archived_count} learned preferences.`);
    setResetConfirm(false);
    load();
  };

  if (loading) return <div className="p-8 text-gray-500">Loading personalization…</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-10">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-light">JARVIS Personalization</h1>
          <p className="text-sm text-gray-500 mt-1">
            Control how JARVIS behaves for you. Explicit settings always take priority over learned behavior.
          </p>
        </div>
        {statusMsg && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-2 rounded-lg text-sm">
            {statusMsg}
          </div>
        )}
      </div>

      {/* ── Current Profile ── */}
      {Object.keys(profile).length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Active Profile</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(profile).map(([section, vals]: any) =>
              Object.entries(vals).map(([field, value]: any) => (
                <div key={`${section}-${field}`} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
                  <p className="text-xs text-gray-400 uppercase tracking-wider">{section} · {field.replace(/_/g, ' ')}</p>
                  <p className="mt-1 font-semibold text-gray-800 capitalize">{value}</p>
                </div>
              ))
            )}
          </div>
        </section>
      )}

      {/* ── Learned Suggestions ── */}
      {suggestions.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-1">💡 JARVIS Learned Suggestions</h2>
          <p className="text-sm text-gray-500 mb-4">
            Based on your behavior, JARVIS suggests these defaults. Nothing is applied until you approve.
          </p>
          <div className="space-y-3">
            {suggestions.map(s => (
              <div key={s.id} className="bg-yellow-50 border border-yellow-200 p-4 rounded-xl flex justify-between items-center">
                <div className="flex-1">
                  <p className="font-medium text-gray-800">
                    Set <span className="font-mono text-blue-700">{s.key}</span> → <span className="font-mono text-green-700">{s.value}</span>
                  </p>
                  <div className="mt-1 max-w-48">{confidenceBar(s.confidence)}</div>
                  <p className="text-xs text-gray-400 mt-1">{s.evidence_count} observations</p>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => approveSuggestion(s.id)}
                    className="bg-green-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-green-700 transition"
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => rejectSuggestion(s.id)}
                    className="bg-white border border-gray-300 text-gray-600 px-3 py-1.5 rounded text-sm hover:bg-gray-50 transition"
                  >
                    Ignore
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── All Preferences ── */}
      <section>
        <h2 className="text-lg font-semibold mb-3">All Preferences</h2>
        {preferences.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 text-gray-400 p-6 rounded-xl text-center text-sm">
            No preferences set yet. Add one below.
          </div>
        ) : (
          <div className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
            {preferences.map(p => (
              <div key={p.id} className="flex items-center justify-between px-4 py-3 bg-white hover:bg-gray-50 transition">
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${sourceColor(p.source)}`}>
                    {p.source === 'USER_EXPLICIT' ? 'Explicit' : 'Learned'}
                  </span>
                  <span className="font-mono text-sm text-gray-700">{p.key}</span>
                  <span className="text-gray-400">→</span>
                  <span className="font-mono text-sm text-green-700">{p.value}</span>
                  {p.scope !== 'GLOBAL' && (
                    <span className="text-xs text-gray-400 italic">[{p.scope}]</span>
                  )}
                </div>
                <button
                  onClick={() => deletePref(p.id)}
                  className="text-xs text-red-400 hover:text-red-600 transition"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add new preference */}
        <div className="mt-4 flex gap-2">
          <input
            value={newKey}
            onChange={e => setNewKey(e.target.value)}
            placeholder="key (e.g. language)"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <input
            value={newValue}
            onChange={e => setNewValue(e.target.value)}
            placeholder="value (e.g. th)"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          <button
            onClick={createPref}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-700 transition"
          >
            Save
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Common keys: <code>language</code>, <code>response_length</code>, <code>tone</code>, <code>formatting</code>, <code>planning_style</code>
        </p>
      </section>

      {/* ── Privacy & Reset ── */}
      <section className="border-t pt-8">
        <h2 className="text-lg font-semibold mb-1 text-red-700">Privacy Controls</h2>
        <p className="text-sm text-gray-500 mb-4">
          Learned preferences are based on your interaction patterns (no raw content stored).
          You can reset them at any time. Explicit preferences are unaffected.
        </p>
        {!resetConfirm ? (
          <button
            onClick={() => setResetConfirm(true)}
            className="border border-red-300 text-red-600 px-4 py-2 rounded text-sm hover:bg-red-50 transition"
          >
            Reset All Learned Preferences
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="text-sm text-red-700 font-medium">Are you sure? This cannot be undone.</span>
            <button onClick={resetLearned} className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 transition">
              Yes, Reset
            </button>
            <button onClick={() => setResetConfirm(false)} className="text-sm text-gray-500 hover:underline">
              Cancel
            </button>
          </div>
        )}
      </section>
    </div>
  );
};

export default PersonalizationPage;
