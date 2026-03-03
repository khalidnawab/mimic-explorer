import { useState } from 'react'
import { api } from '../api/client'

export default function Search() {
  const [diagCode, setDiagCode] = useState('')
  const [labLabel, setLabLabel] = useState('')
  const [labOp, setLabOp] = useState('')
  const [labVal, setLabVal] = useState('')
  const [medication, setMedication] = useState('')
  const [ageOp, setAgeOp] = useState('>=')
  const [ageVal, setAgeVal] = useState('')
  const [gender, setGender] = useState('')

  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [saveName, setSaveName] = useState('')
  const [saved, setSaved] = useState(false)

  function buildCriteria() {
    const inclusion: any[] = []
    if (diagCode) inclusion.push({ type: 'diagnosis', icd_code: diagCode })
    if (labLabel) {
      const c: any = { type: 'lab', label: labLabel }
      if (labOp && labVal) { c.operator = labOp; c.value = Number(labVal) }
      inclusion.push(c)
    }
    if (medication) inclusion.push({ type: 'medication', drug: medication })
    if (ageVal) inclusion.push({ type: 'age', operator: ageOp, value: Number(ageVal) })
    if (gender) inclusion.push({ type: 'gender', value: gender })
    return { inclusion, exclusion: [] }
  }

  async function handleSearch(p = 1) {
    setLoading(true)
    setSaved(false)
    try {
      const data = await api.search(buildCriteria(), p)
      setResults(data)
      setPage(p)
    } catch { /* empty */ }
    setLoading(false)
  }

  async function handleSaveQuery() {
    if (!saveName.trim()) return
    try {
      await api.createQuery({ name: saveName, query_definition: buildCriteria() })
      setSaved(true)
    } catch { /* empty */ }
  }

  async function handleCreateCohort() {
    if (!saveName.trim()) return
    try {
      const cohort = await api.createCohort({ name: saveName, criteria: buildCriteria() })
      await api.executeCohort(cohort.id)
      setSaved(true)
    } catch { /* empty */ }
  }

  const totalPages = results ? Math.ceil(results.count / results.page_size) : 0

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800">Structured Search</h2>

      <div className="bg-white border rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Diagnosis (ICD code)</label>
            <input value={diagCode} onChange={e => setDiagCode(e.target.value)}
              placeholder="e.g. 428" className="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Lab label</label>
            <input value={labLabel} onChange={e => setLabLabel(e.target.value)}
              placeholder="e.g. Glucose" className="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">Lab op</label>
              <select value={labOp} onChange={e => setLabOp(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
                <option value="">Any</option>
                <option value=">">{'>'}</option>
                <option value=">=">{'>='}</option>
                <option value="<">{'<'}</option>
                <option value="<=">{'<='}</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">Lab value</label>
              <input type="number" value={labVal} onChange={e => setLabVal(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Medication</label>
            <input value={medication} onChange={e => setMedication(e.target.value)}
              placeholder="e.g. Aspirin" className="w-full border rounded px-2 py-1.5 text-sm" />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">Age</label>
              <select value={ageOp} onChange={e => setAgeOp(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
                <option value=">=">{'>='}</option>
                <option value=">">{'>'}</option>
                <option value="<=">{'<='}</option>
                <option value="<">{'<'}</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">&nbsp;</label>
              <input type="number" value={ageVal} onChange={e => setAgeVal(e.target.value)}
                placeholder="65" className="w-full border rounded px-2 py-1.5 text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Gender</label>
            <select value={gender} onChange={e => setGender(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm">
              <option value="">Any</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>
        </div>
        <div className="mt-4">
          <button onClick={() => handleSearch(1)} disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {results && (
        <>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">{results.count} encounters found</span>
            <div className="flex items-center gap-2">
              <input value={saveName} onChange={e => setSaveName(e.target.value)}
                placeholder="Name..." className="border rounded px-2 py-1 text-sm w-40" />
              <button onClick={handleSaveQuery}
                className="px-3 py-1 border rounded text-sm hover:bg-gray-50">Save as Query</button>
              <button onClick={handleCreateCohort}
                className="px-3 py-1 bg-primary-600 text-white rounded text-sm hover:bg-primary-700">Create Cohort</button>
              {saved && <span className="text-green-600 text-sm">Saved!</span>}
            </div>
          </div>

          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Patient ID</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Encounter</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Admit Time</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Type</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Diagnoses</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.results.map((r: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-2">{r.subject_id}</td>
                    <td className="px-4 py-2">{r.hadm_id}</td>
                    <td className="px-4 py-2 text-gray-500">{r.admittime ? new Date(r.admittime).toLocaleString() : '-'}</td>
                    <td className="px-4 py-2">{r.admission_type}</td>
                    <td className="px-4 py-2 text-xs text-gray-500 max-w-xs truncate">
                      {r.diagnoses?.map((d: any) => d.icd_code).join(', ') || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button onClick={() => handleSearch(page - 1)} disabled={page <= 1}
                className="px-3 py-1 border rounded text-sm disabled:opacity-30">Prev</button>
              <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
              <button onClick={() => handleSearch(page + 1)} disabled={page >= totalPages}
                className="px-3 py-1 border rounded text-sm disabled:opacity-30">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
