import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const Agents: React.FC = () => {
  const [runs, setRuns] = useState<any[]>([]);
  const [registry, setRegistry] = useState<any[]>([]);
  const [selectedRun, setSelectedRun] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const runRes = await api.get('/api/v1/agent/runs');
      setRuns(runRes.data.data);
      const regRes = await api.get('/api/v1/agent/registry');
      setRegistry(regRes.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  const viewRun = async (id: number) => {
    try {
      const res = await api.get(`/api/v1/agent/runs/${id}`);
      setSelectedRun(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto flex gap-6">
      <div className="w-1/3">
        <h1 className="text-3xl font-light mb-6">Agent Registry</h1>
        <div className="space-y-4 mb-8">
          {registry.map(agent => (
            <div key={agent.name} className="p-4 border border-gray-100 rounded-lg shadow-sm bg-white">
              <h3 className="font-semibold text-lg capitalize">{agent.name}</h3>
              <p className="text-sm text-gray-600 mb-2">{agent.description}</p>
              <div className="flex gap-2 flex-wrap">
                {agent.capabilities.map((c: string) => (
                  <span key={c} className="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded">{c}</span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <h1 className="text-3xl font-light mb-6">Recent Runs</h1>
        <div className="space-y-2">
          {runs.map(run => (
            <div key={run.id} onClick={() => viewRun(run.id)} className={`p-4 border rounded cursor-pointer ${selectedRun?.id === run.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}>
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-semibold px-2 py-1 bg-gray-100 rounded">{run.route_type}</span>
                <span className={`text-xs px-2 py-1 rounded ${run.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{run.status}</span>
              </div>
              <p className="text-sm line-clamp-2 text-gray-800">{run.request}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="w-2/3">
        {selectedRun ? (
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm min-h-full">
            <h2 className="text-2xl font-semibold mb-4">Run #{selectedRun.id} Details</h2>
            <div className="mb-6">
              <h3 className="font-semibold text-gray-600 uppercase text-xs mb-1">Request</h3>
              <p className="text-lg">{selectedRun.request}</p>
            </div>
            
            <div className="mb-6">
              <h3 className="font-semibold text-gray-600 uppercase text-xs mb-2">Execution Plan</h3>
              {selectedRun.plan ? (
                <div className="space-y-3">
                  <p className="text-sm text-gray-500 italic mb-2">{selectedRun.plan.task_summary}</p>
                  {selectedRun.plan.steps?.map((step: any) => (
                    <div key={step.step_id} className="p-3 bg-gray-50 border border-gray-100 rounded flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
                        {step.step_id.replace('step_', '')}
                      </div>
                      <div>
                        <p className="text-sm font-semibold capitalize text-blue-900 mb-1">{step.agent} Agent</p>
                        <p className="text-sm text-gray-700">{step.objective}</p>
                        {step.depends_on?.length > 0 && (
                          <p className="text-xs text-gray-500 mt-2">Depends on: {step.depends_on.join(', ')}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No plan available (likely Simple Chat or Single Specialist)</p>
              )}
            </div>

            <div>
              <h3 className="font-semibold text-gray-600 uppercase text-xs mb-2">Final Results</h3>
              <pre className="bg-gray-50 p-4 rounded text-xs overflow-auto text-gray-800 border border-gray-200 whitespace-pre-wrap">
                {selectedRun.final_result || "No results yet"}
              </pre>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 shadow-sm h-full flex items-center justify-center text-gray-400">
            Select a run to view details
          </div>
        )}
      </div>
    </div>
  );
};

export default Agents;
