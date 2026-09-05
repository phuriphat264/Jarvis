import { create } from 'zustand';
import { memoryService, Memory } from '../services/api/memories';

interface MemoryState {
  memories: Memory[];
  loading: boolean;
  error: string | null;

  fetchMemories: () => Promise<void>;
  searchMemories: (query: string) => Promise<void>;
  createMemory: (content: string, type: string) => Promise<void>;
  updateMemory: (id: number, data: Partial<Memory>) => Promise<void>;
  deleteMemory: (id: number) => Promise<void>;
}

export const useMemoryStore = create<MemoryState>((set, get) => ({
  memories: [],
  loading: false,
  error: null,

  fetchMemories: async () => {
    set({ loading: true, error: null });
    try {
      const data = await memoryService.getMemories();
      set({ memories: data, loading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch memories', loading: false });
    }
  },

  searchMemories: async (query: string) => {
    if (!query.trim()) {
      return get().fetchMemories();
    }
    set({ loading: true, error: null });
    try {
      const data = await memoryService.searchMemories(query);
      set({ memories: data, loading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to search memories', loading: false });
    }
  },

  createMemory: async (content, type) => {
    try {
      const newMem = await memoryService.createMemory({ content, memory_type: type });
      set(state => ({ memories: [newMem, ...state.memories] }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to create memory' });
    }
  },

  updateMemory: async (id, data) => {
    try {
      const updated = await memoryService.updateMemory(id, data);
      set(state => ({
        memories: state.memories.map(m => m.id === id ? updated : m)
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to update memory' });
    }
  },

  deleteMemory: async (id) => {
    try {
      await memoryService.deleteMemory(id);
      set(state => ({
        memories: state.memories.filter(m => m.id !== id)
      }));
    } catch (err: any) {
      set({ error: err.message || 'Failed to delete memory' });
    }
  }
}));
