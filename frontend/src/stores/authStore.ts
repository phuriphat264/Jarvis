import { create } from 'zustand';

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('jarvis_token'),
  setToken: (token: string) => {
    localStorage.setItem('jarvis_token', token);
    set({ token });
  },
  logout: () => {
    localStorage.removeItem('jarvis_token');
    set({ token: null });
  },
}));
