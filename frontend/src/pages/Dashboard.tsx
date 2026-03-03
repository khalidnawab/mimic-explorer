import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts'
import { api } from '../api/client'

interface DashboardProps {
  status: any
}

const ALL_MODULES = ['hosp', 'icu', 'note'] as const
const PATIENT_LIMITS = [
  { label: '100 patients', value: 100 },
  { label: '500 patients', value: 500 },
  { label: '1,000 patients', value: 1000 },
  { label: '5,000 patients', value: 5000 },
  { label: 'All patients', value: null },
]

const COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6']

function Panel({ title, defaultOpen = true, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-5 py-3 flex items-center justify-between text-left font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
      >
        {title}
        <span className="text-gray-400">{open ? '▾' : '▸'}</span>
      </button>
      {open && <div className="px-5 pb-5 space-y-6">{children}</div>}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-800">{typeof value === 'number' ? value.toLocaleString() : value}</p>
    </div>
  )
}

function SupplementImportPanel({ status, onClose }: { status: any; onClose: () => void }) {
  const [folderPath, setFolderPath] = useState(status?.mimic_data_path || '')
  const [folderValid, setFolderValid] = useState<boolean | null>(null)
  const [folderInfo, setFolderInfo] = useState<any>(null)
  const [selectedModules, setSelectedModules] = useState<string[]>([])
  const [existingPatientsOnly, setExistingPatientsOnly] = useState(false)
  const [patientLimit, setPatientLimit] = useState<number | null>(1000)
  const [importing, setImporting] = useState(false)
  const [importStatus, setImportStatus] = useState<any>(null)
  const [error, setError] = useState('')

  const importedModules: string[] = status?.imported_modules || []

  const handleValidate = useCallback(async (path: string) => {
    if (!path) return
    try {
      const result = await api.validateFolder(path)
      setFolderValid(result.valid)
      setFolderInfo(result)
      setError('')
    } catch (e: any) {
      setFolderValid(false)
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    if (folderPath) handleValidate(folderPath)
  }, []) // validate pre-filled path on mount

  const handleBrowse = async () => {
    try {
      const result = await api.browseFolder()
      if (result.path) {
        setFolderPath(result.path)
        handleValidate(result.path)
      }
    } catch (e: any) {
      setError(e.message)
    }
  }

  const toggleModule = (mod: string) => {
    setSelectedModules(prev =>
      prev.includes(mod) ? prev.filter(m => m !== mod) : [...prev, mod]
    )
  }

  const canImport = folderValid && selectedModules.length > 0 && !importing

  const handleStartImport = async () => {
    setImporting(true)
    setError('')
    try {
      // Include already-imported modules so the importer re-runs all stages idempotently
      const allModules = [...new Set([...importedModules, ...selectedModules])]
      await api.supplementImport({
        folder_path: folderPath,
        modules: allModules,
        patient_limit: existingPatientsOnly ? null : patientLimit,
        generate_fhir: false,
        existing_patients_only: existingPatientsOnly,
      })
      // Poll for progress
      const poll = setInterval(async () => {
        try {
          const s = await api.getImportStatus()
          setImportStatus(s)
          if (s.import_status === 'completed' || s.import_status === 'failed' || s.import_status === 'cancelled') {
            clearInterval(poll)
            if (s.import_status === 'completed') {
              setTimeout(() => window.location.reload(), 500)
            } else {
              setImporting(false)
              setError(s.import_progress?.error || `Import ${s.import_status}`)
            }
          }
        } catch {
          clearInterval(poll)
          setImporting(false)
        }
      }, 1000)
    } catch (e: any) {
      setImporting(false)
      setError(e.message)
    }
  }

  const isModuleAvailable = (mod: string) => {
    if (!folderInfo) return false
    if (mod === 'hosp') return folderInfo.valid
    if (mod === 'icu') return folderInfo.icu?.some((f: any) => f.found)
    if (mod === 'note') return folderInfo.note?.some((f: any) => f.found)
    return false
  }

  return (
    <div className="bg-white rounded-lg border border-indigo-200 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">Import Additional Data</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
      </div>

      {/* Folder path */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">MIMIC-IV Data Folder</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={folderPath}
            onChange={e => setFolderPath(e.target.value)}
            className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="/path/to/mimic-iv"
          />
          <button onClick={handleBrowse} className="px-3 py-1.5 bg-gray-100 border border-gray-300 rounded text-sm hover:bg-gray-200">
            Browse
          </button>
          <button onClick={() => handleValidate(folderPath)} className="px-3 py-1.5 bg-indigo-50 border border-indigo-300 rounded text-sm text-indigo-700 hover:bg-indigo-100">
            Validate
          </button>
        </div>
        {folderValid === true && <p className="text-xs text-green-600 mt-1">Folder validated successfully</p>}
        {folderValid === false && <p className="text-xs text-red-600 mt-1">Invalid folder structure</p>}
      </div>

      {/* Existing patients only toggle */}
      {folderValid && (
        <div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={existingPatientsOnly}
              onChange={e => setExistingPatientsOnly(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm font-medium text-gray-700">Import for existing patients only</span>
          </label>
          <p className="text-xs text-gray-500 mt-1 ml-6">
            Only add missing data for the {status?.total_patients?.toLocaleString() || 0} patients already imported. No new patients will be added.
          </p>
        </div>
      )}

      {/* Modules */}
      {folderValid && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Modules</label>
          <div className="flex gap-3">
            {ALL_MODULES.map(mod => {
              const alreadyImported = importedModules.includes(mod)
              const available = isModuleAvailable(mod)
              return (
                <label key={mod} className={`flex items-center gap-2 px-3 py-2 rounded border text-sm ${
                  alreadyImported ? 'bg-green-50 border-green-200 text-green-700' :
                  !available ? 'bg-gray-50 border-gray-200 text-gray-400' :
                  selectedModules.includes(mod) ? 'bg-indigo-50 border-indigo-300 text-indigo-700' :
                  'bg-white border-gray-200 text-gray-700'
                }`}>
                  {alreadyImported ? (
                    <span className="text-green-600">&#10003;</span>
                  ) : (
                    <input
                      type="checkbox"
                      checked={selectedModules.includes(mod)}
                      onChange={() => toggleModule(mod)}
                      disabled={!available}
                    />
                  )}
                  {mod}
                  {alreadyImported && <span className="text-xs">(imported)</span>}
                  {!available && !alreadyImported && <span className="text-xs">(not found)</span>}
                </label>
              )
            })}
          </div>
        </div>
      )}

      {/* Patient limit */}
      {folderValid && !existingPatientsOnly && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Patient Limit</label>
          <select
            value={patientLimit ?? 'all'}
            onChange={e => setPatientLimit(e.target.value === 'all' ? null : Number(e.target.value))}
            className="px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {PATIENT_LIMITS.map(opt => (
              <option key={opt.label} value={opt.value ?? 'all'}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}

      {/* Import progress */}
      {importing && importStatus && (
        <div className="bg-indigo-50 rounded p-3">
          <p className="text-sm font-medium text-indigo-800">
            Importing... Stage: {importStatus.import_progress?.stage || '...'} ({importStatus.import_progress?.stage_index || 0}/{importStatus.import_progress?.stages_total || 13})
          </p>
          <p className="text-xs text-indigo-600 mt-1">{importStatus.import_progress?.detail || ''}</p>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleStartImport}
          disabled={!canImport}
          className="px-4 py-2 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {importing ? 'Importing...' : 'Start Import'}
        </button>
        {!importing && (
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors">
            Cancel
          </button>
        )}
      </div>
    </div>
  )
}

export default function Dashboard({ status }: DashboardProps) {
  const [demographics, setDemographics] = useState<any>(null)
  const [utilization, setUtilization] = useState<any>(null)
  const [clinical, setClinical] = useState<any>(null)
  const [missingness, setMissingness] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showSupplement, setShowSupplement] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getDemographics().catch(() => null),
      api.getUtilization().catch(() => null),
      api.getClinical().catch(() => null),
      api.getMissingness().catch(() => null),
    ]).then(([d, u, c, m]) => {
      setDemographics(d)
      setUtilization(u)
      setClinical(c)
      setMissingness(m)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading dashboard data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
          {status?.imported_modules?.length > 0 && (
            <div className="flex items-center gap-1.5">
              {status.imported_modules.map((mod: string) => (
                <span key={mod} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                  {mod}
                </span>
              ))}
            </div>
          )}
          <button
            onClick={() => setShowSupplement(!showSupplement)}
            className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            + Import More Data
          </button>
        </div>
        <div className="flex gap-2">
          <StatCard label="Patients" value={status?.total_patients || 0} />
          <StatCard label="Encounters" value={status?.total_encounters || 0} />
        </div>
      </div>

      {showSupplement && (
        <SupplementImportPanel status={status} onClose={() => setShowSupplement(false)} />
      )}

      {/* Demographics */}
      {demographics && (
        <Panel title="Demographics">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Age histogram */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Age Distribution</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={demographics.age_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="age" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Gender pie */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Gender Distribution</h4>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={demographics.gender_distribution}
                    dataKey="count"
                    nameKey="gender"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ gender, count }) => `${gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : gender}: ${count}`}
                  >
                    {demographics.gender_distribution.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Race bar chart */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Race/Ethnicity</h4>
              <ResponsiveContainer width="100%" height={Math.max(200, (demographics.race_distribution?.length || 0) * 30)}>
                <BarChart data={demographics.race_distribution} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" fontSize={12} />
                  <YAxis type="category" dataKey="race" width={180} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#06b6d4" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Mortality */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Mortality</h4>
              <div className="flex gap-4 mt-4">
                <div className="flex-1 bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <p className="text-sm text-green-700">Alive</p>
                  <p className="text-3xl font-bold text-green-800">{demographics.mortality.alive.toLocaleString()}</p>
                </div>
                <div className="flex-1 bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                  <p className="text-sm text-red-700">Deceased</p>
                  <p className="text-3xl font-bold text-red-800">{demographics.mortality.deceased.toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>
        </Panel>
      )}

      {/* Utilization */}
      {utilization && (
        <Panel title="Utilization">
          <div className="space-y-6">
            {/* ICU stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard label="Total ICU Stays" value={utilization.icu_stats.total_icu_stays} />
              <StatCard label="Avg ICU LOS (days)" value={utilization.icu_stats.avg_icu_los} />
              <StatCard label="Patients with ICU" value={utilization.icu_stats.patients_with_icu} />
              <StatCard
                label="% with ICU Stay"
                value={
                  utilization.icu_stats.total_patients
                    ? `${Math.round((utilization.icu_stats.patients_with_icu / utilization.icu_stats.total_patients) * 100)}%`
                    : '0%'
                }
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Admissions over time */}
              <div>
                <h4 className="text-sm font-medium text-gray-600 mb-2">Admissions Over Time</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={utilization.admissions_by_month}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" fontSize={11} angle={-45} textAnchor="end" height={60} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#4f46e5" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Avg LOS by admission type */}
              <div>
                <h4 className="text-sm font-medium text-gray-600 mb-2">Avg Length of Stay by Admission Type (days)</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={utilization.los_by_admission_type}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="admission_type" fontSize={11} angle={-30} textAnchor="end" height={80} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="avg_los" fill="#10b981" name="Avg LOS (days)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </Panel>
      )}

      {/* Clinical */}
      {clinical && (
        <Panel title="Clinical Distributions">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top diagnoses */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Top 20 Diagnoses</h4>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={clinical.top_diagnoses} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" fontSize={11} />
                  <YAxis type="category" dataKey="icd_code" width={70} fontSize={10} />
                  <Tooltip
                    formatter={(value: number) => [value, 'Count']}
                    labelFormatter={(label: string) => {
                      const dx = clinical.top_diagnoses.find((d: any) => d.icd_code === label)
                      return dx ? `${label}: ${dx.long_title}` : label
                    }}
                  />
                  <Bar dataKey="count" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top labs */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Top 20 Labs</h4>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={clinical.top_labs} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" fontSize={11} />
                  <YAxis type="category" dataKey="label" width={120} fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Top medications */}
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">Top 20 Medications</h4>
              <ResponsiveContainer width="100%" height={500}>
                <BarChart data={clinical.top_medications} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" fontSize={11} />
                  <YAxis type="category" dataKey="drug" width={120} fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Panel>
      )}

      {/* Missingness */}
      {missingness && (
        <Panel title="Data Completeness">
          <div className="space-y-3">
            {missingness.completeness.map((item: any) => (
              <div key={item.data_type} className="flex items-center gap-4">
                <div className="w-52 text-sm text-gray-700 truncate" title={item.data_type}>
                  {item.data_type}
                </div>
                <div className="flex-1 bg-gray-100 rounded-full h-5 relative overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${item.pct}%`,
                      backgroundColor: item.pct > 80 ? '#10b981' : item.pct > 50 ? '#f59e0b' : '#ef4444',
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-gray-700">
                    {item.pct}% ({item.non_null.toLocaleString()} / {item.total.toLocaleString()})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  )
}
