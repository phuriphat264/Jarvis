import React, { useEffect, useState } from 'react';
import { useMemoryStore } from '../../stores/memoryStore';

const MemoryPage = () => {
  const { memories, loading, error, fetchMemories, searchMemories, createMemory, updateMemory, deleteMemory } = useMemoryStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState('preference');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    searchMemories(searchQuery);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    await createMemory(newContent, newType);
    setNewContent('');
  };

  const handleEditSave = async (id: number) => {
    if (editContent.trim()) {
      await updateMemory(id, { content: editContent.trim() });
    }
    setEditingId(null);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-50 p-6 overflow-y-auto">
      <div className="max-w-4xl w-full mx-auto space-y-6">
        
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">JARVIS Memory</h1>
          <form onSubmit={handleSearch} className="flex space-x-2">
            <input 
              type="text" 
              placeholder="Search memories..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="px-4 py-2 border rounded shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
            <button type="submit" className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-900">
              Search
            </button>
            {searchQuery && (
              <button type="button" onClick={() => { setSearchQuery(''); fetchMemories(); }} className="px-4 py-2 bg-gray-300 text-gray-800 rounded">
                Clear
              </button>
            )}
          </form>
        </div>

        {/* Create new memory */}
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <h2 className="text-lg font-semibold mb-3">Add Manual Memory</h2>
          <form onSubmit={handleCreate} className="flex space-x-2">
            <select 
              value={newType} 
              onChange={e => setNewType(e.target.value)}
              className="px-3 py-2 border rounded bg-gray-50"
            >
              <option value="preference">Preference</option>
              <option value="project">Project</option>
              <option value="fact">Fact</option>
              <option value="goal">Goal</option>
              <option value="instruction">Instruction</option>
            </select>
            <input 
              type="text"
              placeholder="E.g., I prefer dark mode..."
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
              className="flex-1 px-4 py-2 border rounded focus:ring-blue-500 focus:border-blue-500"
            />
            <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50" disabled={!newContent.trim()}>
              Add
            </button>
          </form>
        </div>

        {/* Memory List */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          {loading && <div className="p-4 text-center text-gray-500">Loading memories...</div>}
          {error && <div className="p-4 text-center text-red-500">{error}</div>}
          
          {!loading && !error && memories.length === 0 && (
            <div className="p-8 text-center text-gray-500">No memories found.</div>
          )}

          <div className="divide-y">
            {memories.map(mem => (
              <div key={mem.id} className="p-4 flex justify-between items-start hover:bg-gray-50">
                <div className="flex-1 mr-4">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800 uppercase tracking-wide">
                      {mem.memory_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      Source: {mem.source_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      Importance: {(mem.importance * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {editingId === mem.id ? (
                    <div className="flex space-x-2 mt-2">
                      <input 
                        type="text"
                        value={editContent}
                        onChange={e => setEditContent(e.target.value)}
                        className="flex-1 px-3 py-1 text-sm border rounded"
                        autoFocus
                        onKeyDown={e => e.key === 'Enter' && handleEditSave(mem.id)}
                      />
                      <button onClick={() => handleEditSave(mem.id)} className="text-sm text-green-600 hover:underline">Save</button>
                      <button onClick={() => setEditingId(null)} className="text-sm text-gray-500 hover:underline">Cancel</button>
                    </div>
                  ) : (
                    <p className="text-gray-800 mt-1">{mem.content}</p>
                  )}
                </div>
                
                <div className="flex space-x-3 text-sm">
                  <button onClick={() => { setEditingId(mem.id); setEditContent(mem.content); }} className="text-blue-600 hover:underline">Edit</button>
                  <button onClick={() => deleteMemory(mem.id)} className="text-red-600 hover:underline">Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default MemoryPage;
