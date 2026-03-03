import { useState, useEffect } from 'react'
import { fetchFHIR } from '../api/client'

const RESOURCE_TYPES = [
  'Patient',
  'Encounter',
  'Observation',
  'Condition',
  'Procedure',
  'MedicationRequest',
  'DocumentReference',
] as const

type ResourceType = (typeof RESOURCE_TYPES)[number]

interface SearchField {
  name: string
  label: string
  placeholder: string
}

const SEARCH_FIELDS: Record<ResourceType, SearchField[]> = {
  Patient: [
    { name: '_id', label: 'ID', placeholder: 'mimic-12345' },
    { name: 'gender', label: 'Gender', placeholder: 'male or female' },
  ],
  Encounter: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'date', label: 'Date', placeholder: 'ge2150-01-01 or le2150-12-31' },
  ],
  Observation: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'encounter', label: 'Encounter', placeholder: 'Encounter/mimic-20000' },
    { name: 'category', label: 'Category', placeholder: 'laboratory or vital-signs' },
    { name: 'code', label: 'Code', placeholder: 'Glucose, Heart Rate, ...' },
    { name: 'date', label: 'Date', placeholder: 'ge2150-01-01' },
  ],
  Condition: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'encounter', label: 'Encounter', placeholder: 'Encounter/mimic-20000' },
    { name: 'code', label: 'ICD Code', placeholder: 'I10' },
  ],
  Procedure: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'encounter', label: 'Encounter', placeholder: 'Encounter/mimic-20000' },
  ],
  MedicationRequest: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'encounter', label: 'Encounter', placeholder: 'Encounter/mimic-20000' },
  ],
  DocumentReference: [
    { name: 'patient', label: 'Patient', placeholder: 'Patient/mimic-12345' },
    { name: 'encounter', label: 'Encounter', placeholder: 'Encounter/mimic-20000' },
    { name: 'type', label: 'Note Type', placeholder: 'Discharge summary' },
  ],
}

export default function FHIRExplorer() {
  const [resourceType, setResourceType] = useState<ResourceType>('Patient')
  const [params, setParams] = useState<Record<string, string>>({})
  const [resourceId, setResourceId] = useState('')
  const [response, setResponse] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capability, setCapability] = useState<any>(null)
  const [showCapability, setShowCapability] = useState(false)

  useEffect(() => {
    fetchFHIR('/metadata').then(setCapability).catch(() => {})
  }, [])

  useEffect(() => {
    setParams({})
    setResourceId('')
    setResponse(null)
    setError(null)
  }, [resourceType])

  const buildUrl = () => {
    let path = `/${resourceType}/`
    if (resourceId.trim()) {
      path = `/${resourceType}/${resourceId.trim()}/`
    } else {
      const searchParams = new URLSearchParams()
      for (const [k, v] of Object.entries(params)) {
        if (v.trim()) searchParams.set(k, v.trim())
      }
      const qs = searchParams.toString()
      if (qs) path += `?${qs}`
    }
    return path
  }

  const execute = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const data = await fetchFHIR(buildUrl())
      setResponse(data)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const fields = SEARCH_FIELDS[resourceType]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">FHIR Explorer</h2>
        <p className="text-sm text-gray-500 mt-1">Browse FHIR R4 resources served on-the-fly from MIMIC-IV data</p>
      </div>

      {/* Capability Statement */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <button
          onClick={() => setShowCapability(!showCapability)}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-primary-700"
        >
          <span className={`transform transition-transform ${showCapability ? 'rotate-90' : ''}`}>&#9654;</span>
          CapabilityStatement (/fhir/metadata)
        </button>
        {showCapability && capability && (
          <pre className="mt-3 p-3 bg-gray-50 rounded text-xs overflow-auto max-h-64 text-gray-700">
            {JSON.stringify(capability, null, 2)}
          </pre>
        )}
      </div>

      {/* Query Builder */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        <h3 className="font-semibold text-gray-900">Query Builder</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resource Type</label>
            <select
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value as ResourceType)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {RESOURCE_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resource ID <span className="text-gray-400">(leave empty for search)</span>
            </label>
            <input
              type="text"
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
              placeholder="mimic-12345"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {!resourceId.trim() && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-600">Search Parameters</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {fields.map((field) => (
                <div key={field.name}>
                  <label className="block text-xs font-medium text-gray-500 mb-1">{field.label}</label>
                  <input
                    type="text"
                    value={params[field.name] || ''}
                    onChange={(e) => setParams({ ...params, [field.name]: e.target.value })}
                    placeholder={field.placeholder}
                    className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* URL Preview */}
        <div className="flex items-center gap-3">
          <code className="flex-1 text-xs bg-gray-50 px-3 py-2 rounded border text-gray-600 overflow-auto">
            GET /fhir{buildUrl()}
          </code>
          <button
            onClick={execute}
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Response */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {response && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">
              Response
              {response.resourceType === 'Bundle' && response.total != null && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({response.total} total{response.entry ? `, showing ${response.entry.length}` : ''})
                </span>
              )}
            </h3>
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
              {response.resourceType}
            </span>
          </div>
          <pre className="p-3 bg-gray-50 rounded text-xs overflow-auto max-h-[600px] text-gray-700">
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
