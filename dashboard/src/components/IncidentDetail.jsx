import React, { useState, useEffect } from 'react'
import { AlertCircle, FileText, CheckCircle, Clock, Shield, Eye } from 'lucide-react'
import { fetchIncidentDetail, verifyIncidentIntegrity } from '../api'

export default function IncidentDetail({ incident }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)
  const [verificationResult, setVerificationResult] = useState(null)

  useEffect(() => {
    const loadDetail = async () => {
      try {
        setLoading(true)
        const data = await fetchIncidentDetail(incident.id)
        setDetail(data)
      } catch (error) {
        console.error('Failed to load incident detail:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDetail()
  }, [incident.id])

  const handleVerify = async () => {
    try {
      setVerifying(true)
      
      // Get merkle_root from detail (forensics data) or fallback to incident
      const merkleRoot = detail?.forensics?.merkle_root || detail?.merkle_root || incident?.merkle_root
      
      if (!merkleRoot) {
        setVerificationResult({ 
          valid: false, 
          error: 'Merkle root not available. Forensics collection may not be complete.' 
        })
        return
      }
      
      if (!incident?.id) {
        setVerificationResult({ 
          valid: false, 
          error: 'Incident ID not available.' 
        })
        return
      }
      
      const result = await verifyIncidentIntegrity(incident.id, merkleRoot)
      setVerificationResult(result)
    } catch (error) {
      setVerificationResult({ valid: false, error: error.message || 'Verification failed' })
    } finally {
      setVerifying(false)
    }
  }

  if (loading) {
    return (
      <div className="card p-8">
        <div className="space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse" />
          <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
          <div className="h-32 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="card p-8 text-center">
        <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">Failed to load incident details</p>
      </div>
    )
  }

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-danger-100 text-danger-700 border-danger-200',
      high: 'bg-warning-100 text-warning-700 border-warning-200',
      medium: 'bg-primary-100 text-primary-700 border-primary-200',
      low: 'bg-success-100 text-success-700 border-success-200',
    }
    return colors[severity] || colors.low
  }

  const getRiskColor = (score) => {
    if (score >= 80) return 'text-danger-600'
    if (score >= 60) return 'text-warning-600'
    if (score >= 40) return 'text-primary-600'
    return 'text-success-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{detail.title}</h2>
            <p className="text-sm text-gray-500 mt-1">ID: {detail.id}</p>
          </div>
          <div className={`badge ${getSeverityColor(detail.severity)}`}>
            {detail.severity.toUpperCase()}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Risk Score</p>
            <p className={`text-3xl font-bold mt-1 ${getRiskColor(detail.risk_score)}`}>
              {detail.risk_score}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Status</p>
            <p className="text-lg font-semibold text-gray-900 mt-1 capitalize">{detail.status}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Events</p>
            <p className="text-lg font-semibold text-gray-900 mt-1">{detail.event_count}</p>
          </div>
        </div>
      </div>

      {/* Events */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary-600" />
          Contributing Events
        </h3>
        <div className="space-y-3">
          {detail.events?.map((event) => (
            <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-gray-900">{event.description}</p>
                  <p className="text-xs text-gray-500 mt-1">{event.source}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-primary-600">{event.risk_contribution}%</p>
                  <p className={`text-xs font-medium ${event.severity === 'critical' ? 'text-danger-600' : 'text-warning-600'}`}>
                    {event.severity}
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-400">{new Date(event.timestamp).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Artifacts */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          Forensic Artifacts
        </h3>
        <div className="space-y-2">
          {detail.artifacts?.map((artifact, idx) => (
            <div key={`artifact-${artifact.name || 'unknown'}-${idx}-${artifact.type || ''}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div>
                <p className="font-medium text-gray-900">{artifact.name}</p>
                <p className="text-xs text-gray-500">{artifact.type}</p>
              </div>
              <p className="text-sm text-gray-600 font-medium">{artifact.size}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Forensics & Blockchain */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary-600" />
          Blockchain Anchoring
        </h3>

        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Merkle Root</p>
            <p className="font-mono text-sm text-gray-900 break-all">{detail.forensics?.merkle_root}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Artifacts</p>
              <p className="text-2xl font-bold text-gray-900">{detail.forensics?.artifact_count}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Collected</p>
              <p className="text-sm text-gray-900">{new Date(detail.forensics?.collection_time).toLocaleString()}</p>
            </div>
          </div>

          {(() => {
            const merkleRoot = detail?.forensics?.merkle_root || detail?.merkle_root || incident?.merkle_root
            const hasMerkleRoot = merkleRoot && merkleRoot !== 'pending' && merkleRoot !== 'null'
            
            return (
              <button
                onClick={handleVerify}
                disabled={verifying || !hasMerkleRoot}
                className={`btn w-full flex items-center justify-center gap-2 ${
                  hasMerkleRoot 
                    ? 'btn-primary' 
                    : 'btn-secondary opacity-50 cursor-not-allowed'
                }`}
                title={!hasMerkleRoot ? 'Merkle root not available. Forensics collection may be in progress.' : ''}
              >
                <Eye className="w-4 h-4" />
                {verifying ? 'Verifying...' : hasMerkleRoot ? 'Verify Integrity' : 'Merkle Root Not Available'}
              </button>
            )
          })()}

          {verificationResult && (
            <div
              className={`p-4 rounded-lg border ${
                verificationResult.valid
                  ? 'bg-success-50 border-success-200 text-success-700'
                  : 'bg-danger-50 border-danger-200 text-danger-700'
              }`}
            >
              <div className="flex items-center gap-2">
                {verificationResult.valid ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertCircle className="w-5 h-5" />
                )}
                <p className="font-medium">
                  {verificationResult.valid ? 'Integrity Verified' : 'Verification Failed'}
                </p>
              </div>
              {verificationResult.error && (
                <p className="text-sm mt-2">{verificationResult.error}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Response Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary-600" />
          Response Actions
        </h3>

        <div className="space-y-2">
          {detail.response_status === 'isolation_active' && (
            <div className="flex items-center gap-3 p-3 bg-warning-50 border border-warning-200 rounded-lg">
              <Clock className="w-5 h-5 text-warning-600" />
              <div>
                <p className="font-medium text-warning-900">Network Isolation Active</p>
                <p className="text-sm text-warning-700">Affected systems isolated from network</p>
              </div>
            </div>
          )}
          {detail.response_status === 'deception_deployed' && (
            <div className="flex items-center gap-3 p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <CheckCircle className="w-5 h-5 text-primary-600" />
              <div>
                <p className="font-medium text-primary-900">Deception Deployed</p>
                <p className="text-sm text-primary-700">Honeypot and decoys active</p>
              </div>
            </div>
          )}
          {detail.response_status === 'contained' && (
            <div className="flex items-center gap-3 p-3 bg-success-50 border border-success-200 rounded-lg">
              <CheckCircle className="w-5 h-5 text-success-600" />
              <div>
                <p className="font-medium text-success-900">Threat Contained</p>
                <p className="text-sm text-success-700">Incident has been resolved</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
