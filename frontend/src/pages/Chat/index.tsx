import React, { useEffect, useState, useRef } from 'react';
import { useConversationStore } from '../../stores/conversationStore';
import { useChatStore } from '../../stores/chatStore';
import { fileService, FileData } from '../../services/api/files';

const Chat: React.FC = () => {
  const { 
    conversations, 
    activeConvId, 
    fetchConversations, 
    setActiveConvId, 
    createConversation,
    renameConversation,
    archiveConversation,
    deleteConversation 
  } = useConversationStore();

  const {
    messages,
    hasMore,
    status,
    fetchMessages,
    loadMoreMessages,
    sendMessage,
    reset
  } = useChatStore();

  const [input, setInput] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  
  const [files, setFiles] = useState<FileData[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConversations();
    fileService.listFiles().then(res => {
      if (res.success) {
        setFiles(res.data.files.filter((f: any) => f.status === 'READY'));
      }
    }).catch(err => console.error(err));
  }, []);

  useEffect(() => {
    if (activeConvId) {
      fetchMessages(activeConvId);
    } else {
      reset();
    }
  }, [activeConvId]);

  useEffect(() => {
    // Only scroll to bottom if we are generating or just loaded initially
    if (status === 'GENERATING' || status === 'IDLE') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length, status]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0 && hasMore && activeConvId) {
      loadMoreMessages(activeConvId);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !activeConvId || status === 'GENERATING' || status === 'AGENT_RUNNING') return;
    
    let text = input.trim();
    setInput('');
    
    if (text.startsWith('/task ')) {
       const taskContent = text.replace('/task ', '').trim();
       await useChatStore.getState().startAgentTask(activeConvId, taskContent, 'general', selectedDocumentId || undefined);
    } else if (text.startsWith('/research ')) {
       const taskContent = text.replace('/research ', '').trim();
       await useChatStore.getState().startAgentTask(activeConvId, taskContent, 'research', selectedDocumentId || undefined);
    } else {
       await sendMessage(activeConvId, text, selectedDocumentId || undefined);
    }
  };

  const handleRenameSubmit = async (id: number) => {
    if (editTitle.trim()) {
      await renameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const activeConversations = conversations.filter(c => c.status !== 'deleted' && c.status !== 'archived');

  return (
    <div className="flex h-full bg-white">
      {/* Sidebar */}
      <div className="w-64 border-r bg-gray-50 flex flex-col">
        <div className="p-4 border-b">
          <button 
            onClick={() => createConversation()}
            className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {activeConversations.map(conv => (
            <div 
              key={conv.id}
              className={`group flex items-center justify-between px-4 py-3 border-b hover:bg-gray-100 ${activeConvId === conv.id ? 'bg-gray-200 font-semibold' : ''}`}
            >
              {editingId === conv.id ? (
                <input 
                  autoFocus
                  className="flex-1 px-1 py-1 text-sm border rounded"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  onBlur={() => handleRenameSubmit(conv.id)}
                  onKeyDown={e => e.key === 'Enter' && handleRenameSubmit(conv.id)}
                />
              ) : (
                <button
                  onClick={() => setActiveConvId(conv.id)}
                  className="flex-1 text-left truncate"
                >
                  {conv.title}
                </button>
              )}
              
              <div className="hidden group-hover:flex space-x-1 ml-2">
                <button onClick={() => { setEditingId(conv.id); setEditTitle(conv.title); }} className="text-xs text-blue-600">✎</button>
                <button onClick={() => archiveConversation(conv.id)} className="text-xs text-yellow-600">▼</button>
                <button onClick={() => deleteConversation(conv.id)} className="text-xs text-red-600">✕</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeConvId ? (
          <>
            <div 
              className="flex-1 overflow-y-auto p-4 space-y-4"
              onScroll={handleScroll}
              ref={messagesContainerRef}
            >
              {hasMore && (
                <div className="text-center text-xs text-gray-400 my-2">Scroll up to load older messages</div>
              )}
              
              {messages.map(msg => {
                if (msg.role === 'tool') {
                  return (
                    <div key={msg.id} className="flex justify-start opacity-70">
                      <div className="max-w-xl p-2 rounded-lg bg-gray-200 text-gray-700 text-xs font-mono">
                        🔧 {msg.tool_name} executed
                      </div>
                    </div>
                  );
                }
                
                if (msg.role === 'assistant' && msg.tool_calls && !msg.content) {
                  return null; // Don't render empty assistant messages that only call tools
                }

                return (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xl p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                      {msg.tool_calls && msg.tool_calls.length > 0 && (
                         <div className="text-xs text-gray-500 mb-1 italic">
                           🔧 Calling tool: {msg.tool_calls.map((tc: any) => tc.function?.name).join(', ')}
                         </div>
                      )}
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                );
              })}
              
              {status === 'GENERATING' && (
                <div className="flex justify-start">
                  <div className="max-w-xl p-3 rounded-lg bg-gray-100 text-gray-800">
                    <p className="animate-pulse">JARVIS กำลังคิด...</p>
                  </div>
                </div>
              )}
              {status === 'AGENT_RUNNING' && (
                <div className="flex justify-start">
                  <div className="max-w-xl p-3 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-800">
                    <div className="flex items-center space-x-2">
                       <div className="animate-spin h-4 w-4 border-2 border-indigo-600 border-t-transparent rounded-full"></div>
                       <p className="font-semibold">JARVIS is working on a task...</p>
                    </div>
                    {useChatStore.getState().agentTaskStatus && (
                       <div className="mt-2 text-xs opacity-80">
                         Step: {useChatStore.getState().agentTaskStatus.current_step} / {useChatStore.getState().agentTaskStatus.max_steps}
                         {useChatStore.getState().agentTaskStatus.steps?.slice(-1).map((s: any) => (
                           <span key={s.step_number} className="ml-2 bg-indigo-100 px-1 rounded font-mono">
                             🔧 {s.tool_name || 'THINK'}
                           </span>
                         ))}
                       </div>
                    )}
                  </div>
                </div>
              )}

              {status === 'ERROR' && (
                <div className="flex justify-center my-2">
                  <span className="text-red-500 text-sm">เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <div className="p-4 border-t bg-white">
              <form onSubmit={handleSend} className="flex flex-col space-y-2">
                {/* Preview Thumbnail for image */}
                {selectedDocumentId && files.find(f => f.id === selectedDocumentId)?.filename.match(/\.(png|jpe?g|webp)$/i) && (
                  <div className="flex px-2 py-1">
                     <div className="relative">
                       <img 
                          src={`http://localhost:8000/api/v1/files/${selectedDocumentId}/preview?token=${localStorage.getItem('token')}`} 
                          alt="preview" 
                          className="h-16 w-16 object-cover rounded border"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                       />
                       <button 
                         type="button"
                         onClick={() => setSelectedDocumentId("")}
                         className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs"
                       >
                         x
                       </button>
                     </div>
                  </div>
                )}
                
                <div className="flex">
                  <select 
                    className="mr-2 text-sm border rounded px-2 text-gray-700 bg-gray-50 focus:outline-none"
                    value={selectedDocumentId}
                    onChange={(e) => setSelectedDocumentId(e.target.value)}
                  >
                    <option value="">-- No specific document attached --</option>
                    {files.map(f => (
                      <option key={f.id} value={f.id}>{f.filename}</option>
                    ))}
                  </select>
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    className="flex-1 px-4 py-2 border rounded shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Message JARVIS... (prefix with /web to search, /agent to run task)"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={status === 'GENERATING' || status === 'AGENT_RUNNING'}
                  />
                  <button
                    type="submit"
                    disabled={status === 'GENERATING' || status === 'AGENT_RUNNING' || !input.trim()}
                    className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    Send
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select or create a conversation to start chatting.
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
