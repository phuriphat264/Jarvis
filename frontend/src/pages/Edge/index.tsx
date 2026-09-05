import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const EdgeNodes: React.FC = () => {
  const [nodes, setNodes] = useState<any[]>([]);

  useEffect(() => {
    fetchNodes();
  }, []);

  const fetchNodes = async () => {
    try {
      const res = await api.get('/api/v1/edge/nodes');
      setNodes(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  const enrollNode = async () => {
    try {
      const res = await api.post('/api/v1/edge/enrollments');
      alert(`Enrollment Code: ${res.data.data.enrollment_code}\nExpires: ${res.data.data.expires_at}`);
    } catch (err) {
      console.error(err);
    }
  };

  const revokeNode = async (nodeId: string) => {
    try {
      await api.post(`/api/v1/edge/nodes/${nodeId}/revoke`);
      fetchNodes();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-light">JARVIS Edge Nodes</h1>
        <button onClick={enrollNode} className="bg-blue-600 text-white px-4 py-2 rounded shadow-sm hover:bg-blue-700">Generate Enrollment Code</button>
      </div>

      {nodes.length === 0 ? (
        <div className="text-center p-12 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500">No Edge Nodes registered yet. Deploy JARVIS on a Raspberry Pi to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {nodes.map(node => (
            <div key={node.id} className="border border-gray-200 p-6 rounded-xl bg-white shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-lg">{node.name}</h3>
                    <p className="text-xs text-gray-500 font-mono">{node.node_id}</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${node.status === 'ONLINE' ? 'bg-green-100 text-green-700' : node.status === 'REVOKED' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                    {node.status}
                  </span>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg text-sm border border-gray-100 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Hardware:</span>
                    <span className="font-mono text-gray-800">{node.hardware_info?.arch || 'Raspberry Pi 4'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">CPU Usage:</span>
                    <span className="text-gray-800">{node.hardware_info?.cpu || '0'}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Memory:</span>
                    <span className="text-gray-800">{node.hardware_info?.ram || '0'}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Temperature:</span>
                    <span className="text-gray-800">{node.hardware_info?.temp || '0'}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Sync:</span>
                    <span className="text-gray-800">{node.last_seen ? new Date(node.last_seen).toLocaleString() : 'Never'}</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex gap-2">
                <button className="flex-1 bg-gray-100 hover:bg-gray-200 py-2 rounded text-sm text-gray-700 font-medium">View Logs</button>
                {node.status !== 'REVOKED' && (
                  <button onClick={() => revokeNode(node.node_id)} className="flex-1 text-red-600 hover:bg-red-50 py-2 rounded text-sm font-medium border border-transparent hover:border-red-100">Revoke Access</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EdgeNodes;
