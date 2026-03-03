import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

interface Criterion {
  type: string
  icd_code?: string
  icd_version?: number
  label?: string
  operator?: string
  value?: number | string
  drug?: string
}

interface CriteriaState {
  inclusion: Criterion[]
  exclusion: Criterion[]
}

const EMPTY_CRITERION: Criterion = { type: 'diagnosis' }

export default function CohortBuilder() {
  const [cohorts, setCohorts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [criteria, setCriteria] = useState<CriteriaState>({ inclusion: [], exclusion: [] })
  const [previewCount, setPreviewCount] = useState<number | null>(null)
  const [executing, setExecuting] = useState<number | null>(null)
  const [error, setError] = useState('')

  useEffect(() => { loadCohorts() }, [])

  async function loadCohorts() {
    try {
      const data = await api.getCohorts()
      setCohorts(data.results || data)
    } catch { /* empty */ }
    setLoading(false)
  }

  function addCriterion(list: 'inclusion' | 'exclusion') {
    setCriteria(prev => ({
      ...prev,
      [list]: [...prev[list], { ...EMPTY_CRITERION }],
    }))
  }

  function updateCriterion(list: 'inclusion' | 'exclusion', idx: number, updates: Partial<Criterion>) {
    setCriteria(prev => ({
      ...prev,
      [list]: prev[list].map((c, i) => i === idx ? { ...c, ...updates } : c),
    }))
  }

  function removeCriterion(list: 'inclusion' | 'exclusion', idx: number) {
    setCriteria(prev => ({
      ...prev,
      [list]: prev[list].filter((_, i) => i !== idx),
    }))
  }

  async function handlePreview() {
    setError('')
    try {
      const res = await api.search(criteria)
      setPreviewCount(res.count)
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function handleCreate() {
    if (!name.trim()) { setError('Name is required'); return }
    setError('')
    try {
      await api.createCohort({ name, description, criteria })
      setShowForm(false)
      setName('')
      setDescription('')
      setCriteria({ inclusion: [], exclusion: [] })
      setPreviewCount(null)
      loadCohorts()
    } catch (e: any) {
      setError(e.message)
    }
  }

  async function handleExecute(id: number) {
    setExecuting(id)
    try {
      await api.executeCohort(id)
      loadCohorts()
    } catch { /* empty */ }
    setExecuting(null)
  }

  async function handleDelete(id: number) {
    if (!window.confirm('Are you sure you want to delete this cohort? This action cannot be reversed.')) return
    try {
      await api.deleteCohort(id)
      loadCohorts()
    } catch { /* empty */ }
  }

  function renderCriterionForm(c: Criterion, list: 'inclusion' | 'exclusion', idx: number) {
    return (
      <div key={idx} className="flex flex-wrap items-center gap-2 p-2 bg-gray-50 rounded">
        <select
          value={c.type}
          onChange={e => updateCriterion(list, idx, { type: e.target.value })}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="diagnosis">Diagnosis</option>
          <option value="lab">Lab</option>
          <option value="vital">Vital</option>
          <option value="medication">Medication</option>
          <option value="age">Age</option>
          <option value="gender">Gender</option>
        </select>

        {c.type === 'diagnosis' && (
          <>
            <input
              placeholder="ICD code prefix"
              value={c.icd_code || ''}
              onChange={e => updateCriterion(list, idx, { icd_code: e.target.value })}
              className="border rounded px-2 py-1 text-sm w-32"
            />
            <select
              value={c.icd_version ?? ''}
              onChange={e => updateCriterion(list, idx, { icd_version: e.target.value ? Number(e.target.value) : undefined })}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="">Any version</option>
              <option value="9">ICD-9</option>
              <option value="10">ICD-10</option>
            </select>
          </>
        )}

        {(c.type === 'lab' || c.type === 'vital') && (
          <>
            <input
              placeholder="Label (e.g. Glucose)"
              value={c.label || ''}
              onChange={e => updateCriterion(list, idx, { label: e.target.value })}
              className="border rounded px-2 py-1 text-sm w-36"
            />
            <select
              value={c.operator || ''}
              onChange={e => updateCriterion(list, idx, { operator: e.target.value })}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="">Any</option>
              <option value=">">{'>'}</option>
              <option value=">=">{'>='}</option>
              <option value="<">{'<'}</option>
              <option value="<=">{'<='}</option>
              <option value="=">=</option>
            </select>
            <input
              type="number"
              placeholder="Value"
              value={c.value ?? ''}
              onChange={e => updateCriterion(list, idx, { value: e.target.value ? Number(e.target.value) : undefined })}
              className="border rounded px-2 py-1 text-sm w-24"
            />
          </>
        )}

        {c.type === 'medication' && (
          <input
            placeholder="Drug name"
            value={c.drug || ''}
            onChange={e => updateCriterion(list, idx, { drug: e.target.value })}
            className="border rounded px-2 py-1 text-sm w-44"
          />
        )}

        {c.type === 'age' && (
          <>
            <select
              value={c.operator || '>='}
              onChange={e => updateCriterion(list, idx, { operator: e.target.value })}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value=">=">{'>='}</option>
              <option value=">">{'>'}</option>
              <option value="<=">{'<='}</option>
              <option value="<">{'<'}</option>
              <option value="=">=</option>
            </select>
            <input
              type="number"
              placeholder="Age"
              value={c.value ?? ''}
              onChange={e => updateCriterion(list, idx, { value: e.target.value ? Number(e.target.value) : undefined })}
              className="border rounded px-2 py-1 text-sm w-20"
            />
          </>
        )}

        {c.type === 'gender' && (
          <select
            value={(c.value as string) || ''}
            onChange={e => updateCriterion(list, idx, { value: e.target.value })}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value="">Select</option>
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
        )}

        <button
          onClick={() => removeCriterion(list, idx)}
          className="text-red-500 hover:text-red-700 text-sm px-1"
        >
          Remove
        </button>
      </div>
    )
  }

  if (loading) return <div className="text-gray-500">Loading cohorts...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">Cohort Builder</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 text-sm"
        >
          {showForm ? 'Cancel' : 'New Cohort'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white border rounded-lg p-4 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
                placeholder="e.g. Heart Failure Cohort"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <input
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
                placeholder="Optional description"
              />
            </div>
          </div>

          {/* Inclusion Criteria */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-green-700">Inclusion Criteria (AND)</h3>
              <button onClick={() => addCriterion('inclusion')} className="text-sm text-primary-600 hover:text-primary-700">+ Add</button>
            </div>
            <div className="space-y-2">
              {criteria.inclusion.map((c, i) => renderCriterionForm(c, 'inclusion', i))}
              {criteria.inclusion.length === 0 && <p className="text-xs text-gray-400">No inclusion criteria (matches all patients)</p>}
            </div>
          </div>

          {/* Exclusion Criteria */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-red-700">Exclusion Criteria</h3>
              <button onClick={() => addCriterion('exclusion')} className="text-sm text-primary-600 hover:text-primary-700">+ Add</button>
            </div>
            <div className="space-y-2">
              {criteria.exclusion.map((c, i) => renderCriterionForm(c, 'exclusion', i))}
              {criteria.exclusion.length === 0 && <p className="text-xs text-gray-400">No exclusion criteria</p>}
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex items-center gap-3">
            <button onClick={handlePreview} className="px-3 py-1.5 border rounded text-sm hover:bg-gray-50">
              Preview Count
            </button>
            {previewCount !== null && (
              <span className="text-sm text-gray-600">{previewCount} encounters match</span>
            )}
            <button onClick={handleCreate} className="px-4 py-1.5 bg-primary-600 text-white rounded text-sm hover:bg-primary-700">
              Create Cohort
            </button>
          </div>
        </div>
      )}

      {/* Cohorts Table */}
      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Name</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600">Patients</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600">Encounters</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Created</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {cohorts.map((c: any) => (
              <tr key={c.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 font-medium">
                  <Link to={`/research/cohorts/${c.id}`} className="text-primary-600 hover:underline">{c.name}</Link>
                </td>
                <td className="px-4 py-2 text-right">{c.patient_count ?? '-'}</td>
                <td className="px-4 py-2 text-right">{c.encounter_count ?? '-'}</td>
                <td className="px-4 py-2 text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-2 text-right space-x-2">
                  <button
                    onClick={() => handleExecute(c.id)}
                    disabled={executing === c.id}
                    className="text-primary-600 hover:text-primary-700 disabled:opacity-50"
                  >
                    {executing === c.id ? 'Running...' : 'Execute'}
                  </button>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {cohorts.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No cohorts yet. Create one above.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
