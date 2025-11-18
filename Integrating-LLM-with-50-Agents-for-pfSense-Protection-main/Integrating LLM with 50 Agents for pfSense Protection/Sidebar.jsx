import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Users,
  Network,
  Shield,
  AlertTriangle,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const menuItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/agents', icon: Users, label: 'Agent Management' },
  { path: '/network', icon: Network, label: 'Network Monitoring' },
  { path: '/security', icon: Shield, label: 'Security Overview' },
  { path: '/alerts', icon: AlertTriangle, label: 'Alerts Center' },
  { path: '/logs', icon: FileText, label: 'System Logs' },
  { path: '/settings', icon: Settings, label: 'Settings' }
]

export default function Sidebar({ isOpen, onToggle, systemStatus }) {
  const location = useLocation()

  const getStatusColor = (health) => {
    switch (health) {
      case 'good': return 'bg-green-500'
      case 'warning': return 'bg-yellow-500'
      case 'critical': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="h-full flex flex-col bg-sidebar">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between">
          {isOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center space-x-2"
            >
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-sidebar-foreground">pfSense</h1>
                <p className="text-xs text-sidebar-foreground/60">Multi-Agent System</p>
              </div>
            </motion.div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* System Status */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 border-b border-sidebar-border"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-sidebar-foreground/80">System Status</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(systemStatus.systemHealth)}`} />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-sidebar-foreground/60">Agents Online</span>
                <div className="flex items-center space-x-1">
                  <Activity className="w-3 h-3 text-green-500" />
                  <span className="text-sidebar-foreground font-medium">
                    {systemStatus.agentsOnline}/{systemStatus.totalAgents}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-sidebar-foreground/60">Active Alerts</span>
                <Badge variant={systemStatus.activeAlerts > 5 ? "destructive" : "secondary"} className="text-xs">
                  {systemStatus.activeAlerts}
                </Badge>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path
            const Icon = item.icon
            
            return (
              <li key={item.path}>
                <Link to={item.path}>
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                        : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    {isOpen && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="font-medium"
                      >
                        {item.label}
                      </motion.span>
                    )}
                    {item.path === '/alerts' && systemStatus.activeAlerts > 0 && isOpen && (
                      <Badge variant="destructive" className="ml-auto text-xs">
                        {systemStatus.activeAlerts}
                      </Badge>
                    )}
                  </motion.div>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-4 border-t border-sidebar-border"
        >
          <div className="flex items-center space-x-2 text-xs text-sidebar-foreground/60">
            <Zap className="w-3 h-3" />
            <span>Powered by AI Agents</span>
          </div>
        </motion.div>
      )}
    </div>
  )
}

