import React, { useState, useRef, useEffect } from 'react';
import { voiceService } from '../../services/api/voice';
import { useChatStore } from '../../store/chatStore';

type VoiceState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'THINKING' | 'SPEAKING' | 'ERROR' | 'CANCELLED';

const Voice: React.FC = () => {
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState<string>('');
  const [jarvisResponse, setJarvisResponse] = useState<string>('');
  const [showTranscript, setShowTranscript] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string>('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  
  const { conversations, createConversation, activeConvId, setActiveConvId } = useChatStore();

  useEffect(() => {
    // Ensure we have an active conversation to bind voice to
    if (!activeConvId && conversations.length > 0) {
      setActiveConvId(conversations[0].id);
    } else if (conversations.length === 0) {
      createConversation('Voice Session');
    }
    
    return () => {
      stopRecording();
      stopPlayback();
    };
  }, [conversations, activeConvId]);

  const startRecording = async () => {
    setErrorMsg('');
    setTranscript('');
    setJarvisResponse('');
    stopPlayback();
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Release mic
        stream.getTracks().forEach(track => track.stop());
        
        if (voiceState !== 'CANCELLED') {
          await processVoiceMessage(audioBlob);
        }
      };

      mediaRecorder.start(200);
      setVoiceState('LISTENING');
    } catch (err) {
      console.error(err);
      setErrorMsg('ไม่สามารถใช้ไมโครโฟนได้ กรุณาอนุญาต Microphone จาก Browser Settings');
      setVoiceState('ERROR');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      if (voiceState === 'LISTENING') {
        setVoiceState('PROCESSING');
      }
    }
  };

  const cancelInteraction = () => {
    setVoiceState('CANCELLED');
    stopRecording();
    stopPlayback();
    setTimeout(() => setVoiceState('IDLE'), 2000);
  };

  const processVoiceMessage = async (audioBlob: Blob) => {
    if (!activeConvId) {
       setErrorMsg('No active conversation');
       setVoiceState('ERROR');
       return;
    }
    
    setVoiceState('THINKING');
    try {
      const response = await voiceService.sendMessage(activeConvId, audioBlob);
      setTranscript(response.transcript);
      setJarvisResponse(response.response);
      
      if (response.audio?.base64) {
        setVoiceState('SPEAKING');
        playAudio(response.audio.base64, response.audio.mime_type || 'audio/mpeg');
      } else {
        setVoiceState('IDLE');
      }
      
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Voice processing failed');
      setVoiceState('ERROR');
      setTimeout(() => setVoiceState('IDLE'), 3000);
    }
  };

  const playAudio = (base64Audio: string, mimeType: string) => {
    const audioSrc = `data:${mimeType};base64,${base64Audio}`;
    const audio = new Audio(audioSrc);
    audioPlayerRef.current = audio;
    
    audio.onended = () => {
      setVoiceState('IDLE');
    };
    
    audio.play().catch(e => {
      console.error("Audio playback failed", e);
      setVoiceState('IDLE');
    });
  };

  const stopPlayback = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-900 text-white w-full">
      <div className="text-center w-full max-w-2xl px-6">
        <h1 className="text-3xl font-light tracking-widest mb-12">JARVIS</h1>

        {/* State Indicator */}
        <div className="h-32 flex flex-col items-center justify-center mb-12">
          {voiceState === 'IDLE' && (
             <div className="w-16 h-16 rounded-full bg-blue-500 opacity-50 shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>
          )}
          {voiceState === 'LISTENING' && (
             <div className="w-20 h-20 rounded-full bg-red-500 animate-pulse shadow-[0_0_30px_rgba(239,68,68,0.8)] flex items-center justify-center">
                <span className="text-2xl">🎙️</span>
             </div>
          )}
          {(voiceState === 'PROCESSING' || voiceState === 'THINKING') && (
             <div className="flex space-x-2">
               <div className="w-4 h-4 rounded-full bg-blue-400 animate-bounce"></div>
               <div className="w-4 h-4 rounded-full bg-blue-400 animate-bounce" style={{animationDelay: '0.1s'}}></div>
               <div className="w-4 h-4 rounded-full bg-blue-400 animate-bounce" style={{animationDelay: '0.2s'}}></div>
             </div>
          )}
          {voiceState === 'SPEAKING' && (
             <div className="flex space-x-1 items-end h-12">
               {[1,2,3,4,5,4,3,2,1].map((n, i) => (
                 <div key={i} className="w-2 bg-green-400 animate-pulse rounded-t" style={{height: `${n * 10}px`, animationDelay: `${i * 0.1}s`}}></div>
               ))}
             </div>
          )}
          {voiceState === 'ERROR' && (
             <div className="text-red-400 mt-4">{errorMsg}</div>
          )}
          {voiceState === 'CANCELLED' && (
             <div className="text-gray-400 mt-4">Cancelled</div>
          )}
          
          <div className="mt-6 text-sm uppercase tracking-widest opacity-70">
            {voiceState === 'IDLE' && 'Ready'}
            {voiceState === 'LISTENING' && 'Listening...'}
            {voiceState === 'PROCESSING' && 'Transcribing...'}
            {voiceState === 'THINKING' && 'Thinking...'}
            {voiceState === 'SPEAKING' && 'Speaking...'}
          </div>
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-6 mb-12">
          {voiceState === 'IDLE' || voiceState === 'ERROR' || voiceState === 'CANCELLED' ? (
            <button 
              onClick={startRecording}
              className="px-8 py-3 bg-white text-gray-900 rounded-full font-semibold hover:bg-gray-200 transition"
            >
              Start Listening
            </button>
          ) : (
            <>
              {voiceState === 'LISTENING' && (
                <button 
                  onClick={stopRecording}
                  className="px-8 py-3 bg-red-600 text-white rounded-full font-semibold hover:bg-red-700 transition"
                >
                  Stop & Send
                </button>
              )}
              <button 
                onClick={cancelInteraction}
                className="px-8 py-3 border border-gray-500 text-gray-300 rounded-full hover:bg-gray-800 transition"
              >
                Cancel
              </button>
            </>
          )}
        </div>

        {/* Transcripts */}
        <div className="text-left mt-8 w-full">
          <div className="flex justify-between items-center mb-4">
             <h3 className="text-sm font-semibold opacity-50 uppercase tracking-wider">Conversation</h3>
             <button onClick={() => setShowTranscript(!showTranscript)} className="text-xs opacity-50 hover:opacity-100">
               {showTranscript ? 'Hide' : 'Show'} Transcript
             </button>
          </div>
          
          {showTranscript && (
            <div className="space-y-4 bg-gray-800 p-6 rounded-xl min-h-[150px]">
              {transcript ? (
                <div className="flex flex-col">
                  <span className="text-xs text-blue-400 mb-1">You</span>
                  <p className="text-lg text-gray-100">{transcript}</p>
                </div>
              ) : (
                <div className="text-gray-500 italic">No input yet...</div>
              )}
              
              {jarvisResponse && (
                <div className="flex flex-col mt-4 pt-4 border-t border-gray-700">
                  <span className="text-xs text-green-400 mb-1">JARVIS</span>
                  <p className="text-lg text-gray-100 whitespace-pre-wrap">{jarvisResponse}</p>
                </div>
              )}
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
};

export default Voice;
