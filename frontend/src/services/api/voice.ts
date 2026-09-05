import api from './index';

export interface VoiceMessageResponse {
  transcript: string;
  response: string;
  audio: {
    base64: string | null;
    mime_type: string | null;
  };
}

export const voiceService = {
  sendMessage: async (conversationId: number, audioBlob: Blob, documentId?: string): Promise<VoiceMessageResponse> => {
    const formData = new FormData();
    formData.append('conversation_id', conversationId.toString());
    
    // Create File from Blob
    const file = new File([audioBlob], 'audio.webm', { type: audioBlob.type || 'audio/webm' });
    formData.append('audio', file);
    
    if (documentId) {
      formData.append('document_id', documentId);
    }
    
    const response = await api.post('/api/v1/voice/message', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data.data;
  },
};
