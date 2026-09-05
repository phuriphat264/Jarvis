import { create } from 'zustand';
import { conversationService, Conversation } from '../services/api/conversations';

interface ConversationState {
  conversations: Conversation[];
  activeConvId: number | null;
  loading: boolean;
  error: string | null;
  
  fetchConversations: () => Promise<void>;
  setActiveConvId: (id: number | null) => void;
  createConversation: (title?: string) => Promise<Conversation | null>;
  renameConversation: (id: number, title: string) => Promise<void>;
  archiveConversation: (id: number) => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  activeConvId: null,
  loading: false,
  error: null,

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const data = await conversationService.getConversations();
      set({ conversations: data, loading: false });
      
      const { activeConvId } = get();
      if (data.length > 0 && !activeConvId) {
        set({ activeConvId: data[0].id });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch conversations', loading: false });
    }
  },

  setActiveConvId: (id) => set({ activeConvId: id }),

  createConversation: async (title) => {
    try {
      const newConv = await conversationService.createConversation(title);
      set(state => ({
        conversations: [newConv, ...state.conversations],
        activeConvId: newConv.id
      }));
      return newConv;
    } catch (err: any) {
      set({ error: err.message || 'Failed to create conversation' });
      return null;
    }
  },

  renameConversation: async (id, title) => {
    try {
      const updated = await conversationService.updateConversation(id, { title });
      set(state => ({
        conversations: state.conversations.map(c => c.id === id ? updated : c)
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to rename conversation' });
    }
  },

  archiveConversation: async (id) => {
    try {
      const updated = await conversationService.updateConversation(id, { status: 'archived' });
      set(state => ({
        conversations: state.conversations.map(c => c.id === id ? updated : c)
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to archive conversation' });
    }
  },

  deleteConversation: async (id) => {
    try {
      await conversationService.deleteConversation(id);
      set(state => ({
        conversations: state.conversations.filter(c => c.id !== id),
        activeConvId: state.activeConvId === id ? null : state.activeConvId
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to delete conversation' });
    }
  }
}));
