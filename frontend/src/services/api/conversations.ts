import apiClient from './client';

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  sequence: number;
}

export interface Conversation {
  id: number;
  title: string;
  status: string;
  created_at: string;
  updated_at?: string;
  last_message_at?: string;
}

export interface PaginatedMessages {
  data: Message[];
  has_more: boolean;
  next_cursor: number | null;
}

export const conversationService = {
  getConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get('/api/v1/conversations/');
    return response.data;
  },

  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await apiClient.post('/api/v1/conversations/', { title });
    return response.data;
  },

  updateConversation: async (id: number, updates: { title?: string, status?: string }): Promise<Conversation> => {
    const response = await apiClient.patch(`/api/v1/conversations/${id}`, updates);
    return response.data;
  },

  deleteConversation: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/conversations/${id}`);
  },

  getMessages: async (conversationId: number, limit = 50, before?: number | null): Promise<PaginatedMessages> => {
    let url = `/api/v1/conversations/${conversationId}/messages?limit=${limit}`;
    if (before) {
      url += `&before=${before}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  },

  sendMessage: async (conversationId: number, content: string, clientRequestId?: string, documentId?: string) => {
    const response = await apiClient.post(`/api/v1/conversations/${conversationId}/messages`, { 
      content,
      client_request_id: clientRequestId,
      document_id: documentId
    });
    return response.data;
  }
};
