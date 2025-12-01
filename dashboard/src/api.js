import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:9000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000, // Increased timeout for slower responses
})

// Mock data for demo (replace with real API calls)
const mockIncidents = [
  {
    id: 'inc-demo-001',
    title: 'Suspicious Network Activity Detected',
    status: 'active',
    severity: 'critical',
    risk_score: 92,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    event_count: 24,
    response_status: 'isolation_active',
    merkle_root: 'abc123def456',
    anchored: true,
  },
  {
    id: 'inc-demo-002',
    title: 'Unauthorized File Access Attempt',
    status: 'active',
    severity: 'high',
    risk_score: 78,
    created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
    event_count: 18,
    response_status: 'deception_deployed',
    merkle_root: 'xyz789abc123',
    anchored: true,
  },
  {
    id: 'inc-demo-003',
    title: 'Malware Signature Match',
    status: 'resolved',
    severity: 'medium',
    risk_score: 45,
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    event_count: 12,
    response_status: 'contained',
    merkle_root: 'def456ghi789',
    anchored: true,
  },
]

// Transform Risk Engine incident to dashboard format
function transformIncident(incident) {
  const riskLevel = (incident.risk_level || '').toUpperCase()
  
  // Map risk_level to severity
  const severityMap = {
    'HIGH': 'critical',
    'MEDIUM': 'high',
    'LOW': 'medium'
  }
  
  // Map recommended_action to status
  const statusMap = {
    'kill_session': 'active',
    'deceive': 'investigating',
    'allow': 'resolved'
  }
  
  // Get timestamps from events
  const events = Array.isArray(incident.events) ? incident.events : []
  const timestamps = events.map(e => e.timestamp).filter(Boolean)
  const created_at = timestamps.length > 0 ? timestamps[0] : new Date().toISOString()
  const updated_at = timestamps.length > 0 ? timestamps[timestamps.length - 1] : created_at
  
  // Generate title from event types
  const eventTypes = [...new Set(events.map(e => e.type))].slice(0, 2)
  const title = eventTypes.length > 0 
    ? `${eventTypes.join(', ')} detected`
    : `Risk Level: ${riskLevel}`
  
  return {
    id: incident.incident_id,
    title: title,
    status: statusMap[incident.recommended_action] || 'active',
    severity: severityMap[riskLevel] || 'medium',
    risk_score: incident.risk_score || 0,
    created_at: created_at,
    updated_at: updated_at,
    event_count: events.length,
    response_status: incident.recommended_action,
    merkle_root: incident.artifact_refs?.[0] || null,
    anchored: false, // Will be updated from forensics
    // Store full incident for detail view
    _raw: incident
  }
}

export const fetchIncidents = async () => {
  try {
    // Try real API first
    const response = await api.get('/incidents')
    
    if (response.data && Array.isArray(response.data)) {
      const transformed = response.data.map(transformIncident)
      // Sort by updated_at (most recent first), then by risk_score (highest first) as secondary sort
      return transformed.sort((a, b) => {
        const timeA = new Date(a.updated_at || a.created_at).getTime()
        const timeB = new Date(b.updated_at || b.created_at).getTime()
        // Primary sort: most recent first
        if (timeB !== timeA) {
          return timeB - timeA
        }
        // Secondary sort: highest risk first
        return (b.risk_score || 0) - (a.risk_score || 0)
      })
    }
    return []
  } catch (error) {
    console.warn('Failed to fetch incidents, using mock data:', error.message)
    // Sort mock data too
    return mockIncidents.sort((a, b) => {
      const timeA = new Date(a.updated_at || a.created_at).getTime()
      const timeB = new Date(b.updated_at || b.created_at).getTime()
      // Primary sort: most recent first
      if (timeB !== timeA) {
        return timeB - timeA
      }
      // Secondary sort: highest risk first
      return (b.risk_score || 0) - (a.risk_score || 0)
    })
  }
}

