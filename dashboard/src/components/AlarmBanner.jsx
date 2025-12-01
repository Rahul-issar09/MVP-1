import React, { useState, useEffect, useRef } from 'react'
import { AlertTriangle, X, Volume2, VolumeX, Bell } from 'lucide-react'

export default function AlarmBanner({ incidents }) {
  const [isMuted, setIsMuted] = useState(false)
  const [dismissedAlarms, setDismissedAlarms] = useState(new Set())
  const audioContextRef = useRef(null)
  const lastPlayedRef = useRef(null)
  const audioInitializedRef = useRef(false)

  // Filter high and critical incidents
  const highSeverityIncidents = incidents.filter(
    (incident) =>
      (incident.severity === 'high' || incident.severity === 'critical' || incident.risk_score >= 60) &&
      !dismissedAlarms.has(incident.id)
  )

  // Initialize audio context on first user interaction
  const initializeAudio = async () => {
    if (audioInitializedRef.current && audioContextRef.current) {
      return audioContextRef.current
    }

    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      if (!AudioContextClass) {
        return null
      }

      const audioContext = new AudioContextClass()
      audioContextRef.current = audioContext
      audioInitializedRef.current = true

      // Resume if suspended (required by some browsers)
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }

      return audioContext
    } catch (error) {
      console.warn('Could not initialize audio context:', error)
      return null
    }
  }

  // Play alarm sound when new high-severity incidents are detected
  useEffect(() => {
    if (highSeverityIncidents.length > 0 && !isMuted && audioInitializedRef.current) {
      const latestIncident = highSeverityIncidents[0]
      const incidentId = latestIncident.id

      // Only play sound if this is a new incident (not the same one)
      if (lastPlayedRef.current !== incidentId) {
        playAlarmSound()
        lastPlayedRef.current = incidentId
      }
    }
  }, [highSeverityIncidents.length, isMuted])

  const playAlarmSound = async () => {
    try {
      const audioContext = audioContextRef.current
      if (!audioContext) {
        return // Audio not initialized yet
      }

      // Resume if suspended
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }

      // Create first beep
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.value = 800 // Higher pitch for urgency
      oscillator.type = 'sine'
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.3)

      // Play a second beep after a short delay
      setTimeout(() => {
        if (!audioContextRef.current) return

        const oscillator2 = audioContext.createOscillator()
        const gainNode2 = audioContext.createGain()

        oscillator2.connect(gainNode2)
        gainNode2.connect(audioContext.destination)

        oscillator2.frequency.value = 1000
        oscillator2.type = 'sine'
        gainNode2.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)

        oscillator2.start(audioContext.currentTime)
        oscillator2.stop(audioContext.currentTime + 0.3)
      }, 200)
    } catch (error) {
      console.warn('Could not play alarm sound:', error)
    }
  }

  const handleDismiss = (incidentId) => {
    setDismissedAlarms((prev) => new Set([...prev, incidentId]))
  }

  const handleDismissAll = () => {
    highSeverityIncidents.forEach((incident) => {
      setDismissedAlarms((prev) => new Set([...prev, incident.id]))
    })
  }

  if (highSeverityIncidents.length === 0) {
    return null
  }

  const criticalCount = highSeverityIncidents.filter((i) => i.severity === 'critical' || i.risk_score >= 80).length
  const highCount = highSeverityIncidents.filter((i) => i.severity === 'high' || (i.risk_score >= 60 && i.risk_score < 80)).length

  return (
    <div className="relative">
      {/* Pulsing background for attention */}
      <div className="absolute inset-0 bg-danger-500 opacity-10 animate-pulse" />
      
      <div className="relative bg-gradient-to-r from-danger-600 to-danger-700 text-white shadow-lg border-b-4 border-danger-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1">
              {/* Animated alarm icon */}
              <div className="relative">
                <Bell className="w-8 h-8 animate-pulse" />
                <div className="absolute inset-0 bg-danger-400 rounded-full animate-ping opacity-75" />
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <AlertTriangle className="w-6 h-6 animate-bounce" />
                  <h2 className="text-xl font-bold">
                    SECURITY ALERT: {highSeverityIncidents.length} High-Priority Incident{highSeverityIncidents.length > 1 ? 's' : ''} Detected
                  </h2>
                </div>
                <div className="flex items-center gap-4 text-sm opacity-90">
                  {criticalCount > 0 && (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                      {criticalCount} Critical
                    </span>
                  )}
                  {highCount > 0 && (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                      {highCount} High
                    </span>
                  )}
                  <span className="text-xs opacity-75">
                    Immediate attention required
                  </span>
                  {!audioInitializedRef.current && (
                    <span className="text-xs opacity-75 italic">
                      • Click to enable audio alerts
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Mute/Unmute button */}
              <button
                onClick={async () => {
                  // Initialize audio on first click (user gesture)
                  if (!audioInitializedRef.current) {
                    await initializeAudio()
                  }
                  setIsMuted(!isMuted)
                }}
                className="p-2 hover:bg-danger-700 rounded-lg transition-colors"
                title={isMuted ? 'Unmute alarms' : 'Mute alarms'}
              >
                {isMuted ? (
                  <VolumeX className="w-5 h-5" />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </button>

              {/* Dismiss all button */}
              <button
                onClick={async () => {
                  // Initialize audio on first click (user gesture)
                  if (!audioInitializedRef.current) {
                    await initializeAudio()
                  }
                  handleDismissAll()
                }}
                className="px-4 py-2 bg-danger-800 hover:bg-danger-900 rounded-lg transition-colors text-sm font-medium"
              >
                Dismiss All
              </button>
            </div>
          </div>

          {/* Incident list */}
          <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
            {highSeverityIncidents.slice(0, 5).map((incident) => (
              <div
                key={incident.id}
                className="bg-danger-800/50 rounded-lg p-3 flex items-center justify-between hover:bg-danger-800/70 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className={`w-3 h-3 rounded-full ${
                    incident.severity === 'critical' || incident.risk_score >= 80
                      ? 'bg-white animate-pulse'
                      : 'bg-white/70'
                  }`} />
                  <div className="flex-1">
                    <p className="font-semibold">{incident.title}</p>
                    <p className="text-xs opacity-75">
                      Risk Score: {incident.risk_score}% • {incident.event_count} events
                    </p>
                  </div>
                </div>
                <button
                  onClick={async () => {
                    // Initialize audio on first click (user gesture)
                    if (!audioInitializedRef.current) {
                      await initializeAudio()
                    }
                    handleDismiss(incident.id)
                  }}
                  className="p-1 hover:bg-danger-700 rounded transition-colors"
                  title="Dismiss this alert"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
            {highSeverityIncidents.length > 5 && (
              <p className="text-xs text-center opacity-75">
                +{highSeverityIncidents.length - 5} more incident{highSeverityIncidents.length - 5 > 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

