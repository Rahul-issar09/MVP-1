import React, { useState, useEffect } from 'react'
import { AlertCircle, Shield, Activity, TrendingUp } from 'lucide-react'
import Header from './components/Header'
import AlarmBanner from './components/AlarmBanner'
import IncidentList from './components/IncidentList'
import IncidentDetail from './components/IncidentDetail'
import { fetchIncidents } from './api'

export default function App() {
  const [incidents, setIncidents] = useState([])
  const [selectedIncident, setSelectedIncident] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadIncidents = async () => {
      try {
        setLoading(true)
        const data = await fetchIncidents()
        setIncidents(data)
        setError(null)
      } catch (err) {
        setError(err.message)
        console.error('Failed to load incidents:', err)
      } finally {
        setLoading(false)
      }
    }

    loadIncidents()
    const interval = setInterval(loadIncidents, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const stats = {
    active: incidents.filter((i) => i.status === 'active').length,
    critical: incidents.filter((i) => i.severity === 'critical').length,
    avg_risk: incidents.length > 0 ? Math.round(incidents.reduce((sum, i) => sum + i.risk_score, 0) / incidents.length) : 0,
    total: incidents.length,
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header />
      
      {/* Alarm Banner - Shows for high/critical incidents */}
      <AlarmBanner incidents={incidents} />

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<AlertCircle className="w-6 h-6" />}
            label="Active Incidents"
            value={stats.active}
            color="danger"
          />
          <StatCard
            icon={<Shield className="w-6 h-6" />}
            label="Critical"
            value={stats.critical}
            color="danger"
          />
          <StatCard
            icon={<TrendingUp className="w-6 h-6" />}
            label="Avg Risk Score"
            value={`${stats.avg_risk}%`}
            color="warning"
          />
          <StatCard
            icon={<Activity className="w-6 h-6" />}
            label="Total Incidents"
            value={stats.total}
            color="primary"
          />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <IncidentList
              incidents={incidents}
              selectedIncident={selectedIncident}
              onSelectIncident={setSelectedIncident}
              loading={loading}
              error={error}
            />
          </div>
          <div className="lg:col-span-2">
            {selectedIncident ? (
              <IncidentDetail incident={selectedIncident} />
            ) : (
              <div className="card p-8 text-center">
                <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Select an incident to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }) {
  const colorClasses = {
    danger: 'bg-gradient-to-br from-danger-50 to-danger-100 text-danger-700 border-danger-300 shadow-danger-200',
    warning: 'bg-gradient-to-br from-warning-50 to-warning-100 text-warning-700 border-warning-300 shadow-warning-200',
    success: 'bg-gradient-to-br from-success-50 to-success-100 text-success-700 border-success-300 shadow-success-200',
    primary: 'bg-gradient-to-br from-primary-50 to-primary-100 text-primary-700 border-primary-300 shadow-primary-200',
  }

  const iconClasses = {
    danger: 'text-danger-500',
    warning: 'text-warning-500',
    success: 'text-success-500',
    primary: 'text-primary-500',
  }

  return (
    <div className={`card p-6 border-2 ${colorClasses[color]} transition-all hover:scale-105 hover:shadow-lg`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
          <p className={`text-4xl font-bold ${iconClasses[color]}`}>{value}</p>
        </div>
        <div className={`${iconClasses[color]} opacity-30 transform scale-125`}>{icon}</div>
      </div>
    </div>
  )
}