export const fetchIncidentDetail = async (incidentId) => {
  try {
    const response = await api.get(`/incidents/${incidentId}`)
    const incident = response.data
    
    if (!incident) {
      throw new Error('Incident not found')
    }
    
    // Transform events for display
    const events = (incident.events || []).map((evt, idx) => {
      let source = 'Unknown Detector'
      if (evt.detector === 'network') source = 'Network Detector'
      else if (evt.detector === 'app') source = 'App Detector'
      else if (evt.detector === 'visual') source = 'Visual Detector'
      
      // Create description from event details
      let description = `${evt.type} detected`
      if (evt.details) {
        if (evt.details.length) {
          description += ` (${evt.details.length} bytes)`
        }
        if (evt.details.direction) {
          description += ` - ${evt.details.direction}`
        }
      }
      
      // Ensure unique ID by combining event_id with index and timestamp
      const uniqueId = evt.event_id 
        ? `${evt.event_id}-${idx}-${evt.timestamp || Date.now()}`
        : `evt-${incident.incident_id}-${idx}-${evt.timestamp || Date.now()}`
      
      return {
        id: uniqueId,
        type: evt.type,
        severity: incident.risk_level?.toLowerCase() || 'medium',
        timestamp: evt.timestamp,
        description: description,
        source: source,
        confidence: evt.confidence || 0,
        details: evt.details || {}
      }
    })
    
    // Get risk explanation
    let riskExplanation = null
    try {
      const expResp = await api.get(`/incidents/${incidentId}/explanation`)
      riskExplanation = expResp.data
    } catch (e) {
      console.warn('Could not fetch risk explanation:', e)
    }
    
    // Get timestamps
    const timestamps = events.map(e => e.timestamp).filter(Boolean)
    const created_at = timestamps.length > 0 ? timestamps[0] : new Date().toISOString()
    const updated_at = timestamps.length > 0 ? timestamps[timestamps.length - 1] : created_at
    
    return {
      ...transformIncident(incident),
      events: events,
      risk_explanation: riskExplanation,
      artifacts: incident.artifact_refs || [],
      forensics: {
        artifact_count: incident.artifact_refs?.length || 0,
        collection_time: created_at,
        merkle_root: incident.artifact_refs?.[0] || null
      }
    }
  } catch (error) {
    console.error('Failed to fetch incident detail:', error)
    // Return mock detail as fallback
    const incident = mockIncidents.find((i) => i.id === incidentId)
    if (incident) {
      return {
        ...incident,
        events: [
          {
            id: 'evt-001',
            type: 'network_anomaly',
            severity: 'high',
            timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            description: 'Unusual outbound traffic detected',
            source: 'Network Detector',
            risk_contribution: 25,
          },
        ],
        artifacts: [],
        forensics: {
          artifact_count: 0,
          collection_time: null,
        },
      }
    }
    throw error
  }
}

export const verifyIncidentIntegrity = async (incidentId, merkleRoot) => {
  try {
    // Validate inputs
    if (!incidentId || !merkleRoot) {
      throw new Error('Incident ID and Merkle root are required for verification')
    }
    
    // Call the blockchain gateway directly; it exposes /api/verify
    const response = await axios.post('http://localhost:8080/api/verify', {
      incident_id: String(incidentId),
      merkle_root: String(merkleRoot),
    })
    return response.data
  } catch (error) {
    console.error('Verification failed:', error)
    
    // Provide more detailed error message
    if (error.response?.status === 422) {
      return { 
        valid: false, 
        error: 'Invalid request format. Please ensure incident has been anchored to blockchain.' 
      }
    }
    
    return { 
      valid: false, 
      error: error.message || 'Verification failed. Please check if blockchain gateway is running.' 
    }
  }
}

export const getIncidentRiskExplanation = async (incidentId) => {
  try {
    // Risk engine exposes /incidents/{id}/explanation
    const response = await api.get(`/incidents/${incidentId}/explanation`)
    const data = response.data || { top_contributors: [] }

    return {
      top_events: (data.top_contributors || []).map((c) => ({
        type: c.type,
        contribution: c.score,
      })),
    }
  } catch (error) {
    return {
      top_events: [
        { type: 'suspicious_command', contribution: 35 },
        { type: 'network_anomaly', contribution: 25 },
        { type: 'visual_anomaly', contribution: 20 },
      ],
    }
  }
}
