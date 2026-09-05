import { api } from './index';

export interface FileData {
  id: string;
  filename: string;
  status: string;
  size_bytes: number;
  created_at: string;
  error_message?: string;
}

export const fileService = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return res.data;
  },
  
  listFiles: async () => {
    const res = await api.get('/files');
    return res.data;
  },
  
  deleteFile: async (id: string) => {
    const res = await api.delete(`/files/${id}`);
    return res.data;
  },
  
  reprocessFile: async (id: string) => {
    const res = await api.post(`/files/${id}/reprocess`);
    return res.data;
  }
};
