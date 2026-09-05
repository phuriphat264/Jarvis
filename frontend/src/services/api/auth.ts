import apiClient from './client';

export const authService = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 expects username
    formData.append('password', password);
    
    const response = await apiClient.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (email: string, password: string, full_name?: string) => {
    const response = await apiClient.post('/api/v1/auth/register', { email, password, full_name });
    return response.data;
  },

  getMe: async () => {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  }
};
