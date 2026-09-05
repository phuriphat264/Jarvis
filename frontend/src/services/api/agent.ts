import { api } from './index';

export const agentService = {
  createTask: async (request: string, conversationId?: number, clientRequestId?: string, agentType: string = 'general', documentId?: string) => {
    const res = await api.post('/agent/tasks', {
      request,
      conversation_id: conversationId,
      client_request_id: clientRequestId,
      agent_type: agentType,
      document_id: documentId
    });
    return res.data;
  },
  
  getTask: async (taskId: number) => {
    const res = await api.get(`/agent/tasks/${taskId}`);
    return res.data;
  },
  
  cancelTask: async (taskId: number) => {
    const res = await api.post(`/agent/tasks/${taskId}/cancel`);
    return res.data;
  }
};
