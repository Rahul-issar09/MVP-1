import React from 'react'
import { Shield, Bell, Settings, Activity } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-white border-b-2 border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-primary-600 to-primary-700 rounded-xl shadow-lg transform hover:scale-105 transition-transform">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                SentinelVNC
                <span className="flex items-center gap-1 text-xs font-normal text-success-600">
                  <Activity className="w-3 h-3 animate-pulse" />
                  Live
                </span>
              </h1>
              <p className="text-sm text-gray-500">Security Incident Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button 
              className="p-2 hover:bg-gray-100 rounded-lg transition-all hover:scale-110 active:scale-95"
              title="Notifications"
            >
              <Bell className="w-5 h-5 text-gray-600" />
            </button>
            <button 
              className="p-2 hover:bg-gray-100 rounded-lg transition-all hover:scale-110 active:scale-95"
              title="Settings"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
            <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center shadow-md hover:shadow-lg transition-shadow cursor-pointer">
              <span className="text-white font-semibold text-sm">AD</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
