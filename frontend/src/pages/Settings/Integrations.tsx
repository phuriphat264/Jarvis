import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const Integrations: React.FC = () => {
  const [connections, setConnections] = useState<any[]>([]);
  const [pendingActions, setPendingActions] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const connRes = await api.get('/api/v1/integrations');
      setConnections(connRes.data);
      const pendingRes = await api.get('/api/v1/actions/pending');
      setPendingActions(pendingRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  const connect = async (provider: string) => {
    try {
      const res = await api.post(`/api/v1/integrations/${provider}/connect`);
      window.location.href = res.data.url;
    } catch (err) {
      console.error(err);
    }
  };

  const disconnect = async (provider: string) => {
    try {
      await api.post(`/api/v1/integrations/${provider}/disconnect`);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const confirmAction = async (id: number) => {
    try {
      await api.post(`/api/v1/actions/${id}/confirm`);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const rejectAction = async (id: number) => {
    try {
      await api.post(`/api/v1/actions/${id}/reject`);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const providers = ["google_calendar", "gmail", "line", "telegram", "webhook"];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-light mb-8">Integration Settings</h1>
      
      {pendingActions.length > 0 && (
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-4 text-orange-600">Pending Confirmations</h2>
          <div className="space-y-4">
            {pendingActions.map(action => (
              <div key={action.id} className="border border-orange-200 bg-orange-50 p-4 rounded-xl flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-orange-900">{action.description}</h3>
                  <pre className="text-xs text-orange-700 mt-1 bg-orange-100 p-2 rounded">{JSON.stringify(action.arguments, null, 2)}</pre>
                </div>
                <div className="space-x-2">
                  <button onClick={() => rejectAction(action.id)} className="px-4 py-2 bg-white text-orange-600 border border-orange-200 rounded shadow-sm hover:bg-orange-100">Reject</button>
                  <button onClick={() => confirmAction(action.id)} className="px-4 py-2 bg-orange-600 text-white rounded shadow-sm hover:bg-orange-700">Confirm</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <h2 className="text-xl font-semibold mb-4">Connected Services</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {providers.map(provider => {
          const conn = connections.find(c => c.provider === provider);
          return (
            <div key={provider} className="border p-6 rounded-xl bg-white shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-bold capitalize">{provider.replace('_', ' ')}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full ${conn ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {conn ? 'Connected' : 'Not Connected'}
                  </span>
                </div>
                {conn && <p className="text-sm text-gray-500 mb-4">Last synced: {new Date(conn.created_at).toLocaleDateString()}</p>}
              </div>
              <div>
                {conn ? (
                  <button onClick={() => disconnect(provider)} className="text-red-500 text-sm hover:underline">Disconnect</button>
                ) : (
                  <button onClick={() => connect(provider)} className="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg text-sm w-full font-medium hover:bg-blue-100">Connect</button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  );
};

export default Integrations;
