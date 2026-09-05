import React from 'react'
import { Outlet, Link } from 'react-router-dom'

const MainLayout = () => {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar Placeholder */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 text-xl font-bold border-b border-gray-800">
          JARVIS
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <Link to="/" className="block py-2 px-4 rounded hover:bg-gray-800">Home</Link>
          <Link to="/chat" className="block py-2 px-4 rounded hover:bg-gray-800">Chat</Link>
          <Link to="/voice" className="block py-2 px-4 rounded hover:bg-gray-800 text-blue-400">🎙️ Voice</Link>
          <Link to="/memory" className="block py-2 px-4 rounded hover:bg-gray-800">Memory</Link>
          <Link to="/files" className="block py-2 px-4 rounded hover:bg-gray-800">Files</Link>
          <Link to="/vision" className="block py-2 px-4 rounded hover:bg-gray-800">Vision</Link>
          <Link to="/research" className="block py-2 px-4 rounded hover:bg-gray-800">Research</Link>
          <Link to="/agents" className="block py-2 px-4 rounded hover:bg-gray-800">Agents</Link>
        </nav>
        <div className="p-4 border-t border-gray-800">
          <Link to="/settings" className="block py-2 px-4 rounded hover:bg-gray-800">Settings</Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-white">
        <Outlet />
      </div>
    </div>
  )
}

export default MainLayout
