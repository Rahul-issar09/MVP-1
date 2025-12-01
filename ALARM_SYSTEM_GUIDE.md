# Alarm System & UI Enhancements Guide

## Overview
The SentinelVNC Dashboard now includes a comprehensive alarm system that automatically alerts administrators when high-priority security incidents are detected. The system works even when the admin is offline (browser tab is open), ensuring critical incidents are never missed.

## Features

### 1. Alarm Banner Component
- **Location**: Appears at the top of the dashboard, below the header
- **Trigger Conditions**: 
  - Incidents with severity `high` or `critical`
  - Incidents with risk score ≥ 60%
- **Visual Features**:
  - Red gradient background with pulsing animation
  - Animated bell icon with ping effect
  - Alert triangle with bounce animation
  - Shows count of critical and high-severity incidents
  - Displays up to 5 recent high-priority incidents
  - Scrollable list for more incidents

### 2. Audio Alerts
- **Automatic Sound**: Plays a two-tone beep when new high-severity incidents are detected
- **Mute/Unmute**: Toggle button to silence alarms while keeping visual alerts
- **Smart Playback**: Only plays sound for new incidents (not repeated for the same incident)

### 3. Alarm Controls
- **Mute Button**: Toggle audio alerts on/off
- **Dismiss All**: Dismiss all current alarms at once
- **Individual Dismiss**: Dismiss specific incident alarms
- **Persistent**: Alarms remain visible until dismissed or resolved

### 4. UI Enhancements

#### Header Improvements
- Enhanced gradient logo with hover effects
- "Live" status indicator with pulsing animation
- Improved button hover states with scale animations
- Better shadow and border styling

#### Stat Cards
- Gradient backgrounds for better visual hierarchy
- Larger, bolder numbers
- Hover scale effects
- Enhanced color coding

#### Incident List
- Gradient header with live indicator
- Better selection highlighting with gradient backgrounds
- Enhanced severity badges
- Improved risk score display with color coding
- Smooth hover transitions

#### General Improvements
- Better shadows and borders throughout
- Smooth transitions and animations
- Improved color contrast
- Professional gradient effects

## How It Works

### Alarm Detection
1. The dashboard polls for incidents every 30 seconds
2. When new incidents are fetched, the `AlarmBanner` component filters for high-severity incidents
3. If any incidents match the criteria (severity: high/critical OR risk_score ≥ 60), the alarm banner appears
4. Audio alert plays automatically (unless muted) for new incidents

### Alarm Persistence
- Alarms remain visible even if the admin is not actively viewing the dashboard
- The browser tab will continue to poll for incidents in the background
- When new high-severity incidents are detected, the alarm banner appears immediately

### Dismissal Behavior
- Dismissed alarms are stored in component state
- Dismissed incidents won't trigger alarms again unless they're new incidents
- Refreshing the page resets dismissed alarms (by design - ensures critical incidents aren't permanently ignored)

## Demo Usage

### To Demonstrate the Alarm System:

1. **Start all services** (as per DEMO_SETUP.md)

2. **Launch the dashboard**:
   ```bash
   cd dashboard
   npm start
   ```

3. **Trigger a high-severity incident**:
   ```bash
   python scripts/demo_attack_simulator.py
   ```
   Or use the test script:
   ```bash
   python scripts/test_demo_flow.py
   ```

4. **Observe the alarm**:
   - The alarm banner should appear at the top
   - Audio alert should play (if not muted)
   - The banner shows incident count and details
   - Incidents are listed with risk scores

5. **Test alarm controls**:
   - Click "Mute" to silence audio (visual alert remains)
   - Click "Dismiss All" to hide all current alarms
   - Click "X" on individual incidents to dismiss specific alarms

6. **Test persistence**:
   - Leave the dashboard open in a browser tab
   - Trigger another high-severity incident
   - The alarm should appear automatically (even if tab is in background)

## Customization

### Adjusting Alarm Thresholds
Edit `dashboard/src/components/AlarmBanner.jsx`:
```javascript
const highSeverityIncidents = incidents.filter(
  (incident) =>
    (incident.severity === 'high' || 
     incident.severity === 'critical' || 
     incident.risk_score >= 60) && // Change this threshold
    !dismissedAlarms.has(incident.id)
)
```

### Customizing Audio Alert
Edit the `playAlarmSound()` function in `AlarmBanner.jsx`:
- Change `frequency.value` for different pitch
- Adjust `gain` values for volume
- Modify timing for different patterns

### Styling Customization
- Alarm colors: Edit gradient classes in `AlarmBanner.jsx`
- Animation speed: Modify CSS animation durations in `index.css`
- Banner height: Adjust padding and max-height in the component

## Technical Details

### Component Structure
```
App.jsx
  ├── Header.jsx
  ├── AlarmBanner.jsx (NEW)
  ├── IncidentList.jsx
  └── IncidentDetail.jsx
```

### State Management
- Alarm dismissal state is local to `AlarmBanner` component
- Incident data flows from `App.jsx` via props
- Audio playback uses Web Audio API for cross-browser compatibility

### Performance
- Alarm banner only renders when high-severity incidents exist
- Audio is only played for new incidents (not on every render)
- Efficient filtering using array methods
- Minimal re-renders with proper React hooks

## Browser Compatibility
- **Chrome/Edge**: Full support (Web Audio API)
- **Firefox**: Full support
- **Safari**: Full support (may require user interaction for audio)
- **Mobile**: Visual alerts work; audio may be limited by browser policies

## Notes
- Audio alerts require user interaction on some browsers (Safari, mobile)
- Dismissed alarms reset on page refresh (by design)
- The alarm system works independently of admin presence (browser tab open)
- Multiple high-severity incidents are aggregated in a single banner

