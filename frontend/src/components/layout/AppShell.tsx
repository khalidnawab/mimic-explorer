import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import Dashboard from '../../pages/Dashboard'
import PatientSearch from '../../pages/PatientSearch'
import PatientChart from '../../pages/PatientChart'
import EncounterBrowser from '../../pages/EncounterBrowser'
import CohortBuilder from '../../pages/CohortBuilder'
import Search from '../../pages/Search'
import PlotBuilder from '../../pages/PlotBuilder'
import ExportManager from '../../pages/ExportManager'
import CohortDetail from '../../pages/CohortDetail'
import FHIRExplorer from '../../pages/FHIRExplorer'
import Documentation from '../../pages/Documentation'

interface AppShellProps {
  status: any
}

const researchTabs = [
  { path: '/research/cohorts', label: 'Cohorts' },
  { path: '/research/search', label: 'Search' },
  { path: '/research/plots', label: 'Plots' },
  { path: '/research/export', label: 'Export' },
]

export default function AppShell({ status }: AppShellProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '□' },
    { path: '/patients', label: 'Patients', icon: '♥' },
    { path: '/encounters', label: 'Encounters', icon: '⊕' },
    { path: '/research', label: 'Research', icon: '◊' },
    { path: '/fhir-explorer', label: 'FHIR', icon: '⚕' },
    { path: '/docs', label: 'Docs', icon: '?' },
  ]

  const isResearch = location.pathname.startsWith('/research')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-primary-700">MIMIC Explorer</h1>
            <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full font-mono">
              v0.1.0
            </span>
            <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
              {status?.total_patients?.toLocaleString()} patients
            </span>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* Research sub-nav */}
      {isResearch && (
        <div className="bg-white border-b border-gray-100 px-6">
          <nav className="flex gap-1 max-w-7xl mx-auto">
            {researchTabs.map((tab) => (
              <Link
                key={tab.path}
                to={tab.path}
                className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                  location.pathname === tab.path || location.pathname.startsWith(tab.path + '/')
                    ? 'border-primary-600 text-primary-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </nav>
        </div>
      )}

      {/* Main content */}
      <main className="p-6 max-w-7xl mx-auto">
        <Routes>
          <Route path="/" element={<Dashboard status={status} />} />
          <Route path="/patients" element={<PatientSearch />} />
          <Route path="/patients/:subjectId" element={<PatientChart />} />
          <Route path="/encounters" element={<EncounterBrowser />} />
          <Route path="/research" element={<Navigate to="/research/cohorts" replace />} />
          <Route path="/research/cohorts" element={<CohortBuilder />} />
          <Route path="/research/cohorts/:id" element={<CohortDetail />} />
          <Route path="/research/search" element={<Search />} />
          <Route path="/research/plots" element={<PlotBuilder />} />
          <Route path="/research/export" element={<ExportManager />} />
          <Route path="/fhir-explorer" element={<FHIRExplorer />} />
          <Route path="/docs" element={<Documentation />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-3 px-6 text-center text-xs text-gray-400">
        Developed by Khalid Nawab &middot; CC BY-NC-ND 4.0
      </footer>
    </div>
  )
}
