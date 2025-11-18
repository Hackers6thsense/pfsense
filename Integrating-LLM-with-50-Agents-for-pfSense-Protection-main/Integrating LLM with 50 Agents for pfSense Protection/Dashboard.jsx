import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  Shield,
  Network,
  AlertTriangle,
  Users,
  Cpu,
  HardDrive,
  Wifi,
  TrendingUp,
  TrendingDown,
  Eye,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// Mock data for charts
const networkTrafficData = [
  { time: '00:00', inbound: 45, outbound: 32 },
  { time: '04:00', inbound: 52, outbound: 38 },
  { time: '08:00', inbound: 78, outbound: 65 },
  { time: '12:00', inbound: 95, outbound: 82 },
  { time: '16:00', inbound: 88, outbound: 75 },
  { time: '20:00', inbound: 67, outbound: 54 },
]

const agentPerformanceData = [
  { name: 'Log Analyzer', performance: 98, load: 45 },
  { name: 'Traffic Monitor', performance: 95, load: 62 },
  { name: 'Security Scanner', performance: 92, load: 78 },
  { name: 'Firewall Monitor', performance: 97, load: 34 },
  { name: 'Intrusion Detection', performance: 94, load: 56 },
]

const threatDistribution = [
  { name: 'Malware', value: 35, color: '#ef4444' },
  { name: 'Intrusion Attempts', value: 28, color: '#f97316' },
  { name: 'DDoS', value: 20, color: '#eab308' },
  { name: 'Phishing', value: 12, color: '#22c55e' },
  { name: 'Other', value: 5, color: '#6366f1' },
]

const systemMetrics = [
  { time: '00:00', cpu: 35, memory: 62, network: 45 },
  { time: '04:00', cpu: 28, memory: 58, network: 52 },
  { time: '08:00', cpu: 65, memory: 72, network: 78 },
  { time: '12:00', cpu: 82, memory: 85, network: 95 },
  { time: '16:00', cpu: 75, memory: 78, network: 88 },
  { time: '20:00', cpu: 54, memory: 65, network: 67 },
]

export default function Dashboard({ systemStatus }) {
  const [realtimeData, setRealtimeData] = useState({
    cpuUsage: 45,
    memoryUsage: 62,
    networkLoad: 78,
    diskUsage: 34,
    threatsBlocked: 1247,
    packetsAnalyzed: 2847392,
    activeConnections: 1834
  })

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setRealtimeData(prev => ({
        ...prev,
        cpuUsage: Math.max(20, Math.min(90, prev.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(30, Math.min(95, prev.memoryUsage + (Math.random() - 0.5) * 8)),
        networkLoad: Math.max(10, Math.min(100, prev.networkLoad + (Math.random() - 0.5) * 15)),
        threatsBlocked: prev.threatsBlocked + Math.floor(Math.random() * 3),
        packetsAnalyzed: prev.packetsAnalyzed + Math.floor(Math.random() * 1000) + 500,
        activeConnections: Math.max(1000, Math.min(3000, prev.activeConnections + Math.floor(Math.random() * 100) - 50))
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const StatCard = ({ title, value, change, icon: Icon, trend, color = "text-foreground" }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <Icon className={`h-4 w-4 ${color}`} />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          {change && (
            <div className="flex items-center text-xs text-muted-foreground">
              {trend === 'up' ? (
                <TrendingUp className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <TrendingDown className="mr-1 h-3 w-3 text-red-500" />
              )}
              {change} from last hour
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time monitoring and control of your pfSense multi-agent system
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="text-green-600 border-green-600">
            <Activity className="w-3 h-3 mr-1" />
            System Online
          </Badge>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Agents Online"
          value={`${systemStatus.agentsOnline}/${systemStatus.totalAgents}`}
          change="+2"
          trend="up"
          icon={Users}
          color="text-blue-500"
        />
        <StatCard
          title="Active Alerts"
          value={systemStatus.activeAlerts}
          change="-1"
          trend="down"
          icon={AlertTriangle}
          color="text-red-500"
        />
        <StatCard
          title="Threats Blocked"
          value={realtimeData.threatsBlocked.toLocaleString()}
          change="+47"
          trend="up"
          icon={Shield}
          color="text-green-500"
        />
        <StatCard
          title="Network Load"
          value={`${realtimeData.networkLoad}%`}
          change="+5%"
          trend="up"
          icon={Network}
          color="text-purple-500"
        />
      </div>

      {/* System Resources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Cpu className="w-5 h-5" />
              <span>System Resources</span>
            </CardTitle>
            <CardDescription>Real-time system performance metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>CPU Usage</span>
                <span>{realtimeData.cpuUsage}%</span>
              </div>
              <Progress value={realtimeData.cpuUsage} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Memory Usage</span>
                <span>{realtimeData.memoryUsage}%</span>
              </div>
              <Progress value={realtimeData.memoryUsage} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Disk Usage</span>
                <span>{realtimeData.diskUsage}%</span>
              </div>
              <Progress value={realtimeData.diskUsage} className="h-2" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Network Load</span>
                <span>{realtimeData.networkLoad}%</span>
              </div>
              <Progress value={realtimeData.networkLoad} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Eye className="w-5 h-5" />
              <span>Real-time Statistics</span>
            </CardTitle>
            <CardDescription>Live system activity metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-blue-500">
                  {realtimeData.packetsAnalyzed.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">Packets Analyzed</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <div className="text-2xl font-bold text-green-500">
                  {realtimeData.activeConnections.toLocaleString()}
                </div>
                <div className="text-sm text-muted-foreground">Active Connections</div>
              </div>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-3xl font-bold text-red-500">
                {realtimeData.threatsBlocked.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Total Threats Blocked Today</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Network Traffic */}
        <Card>
          <CardHeader>
            <CardTitle>Network Traffic</CardTitle>
            <CardDescription>Inbound and outbound traffic over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={networkTrafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="inbound"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="outbound"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Threat Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Distribution</CardTitle>
            <CardDescription>Types of threats detected today</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={threatDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {threatDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {threatDistribution.map((item, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm">{item.name}</span>
                  <span className="text-sm text-muted-foreground">({item.value}%)</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="w-5 h-5" />
            <span>Agent Performance</span>
          </CardTitle>
          <CardDescription>Performance and load metrics for active agents</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agentPerformanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="performance" fill="#3b82f6" name="Performance %" />
              <Bar dataKey="load" fill="#10b981" name="Load %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* System Metrics Over Time */}
      <Card>
        <CardHeader>
          <CardTitle>System Metrics Over Time</CardTitle>
          <CardDescription>CPU, Memory, and Network usage trends</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={systemMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#ef4444"
                strokeWidth={2}
                name="CPU %"
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Memory %"
              />
              <Line
                type="monotone"
                dataKey="network"
                stroke="#10b981"
                strokeWidth={2}
                name="Network %"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

