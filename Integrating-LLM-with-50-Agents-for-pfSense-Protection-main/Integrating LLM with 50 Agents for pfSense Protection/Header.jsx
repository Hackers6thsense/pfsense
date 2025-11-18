import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Menu,
  Sun,
  Moon,
  Bell,
  Search,
  User,
  Settings,
  LogOut,
  Activity,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export default function Header({ onToggleSidebar, darkMode, onToggleDarkMode, systemStatus }) {
  const [searchQuery, setSearchQuery] = useState('')

  const getConnectionStatus = () => {
    const percentage = (systemStatus.agentsOnline / systemStatus.totalAgents) * 100
    if (percentage >= 90) return { status: 'excellent', color: 'text-green-500', icon: Wifi }
    if (percentage >= 70) return { status: 'good', color: 'text-yellow-500', icon: Wifi }
    return { status: 'poor', color: 'text-red-500', icon: WifiOff }
  }

  const connectionInfo = getConnectionStatus()
  const ConnectionIcon = connectionInfo.icon

  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6">
      {/* Left Section */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleSidebar}
          className="lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </Button>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search agents, logs, alerts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 w-64 lg:w-80"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-4">
        {/* System Status Indicators */}
        <div className="hidden md:flex items-center space-x-4">
          {/* Connection Status */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-muted/50"
          >
            <ConnectionIcon className={`w-4 h-4 ${connectionInfo.color}`} />
            <span className="text-sm font-medium">
              {systemStatus.agentsOnline}/{systemStatus.totalAgents}
            </span>
          </motion.div>

          {/* System Health */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-muted/50"
          >
            <Activity className="w-4 h-4 text-green-500" />
            <span className="text-sm font-medium capitalize">{systemStatus.systemHealth}</span>
          </motion.div>
        </div>

        {/* Dark Mode Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleDarkMode}
          className="relative"
        >
          <motion.div
            initial={false}
            animate={{ rotate: darkMode ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </motion.div>
        </Button>

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="relative">
              <Bell className="w-5 h-5" />
              {systemStatus.activeAlerts > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1"
                >
                  <Badge variant="destructive" className="text-xs px-1 min-w-[1.25rem] h-5">
                    {systemStatus.activeAlerts}
                  </Badge>
                </motion.div>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Recent Alerts</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {systemStatus.activeAlerts > 0 ? (
              <>
                <DropdownMenuItem className="flex flex-col items-start space-y-1 p-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full" />
                    <span className="font-medium">High CPU Usage</span>
                    <Badge variant="destructive" className="text-xs">Critical</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">Agent-Security-01 reporting 95% CPU usage</p>
                  <span className="text-xs text-muted-foreground">2 minutes ago</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="flex flex-col items-start space-y-1 p-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                    <span className="font-medium">Network Anomaly</span>
                    <Badge variant="secondary" className="text-xs">Warning</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">Unusual traffic pattern detected on LAN</p>
                  <span className="text-xs text-muted-foreground">5 minutes ago</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-center text-sm text-primary">
                  View All Alerts
                </DropdownMenuItem>
              </>
            ) : (
              <DropdownMenuItem className="text-center text-muted-foreground">
                No active alerts
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="relative">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-foreground" />
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Administrator</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

