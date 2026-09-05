import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const IntelligenceDashboard: React.FC = () => {
  const [world, setWorld] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  useEffect(() => {
    fetchWorld();
    fetchRecommendations();
  }, []);

  const fetchWorld = async () => {
    try {
      const res = await api.get('/api/v1/intelligence/world');
      setWorld(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const res = await api.get('/api/v1/intelligence/recommendations');
      setRecommendations(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  const dismissRec = async (id: number) => {
    try {
      await api.post(`/api/v1/intelligence/recommendations/${id}/dismiss`);
      fetchRecommendations();
    } catch (err) {
      console.error(err);
    }
  };

  if (!world) return <div className="p-8">Loading Intelligence...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <h1 className="text-3xl font-light">Intelligence & World Model</h1>

      {/* Recommendations */}
      <section>
        <h2 className="text-xl font-medium mb-4 flex items-center gap-2">
          <span>Proactive Attention</span>
          <span className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">{recommendations.length}</span>
        </h2>
        
        {recommendations.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 text-gray-500 p-6 rounded-xl text-center">
            All clear. No urgent items need your attention right now.
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map(rec => (
              <div key={rec.id} className="bg-yellow-50 border border-yellow-200 p-4 rounded-xl flex justify-between items-center shadow-sm">
                <div>
                  <span className="text-xs font-semibold text-yellow-800 uppercase tracking-wider">{rec.type}</span>
                  <p className="mt-1 font-medium text-gray-800">{rec.message}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => dismissRec(rec.id)} className="text-sm bg-white border border-gray-300 text-gray-600 px-3 py-1 rounded hover:bg-gray-50 transition">Dismiss</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Current Situations */}
        <section className="bg-white border border-gray-200 p-6 rounded-xl shadow-sm">
          <h2 className="text-xl font-medium mb-4">Current Situations</h2>
          {world.situations.length === 0 ? (
            <p className="text-gray-500">NORMAL</p>
          ) : (
            <ul className="space-y-3">
              {world.situations.map((sit: any, idx: number) => (
                <li key={idx} className="flex justify-between items-center bg-gray-50 p-3 rounded border border-gray-100">
                  <span className="font-mono text-sm text-gray-700">{sit.type}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${sit.severity === 'HIGH' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}`}>
                    {sit.severity}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Home & Edge State */}
        <section className="bg-white border border-gray-200 p-6 rounded-xl shadow-sm">
          <h2 className="text-xl font-medium mb-4">Environment Context</h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500 mb-1">IoT Devices</p>
              <div className="flex gap-4">
                <div className="bg-green-50 text-green-700 px-4 py-2 rounded-lg border border-green-100 flex-1 text-center">
                  <span className="block text-2xl font-bold">{world.home_state?.online_count || 0}</span>
                  <span className="text-xs">Online</span>
                </div>
                <div className="bg-gray-50 text-gray-700 px-4 py-2 rounded-lg border border-gray-200 flex-1 text-center">
                  <span className="block text-2xl font-bold">{world.home_state?.offline_count || 0}</span>
                  <span className="text-xs">Offline</span>
                </div>
              </div>
            </div>
            
            <div>
              <p className="text-sm text-gray-500 mb-1">Edge Nodes</p>
              <div className="bg-blue-50 text-blue-700 px-4 py-2 rounded-lg border border-blue-100 text-center">
                <span className="block text-2xl font-bold">{world.edge_state?.online_count || 0}</span>
                <span className="text-xs">Active Nodes</span>
              </div>
            </div>
          </div>
        </section>
      </div>

    </div>
  );
};

export default IntelligenceDashboard;
