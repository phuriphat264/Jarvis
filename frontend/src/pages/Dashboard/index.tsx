import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const Dashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [world, setWorld] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await api.get('/api/v1/personal/dashboard');
        setData(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    const fetchIntelligence = async () => {
      try {
        const w = await api.get('/api/v1/intelligence/world');
        setWorld(w.data.data);
        const r = await api.get('/api/v1/intelligence/recommendations');
        setRecs(r.data.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchDashboard();
    fetchIntelligence();
  }, []);

  if (!data) return <div className="p-8">Loading Personal OS...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-light mb-8">Personal Command Center</h1>
      
      {/* Pending Actions Alert */}
      <div className="mb-6">
        <div className="bg-orange-50 border border-orange-200 p-4 rounded-xl shadow-sm">
          <h2 className="text-orange-800 font-semibold mb-2">Pending Confirmations</h2>
          <p className="text-sm text-orange-700">View and confirm pending actions via Settings &gt; Integrations or the CLI.</p>
        </div>
      </div>
      
      {/* Intelligence Widget (Phase 16) */}
      {recs.length > 0 && (
        <div className="mb-6">
          <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl shadow-sm flex justify-between items-center">
            <div>
              <h2 className="text-blue-800 font-semibold mb-1 flex items-center gap-2">
                <span>JARVIS Intelligence</span>
                <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">{recs.length} Notifications</span>
              </h2>
              <p className="text-sm text-blue-700">{recs[0].message}</p>
            </div>
            <a href="/intelligence" className="bg-white border border-blue-300 text-blue-700 px-4 py-2 rounded text-sm hover:bg-blue-50 transition">Review All</a>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Tasks & Reminders */}
        <div className="md:col-span-2 space-y-6">
          <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold mb-4">Today's Focus</h2>
            {data.overdue_tasks.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-red-500 mb-2">Overdue</h3>
                {data.overdue_tasks.map((t: any) => (
                  <div key={t.id} className="p-3 border-l-4 border-red-500 bg-red-50 mb-2 rounded-r">
                    <p className="text-sm">{t.title}</p>
                  </div>
                ))}
              </div>
            )}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 mb-2">Tasks</h3>
              {data.today_tasks.length === 0 ? (
                <p className="text-sm text-gray-400 italic">No tasks due today</p>
              ) : (
                data.today_tasks.map((t: any) => (
                  <div key={t.id} className="p-3 border-l-4 border-blue-500 bg-blue-50 mb-2 rounded-r flex justify-between">
                    <p className="text-sm">{t.title}</p>
                    <span className="text-xs text-blue-500">{new Date(t.due_at).toLocaleTimeString()}</span>
                  </div>
                ))
              )}
            </div>
          </section>
          
          <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold mb-4">Upcoming Reminders</h2>
            {data.upcoming_reminders.length === 0 ? (
                <p className="text-sm text-gray-400 italic">No upcoming reminders</p>
              ) : (
                data.upcoming_reminders.map((r: any) => (
                  <div key={r.id} className="p-3 border-l-4 border-yellow-500 bg-yellow-50 mb-2 rounded-r flex justify-between">
                    <p className="text-sm">{r.title}</p>
                    <span className="text-xs text-yellow-600">{new Date(r.remind_at).toLocaleString()}</span>
                  </div>
                ))
            )}
          </section>
          {/* Smart Home Summary */}
          <div className="bg-white border border-gray-100 rounded-xl p-6 shadow-sm mt-6">
            <h2 className="font-semibold text-gray-800 mb-4 flex justify-between">
              Smart Home 
              <a href="/devices" className="text-blue-500 text-sm font-normal">View Devices &rarr;</a>
            </h2>
            <div className="flex gap-4">
              <div className="flex-1 bg-green-50 p-4 rounded-lg flex items-center justify-between border border-green-100">
                <span className="text-green-800">Online</span>
                <span className="font-bold text-green-700">All</span>
              </div>
              <div className="flex-1 bg-gray-50 p-4 rounded-lg flex items-center justify-between border border-gray-100">
                <span className="text-gray-600">Active Automations</span>
                <span className="font-bold text-gray-700">0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Projects, Goals, Events */}
        <div className="space-y-6">
          <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold mb-4">Today's Schedule</h2>
            {data.today_events.length === 0 ? (
                <p className="text-sm text-gray-400 italic">Free day</p>
              ) : (
                data.today_events.map((e: any) => (
                  <div key={e.id} className="p-3 border border-gray-100 mb-2 rounded">
                    <p className="text-sm font-medium">{e.title}</p>
                    <p className="text-xs text-gray-500">{new Date(e.start_at).toLocaleTimeString()} - {new Date(e.end_at).toLocaleTimeString()}</p>
                  </div>
                ))
            )}
          </section>
          
          <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold mb-4">Active Projects</h2>
            {data.active_projects.length === 0 ? (
                <p className="text-sm text-gray-400 italic">No active projects</p>
              ) : (
                data.active_projects.map((p: any) => (
                  <div key={p.id} className="mb-4">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium">{p.name}</span>
                    </div>
                  </div>
                ))
            )}
          </section>
          
          <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold mb-4">Active Goals</h2>
            {data.active_goals.length === 0 ? (
                <p className="text-sm text-gray-400 italic">No active goals</p>
              ) : (
                data.active_goals.map((g: any) => (
                  <div key={g.id} className="mb-4">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium">{g.title}</span>
                      <span className="text-sm text-gray-500">{g.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${g.progress}%` }}></div>
                    </div>
                  </div>
                ))
            )}
          </section>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
