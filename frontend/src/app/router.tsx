import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout'
import Chat from '../pages/Chat'
import Memory from '../pages/Memory'
import Login from '../pages/Login'
import Files from '../pages/Files'
import Voice from '../pages/Voice'
import Dashboard from '../pages/Dashboard'
import Integrations from '../pages/Settings/Integrations'
import Agents from '../pages/Agents'
import Devices from '../pages/Devices'
import EdgeNodes from '../pages/Edge'
import IntelligenceDashboard from '../pages/Intelligence'
import PersonalizationPage from '../pages/Personalization'

// Placeholders
const Vision = () => <div className="p-4"><h1 className="text-2xl font-bold">Vision Module — Coming Soon</h1></div>
const Research = () => <div className="p-4"><h1 className="text-2xl font-bold">Research Module — Coming Soon</h1></div>

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/chat', element: <Chat /> },
      { path: '/memory', element: <Memory /> },
      { path: '/files', element: <Files /> },
      { path: '/voice', element: <Voice /> },
      { path: '/vision', element: <Vision /> },
      { path: '/research', element: <Research /> },
      { path: '/agents', element: <Agents /> },
      { path: '/devices', element: <Devices /> },
      { path: '/edge', element: <EdgeNodes /> },
      { path: '/intelligence', element: <IntelligenceDashboard /> },
      { path: '/personalization', element: <PersonalizationPage /> },
      { path: '/settings/integrations', element: <Integrations /> },
    ],
  },
])
