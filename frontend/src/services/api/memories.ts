import apiClient from './client';

export interface Memory {
  id: number;
  user_id: number;
  content: string;
  memory_type: string;
  importance: number;
  confidence: number;
  source_type: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export const memoryService = {
  getMemories: async (): Promise<Memory[]> => {
    const response = await apiClient.get('/api/v1/memories/');
    return response.data;
  },

  searchMemories: async (query: string): Promise<Memory[]> => {
    const response = await apiClient.get(`/api/v1/memories/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  createMemory: async (data: { content: string, memory_type: string, importance?: number, confidence?: number }): Promise<Memory> => {
    const response = await apiClient.post('/api/v1/memories/', data);
    return response.data;
  },

  updateMemory: async (id: number, data: Partial<Memory>): Promise<Memory> => {
    const response = await apiClient.patch(`/api/v1/memories/${id}`, data);
    return response.data;
  },

  deleteMemory: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/memories/${id}`);
  }
};
