import React, { useEffect, useState } from 'react';
import { fileService, FileData } from '../../services/api/files';
import { FiUpload, FiTrash2, FiRefreshCw } from 'react-icons/fi';

const Files: React.FC = () => {
  const [files, setFiles] = useState<FileData[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const res = await fileService.listFiles();
      if (res.success) {
        setFiles(res.data.files);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
    const interval = setInterval(loadFiles, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setUploading(true);
    setError(null);
    try {
      await fileService.uploadFile(file);
      await loadFiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    try {
      await fileService.deleteFile(id);
      await loadFiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Delete failed');
    }
  };

  const handleReprocess = async (id: string) => {
    try {
      await fileService.reprocessFile(id);
      await loadFiles();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reprocess failed');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Files & Documents</h1>
      
      {error && (
        <div className="bg-red-100 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="mb-6 flex items-center">
        <label className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded cursor-pointer flex items-center shadow">
          <FiUpload className="mr-2" />
          {uploading ? 'Uploading...' : 'Upload File'}
          <input type="file" className="hidden" accept=".pdf,.docx,.xlsx,.csv,.pptx,.txt,.md,.png,.jpg,.jpeg,.webp" onChange={handleUpload} disabled={uploading} />
        </label>
        <p className="text-gray-500 text-sm ml-4">
          Supported: PDF, DOCX, XLSX, CSV, PPTX, TXT, Images (PNG, JPG, WEBP)
        </p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Filename</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {files.map(file => (
              <tr key={file.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{file.filename}</div>
                  {file.error_message && (
                    <div className="text-xs text-red-500">{file.error_message}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                    ${file.status === 'READY' ? 'bg-green-100 text-green-800' : 
                      file.status === 'FAILED' ? 'bg-red-100 text-red-800' : 
                      'bg-yellow-100 text-yellow-800'}`}>
                    {file.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {(file.size_bytes / 1024 / 1024).toFixed(2)} MB
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium flex gap-2">
                  <button onClick={() => handleReprocess(file.id)} className="text-indigo-600 hover:text-indigo-900" title="Reprocess">
                    <FiRefreshCw />
                  </button>
                  <button onClick={() => handleDelete(file.id)} className="text-red-600 hover:text-red-900" title="Delete">
                    <FiTrash2 />
                  </button>
                </td>
              </tr>
            ))}
            {files.length === 0 && !loading && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                  No files uploaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Files;
