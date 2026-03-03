import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from './api/client'
import AppShell from './components/layout/AppShell'
import SetupWizard from './pages/SetupWizard'

interface AppStatus {
  import_status: string
  total_patients: number
  total_encounters: number
}

function App() {
  const [status, setStatus] = useState<AppStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getStatus().then((data) => {
      setStatus(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  const isSetupComplete = status?.import_status === 'completed'

  return (
    <Routes>
      <Route path="/setup" element={<SetupWizard onComplete={() => window.location.href = '/'} />} />
      <Route path="/*" element={
        isSetupComplete
          ? <AppShell status={status} />
          : <Navigate to="/setup" replace />
      } />
    </Routes>
  )
}

function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }
  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-primary-600 ${sizeClasses[size]}`} />
  )
}

export default App
