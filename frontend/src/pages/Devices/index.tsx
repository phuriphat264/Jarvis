import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const Devices: React.FC = () => {
  const [devices, setDevices] = useState<any[]>([]);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const res = await api.get('/api/v1/iot/devices');
      setDevices(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'light': return '💡';
      case 'sensor': return '🌡';
      case 'plug': return '🔌';
      case 'camera': return '📷';
      default: return '🎛';
    }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-light">Smart Home Devices</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded shadow-sm hover:bg-blue-700">Add Device</button>
      </div>

      {devices.length === 0 ? (
        <div className="text-center p-12 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500">No IoT devices registered yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {devices.map(device => (
            <div key={device.id} className="border border-gray-200 p-6 rounded-xl bg-white shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getIcon(device.type)}</span>
                    <div>
                      <h3 className="font-semibold text-lg">{device.name}</h3>
                      <p className="text-xs text-gray-500">{device.room || 'No Room Assigned'}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${device.state.online ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {device.state.online ? 'Online' : 'Offline'}
                  </span>
                </div>
                
                <div className="mt-4 bg-gray-50 p-3 rounded-lg text-sm border border-gray-100">
                  {device.type === 'light' || device.type === 'plug' ? (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Power:</span>
                      <span className="font-semibold">{device.state.power ? 'ON' : 'OFF'}</span>
                    </div>
                  ) : null}
                  {device.type === 'sensor' && device.state.temperature ? (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Temp:</span>
                      <span className="font-semibold">{device.state.temperature}°C</span>
                    </div>
                  ) : null}
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                {/* Manual overrides in UI will trigger backend Tools via API in real app */}
                {(device.capabilities?.power) && (
                  <>
                    <button className="flex-1 bg-gray-100 hover:bg-gray-200 py-1 rounded text-sm text-gray-700">Toggle</button>
                  </>
                )}
                <button className="flex-1 text-blue-600 hover:bg-blue-50 py-1 rounded text-sm border border-transparent hover:border-blue-100">Details</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Devices;
