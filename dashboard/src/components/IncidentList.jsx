import React from 'react'
import { AlertCircle, Clock, TrendingUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function IncidentList({ incidents, selectedIncident, onSelectIncident, loading, error }) {
  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'text-danger-600 bg-danger-50 border-danger-200',
      high: 'text-warning-600 bg-warning-50 border-warning-200',
      medium: 'text-primary-600 bg-primary-50 border-primary-200',
      low: 'text-success-600 bg-success-50 border-success-200',
    }
    return colors[severity] || colors.low
  }

  const getStatusBadge = (status) => {
    const badges = {
      active: 'bg-danger-100 text-danger-700',
      resolved: 'bg-success-100 text-success-700',
      investigating: 'bg-primary-100 text-primary-700',
    }
    return badges[status] || badges.investigating
  }

  if (loading) {
    return (
      <div className="card p-6">
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6 border-danger-200 bg-danger-50">
        <p className="text-danger-700 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden shadow-lg">
      <div className="p-6 border-b-2 border-gray-200 bg-gradient-to-r from-gray-50 to-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Incidents</h2>
            <p className="text-sm text-gray-500 mt-1">{incidents.length} total</p>
          </div>
          {incidents.length > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
              <span className="text-xs text-gray-600">Live</span>
            </div>
          )}
        </div>
      </div>

      <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
        {incidents.map((incident) => (
          <button
            key={incident.id}
            onClick={() => onSelectIncident(incident)}
            className={`w-full p-4 text-left transition-all hover:bg-gray-50 hover:shadow-sm ${
              selectedIncident?.id === incident.id 
                ? 'bg-gradient-to-r from-primary-50 to-primary-100 border-l-4 border-primary-600 shadow-md' 
                : 'border-l-4 border-transparent'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium text-gray-900 truncate">{incident.title}</h3>
                  <span className={`badge-sm ${getStatusBadge(incident.status)}`}>
                    {incident.status}
                  </span>
                </div>
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
                </p>
              </div>

              <div className="flex flex-col items-end gap-2">
                <div className={`badge-sm ${getSeverityColor(incident.severity)} font-semibold`}>
                  {incident.severity.toUpperCase()}
                </div>
                <div className={`flex items-center gap-1 text-sm font-bold ${
                  incident.risk_score >= 80 ? 'text-danger-600' :
                  incident.risk_score >= 60 ? 'text-warning-600' :
                  'text-gray-700'
                }`}>
                  <TrendingUp className="w-4 h-4" />
                  {incident.risk_score}%
                </div>
              </div>
            </div>

            <div className="mt-3 flex items-center gap-2 text-xs text-gray-600">
              <AlertCircle className="w-3 h-3" />
              <span>{incident.event_count} events</span>
              {incident.anchored && (
                <>
                  <span className="text-gray-300">•</span>
                  <span className="text-success-600 font-medium">✓ Anchored</span>
                </>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
