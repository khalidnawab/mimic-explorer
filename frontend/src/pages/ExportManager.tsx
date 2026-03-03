import { useState, useEffect } from 'react'
import { api } from '../api/client'

const DATA_TYPES = [
  { key: 'demographics', label: 'Demographics' },
  { key: 'encounters', label: 'Encounters' },
  { key: 'labs', label: 'Lab Results' },
  { key: 'vitals', label: 'Vital Signs' },
  { key: 'diagnoses', label: 'Diagnoses' },
  { key: 'medications', label: 'Medications' },
  { key: 'notes', label: 'Clinical Notes' },
]

export default function ExportManager() {
  const [cohorts, setCohorts] = useState<any[]>([])
  const [source, setSource] = useState<'cohort' | 'patients'>('cohort')
  const [cohortId, setCohortId] = useState<string>('')
  const [patientIds, setPatientIds] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['demographics', 'encounters'])
  const [format, setFormat] = useState<'csv' | 'json'>('csv')
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadCohorts() {
      try {
        const data = await api.getCohorts()
        setCohorts(data.results || data || [])
      } catch { /* empty */ }
    }
    loadCohorts()
  }, [])

  function toggleType(key: string) {
    setSelectedTypes(prev =>
      prev.includes(key) ? prev.filter(t => t !== key) : [...prev, key]
    )
  }

  async function handleExport() {
    setError('')
    if (selectedTypes.length === 0) { setError('Select at least one data type'); return }

    const params: any = { format, data_types: selectedTypes }
    if (source === 'cohort') {
      if (!cohortId) { setError('Select a cohort'); return }
      params.cohort_id = Number(cohortId)
    } else {
      const ids = patientIds.split(',').map(s => s.trim()).filter(Boolean).map(Number)
      if (ids.length === 0) { setError('Enter at least one patient ID'); return }
      params.patient_ids = ids
    }

    setExporting(true)
    try {
      if (format === 'csv') {
        const blob = await api.exportData(params) as Blob
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'mimic_export.csv'
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const data = await api.exportData(params)
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'mimic_export.json'
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (e: any) {
      setError(e.message)
    }
    setExporting(false)
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800">Export Manager</h2>

      <div className="bg-white border rounded-lg p-4 space-y-4">
        {/* Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Data Source</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={source === 'cohort'} onChange={() => setSource('cohort')} />
              Cohort
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={source === 'patients'} onChange={() => setSource('patients')} />
              Patient IDs
            </label>
          </div>
          {source === 'cohort' ? (
            <select value={cohortId} onChange={e => setCohortId(e.target.value)}
              className="mt-2 w-full border rounded px-2 py-1.5 text-sm max-w-md">
              <option value="">Select cohort...</option>
              {cohorts.map((c: any) => (
                <option key={c.id} value={c.id}>{c.name} ({c.patient_count ?? '?'} patients)</option>
              ))}
            </select>
          ) : (
            <input value={patientIds} onChange={e => setPatientIds(e.target.value)}
              placeholder="e.g. 10006, 10011, 10023"
              className="mt-2 w-full border rounded px-2 py-1.5 text-sm max-w-md" />
          )}
        </div>

        {/* Data Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Data Types</label>
          <div className="flex flex-wrap gap-3">
            {DATA_TYPES.map(dt => (
              <label key={dt.key} className="flex items-center gap-1.5 text-sm">
                <input type="checkbox" checked={selectedTypes.includes(dt.key)}
                  onChange={() => toggleType(dt.key)} />
                {dt.label}
              </label>
            ))}
          </div>
        </div>

        {/* Format */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={format === 'csv'} onChange={() => setFormat('csv')} />
              CSV
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" checked={format === 'json'} onChange={() => setFormat('json')} />
              JSON
            </label>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button onClick={handleExport} disabled={exporting}
          className="px-4 py-2 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50">
          {exporting ? 'Exporting...' : 'Download Export'}
        </button>
      </div>
    </div>
  )
}
