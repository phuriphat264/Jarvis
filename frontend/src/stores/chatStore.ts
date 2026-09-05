import { create } from 'zustand';
import { conversationService, Message } from '../services/api/conversations';
import { agentService } from '../services/api/agent';

interface ChatState {
  messages: Message[];
  hasMore: boolean;
  nextCursor: number | null;
  status: 'IDLE' | 'LOADING' | 'GENERATING' | 'ERROR' | 'AGENT_RUNNING';
  agentTaskStatus: any | null; // Tracks step status
  
  fetchMessages: (conversationId: number, limit?: number) => Promise<void>;
  loadMoreMessages: (conversationId: number, limit?: number) => Promise<void>;
  sendMessage: (conversationId: number, content: string, documentId?: string) => Promise<void>;
  startAgentTask: (conversationId: number, content: string, agentType?: string, documentId?: string) => Promise<void>;
  pollAgentTask: (taskId: number, conversationId: number) => Promise<void>;
  reset: () => void;
}

const generateRequestId = () => Math.random().toString(36).substring(2, 15);

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  hasMore: false,
  nextCursor: null,
  status: 'IDLE',
  agentTaskStatus: null,

  fetchMessages: async (conversationId, limit = 50) => {
    set({ status: 'LOADING' });
    try {
      const data = await conversationService.getMessages(conversationId, limit);
      set({ 
        messages: data.data,
        hasMore: data.has_more,
        nextCursor: data.next_cursor,
        status: 'IDLE'
      });
    } catch (err) {
      set({ status: 'ERROR' });
    }
  },

  loadMoreMessages: async (conversationId, limit = 50) => {
    const { nextCursor, hasMore, messages } = get();
    if (!hasMore || nextCursor === null) return;
    
    try {
      const data = await conversationService.getMessages(conversationId, limit, nextCursor);
      set({
        messages: [...data.data, ...messages], // prepend older messages
        hasMore: data.has_more,
        nextCursor: data.next_cursor,
      });
    } catch (err) {
      console.error('Failed to load more messages', err);
    }
  },

  sendMessage: async (conversationId, content, documentId) => {
    const tempId = Date.now();
    const requestId = generateRequestId();
    
    // Optimistic insert
    const tempMsg: Message = {
      id: tempId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      sequence: 999999 // temp
    };
    
    set(state => ({
      messages: [...state.messages, tempMsg],
      status: 'GENERATING'
    }));

    try {
      const res = await conversationService.sendMessage(conversationId, content, requestId, documentId);
      if (res.success) {
        set(state => {
          const filtered = state.messages.filter(m => m.id !== tempId);
          return {
            messages: [...filtered, res.data.user_message, res.data.assistant_message],
            status: 'IDLE'
          };
        });
      }
    } catch (err) {
      set({ status: 'ERROR' });
    }
  },

  startAgentTask: async (conversationId, content, agentType = 'general', documentId) => {
    const tempId = Date.now();
    const requestId = generateRequestId();
    
    // Opt-insert user message
    const tempMsg: Message = {
      id: tempId, role: 'user', content, created_at: new Date().toISOString(), sequence: 999999
    };
    
    set(state => ({
      messages: [...state.messages, tempMsg],
      status: 'AGENT_RUNNING',
      agentTaskStatus: null
    }));
    
    try {
      const res = await agentService.createTask(content, conversationId, requestId, agentType, documentId);
      if (res.success) {
        // Start polling
        get().pollAgentTask(res.data.task_id, conversationId);
      }
    } catch (err) {
      set({ status: 'ERROR' });
    }
  },
  
  pollAgentTask: async (taskId, conversationId) => {
    const checkStatus = async () => {
      try {
        const res = await agentService.getTask(taskId);
        if (res.success) {
          const task = res.data;
          set({ agentTaskStatus: task });
          
          if (task.status === 'COMPLETED' || task.status === 'FAILED' || task.status === 'CANCELLED' || task.status === 'LIMIT_REACHED' || task.status === 'TIMEOUT') {
             // Fetch final messages to get the assistant response
             await get().fetchMessages(conversationId);
             set({ status: 'IDLE', agentTaskStatus: null });
             return;
          }
          
          // Poll again in 2 seconds
          setTimeout(checkStatus, 2000);
        }
      } catch (err) {
        set({ status: 'ERROR' });
      }
    };
    
    setTimeout(checkStatus, 1000);
  },

  reset: () => set({ messages: [], hasMore: false, nextCursor: null, status: 'IDLE', agentTaskStatus: null })
}));
