import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import './App.css'

// Components
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import AgentManagement from './components/AgentManagement'
import NetworkMonitoring from './components/NetworkMonitoring'
import SecurityOverview from './components/SecurityOverview'
import AlertsCenter from './components/AlertsCenter'
import SystemLogs from './components/SystemLogs'
import Settings from './components/Settings'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [systemStatus, setSystemStatus] = useState({
    agentsOnline: 47,
    totalAgents: 50,
    activeAlerts: 3,
    systemHealth: 'good'
  })

  // Toggle dark mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        agentsOnline: Math.max(45, Math.min(50, prev.agentsOnline + Math.floor(Math.random() * 3) - 1)),
        activeAlerts: Math.max(0, Math.min(10, prev.activeAlerts + Math.floor(Math.random() * 3) - 1))
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <Router>
      <div className="flex h-screen bg-background text-foreground">
        {/* Sidebar */}
        <motion.div
          initial={false}
          animate={{ width: sidebarOpen ? 280 : 80 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="bg-sidebar border-r border-sidebar-border"
        >
          <Sidebar 
            isOpen={sidebarOpen} 
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            systemStatus={systemStatus}
          />
        </motion.div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header 
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            darkMode={darkMode}
            onToggleDarkMode={() => setDarkMode(!darkMode)}
            systemStatus={systemStatus}
          />

          {/* Page Content */}
          <main className="flex-1 overflow-auto bg-background">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard systemStatus={systemStatus} />} />
              <Route path="/agents" element={<AgentManagement />} />
              <Route path="/network" element={<NetworkMonitoring />} />
              <Route path="/security" element={<SecurityOverview />} />
              <Route path="/alerts" element={<AlertsCenter />} />
              <Route path="/logs" element={<SystemLogs />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App

