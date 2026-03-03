import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { api } from '../api/client'

const COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function CohortDetail() {
  const { id } = useParams<{ id: string }>()
  const cohortId = Number(id)

  const [cohort, setCohort] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [members, setMembers] = useState<any>(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [groupFilter, setGroupFilter] = useState('')
  const [loading, setLoading] = useState(true)

  // Compare state
  const [allCohorts, setAllCohorts] = useState<any[]>([])
  const [compareId, setCompareId] = useState<string>('')
  const [comparison, setComparison] = useState<any>(null)
  const [comparing, setComparing] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [c, s, cohortsList] = await Promise.all([
          api.getCohort(cohortId),
          api.getCohortStats(cohortId),
          api.getCohorts(),
        ])
        setCohort(c)
        setStats(s)
        setAllCohorts((cohortsList.results || cohortsList).filter((co: any) => co.id !== cohortId))
      } catch { /* empty */ }
      setLoading(false)
    }
    load()
  }, [cohortId])

  useEffect(() => {
    loadMembers()
  }, [cohortId, page, search, groupFilter])

  async function loadMembers() {
    const params: Record<string, string> = { page: String(page) }
    if (search) params.search = search
    if (groupFilter) params.group = groupFilter
    try {
      const data = await api.getCohortMembers(cohortId, params)
      setMembers(data)
    } catch { /* empty */ }
  }

  async function handleCompare() {
    if (!compareId) return
    setComparing(true)
    try {
      const data = await api.compareCohorts(cohortId, Number(compareId))
      setComparison(data)
    } catch { /* empty */ }
    setComparing(false)
  }

  function renderCriteria(criteria: any) {
    if (!criteria) return <span className="text-gray-400">No criteria defined</span>
    const parts: string[] = []
    for (const c of (criteria.inclusion || [])) {
      switch (c.type) {
        case 'diagnosis':
          parts.push(`Diagnosis ICD starts with "${c.icd_code}"${c.icd_version ? ` (v${c.icd_version})` : ''}`)
          break
        case 'lab':
          parts.push(`Lab "${c.label}"${c.operator ? ` ${c.operator} ${c.value}` : ''}`)
          break
        case 'vital':
          parts.push(`Vital "${c.label}"${c.operator ? ` ${c.operator} ${c.value}` : ''}`)
          break
        case 'medication':
          parts.push(`Medication contains "${c.drug}"`)
          break
        case 'age':
          parts.push(`Age ${c.operator || '>='} ${c.value}`)
          break
        case 'gender':
          parts.push(`Gender = ${c.value === 'M' ? 'Male' : 'Female'}`)
          break
      }
    }
    for (const c of (criteria.exclusion || [])) {
      parts.push(`EXCLUDE: ${c.type} "${c.icd_code || c.label || c.drug || c.value}"`)
    }
    return parts.length > 0
      ? parts.map((p, i) => <span key={i} className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded mr-1 mb-1">{p}</span>)
      : <span className="text-gray-400">No criteria (all patients)</span>
  }

  if (loading) return <div className="text-gray-500">Loading cohort...</div>
  if (!cohort) return <div className="text-red-500">Cohort not found</div>

  const genderData = stats?.gender_distribution
    ? Object.entries(stats.gender_distribution).map(([k, v]) => ({
        name: k === 'M' ? 'Male' : k === 'F' ? 'Female' : k,
        value: v as number,
      }))
    : []

  const ageData = stats?.age_distribution
    ? Object.entries(stats.age_distribution)
        .filter(([_, v]) => (v as number) > 0)
        .map(([k, v]) => ({ range: k, count: v as number }))
    : []

  const groupLabels = stats?.group_distribution ? Object.keys(stats.group_distribution) : []
  const totalPages = members ? Math.ceil(members.count / members.page_size) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/research/cohorts" className="text-primary-600 hover:text-primary-700 text-sm">&larr; All Cohorts</Link>
        <h2 className="text-xl font-bold text-gray-800">{cohort.name}</h2>
      </div>

      {cohort.description && (
        <p className="text-sm text-gray-600">{cohort.description}</p>
      )}

      {/* Criteria Summary */}
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Criteria</h3>
        <div className="flex flex-wrap">{renderCriteria(cohort.criteria)}</div>
      </div>

      {/* Stats Panel */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-primary-700">{stats.patient_count?.toLocaleString()}</div>
            <div className="text-xs text-gray-500 mt-1">Patients</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-primary-700">{stats.encounter_count?.toLocaleString()}</div>
            <div className="text-xs text-gray-500 mt-1">Encounters</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-primary-700">{stats.avg_age ?? '-'}</div>
            <div className="text-xs text-gray-500 mt-1">Avg Age</div>
          </div>
          <div className="bg-white border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-primary-700">{stats.mortality_rate}%</div>
            <div className="text-xs text-gray-500 mt-1">Mortality ({stats.mortality_count})</div>
          </div>
        </div>
      )}

      {/* Charts Row */}
      {stats && (genderData.length > 0 || ageData.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {genderData.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Gender Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={genderData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                    outerRadius={70} label={({ name, value }) => `${name}: ${value}`}>
                    {genderData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          {ageData.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Age Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={ageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Members Table */}
      <div className="bg-white border rounded-lg">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">
            Members {members ? `(${members.count.toLocaleString()})` : ''}
          </h3>
          <div className="flex items-center gap-2">
            <input
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              placeholder="Search patient ID..."
              className="border rounded px-2 py-1 text-sm w-40"
            />
            {groupLabels.length > 0 && (
              <select value={groupFilter} onChange={e => { setGroupFilter(e.target.value); setPage(1) }}
                className="border rounded px-2 py-1 text-sm">
                <option value="">All groups</option>
                {groupLabels.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            )}
          </div>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Patient ID</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Gender</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600">Age</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Encounter</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Admit Time</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Type</th>
              {groupLabels.length > 0 && (
                <th className="text-left px-4 py-2 font-medium text-gray-600">Group</th>
              )}
              <th className="text-left px-4 py-2 font-medium text-gray-600">Expired</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {members?.results?.map((m: any, i: number) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-4 py-2">
                  <Link to={`/patients/${m.subject_id}`} className="text-primary-600 hover:underline">
                    {m.subject_id}
                  </Link>
                </td>
                <td className="px-4 py-2">{m.gender === 'M' ? 'Male' : m.gender === 'F' ? 'Female' : m.gender}</td>
                <td className="px-4 py-2 text-right">{m.anchor_age}</td>
                <td className="px-4 py-2">{m.hadm_id ?? '-'}</td>
                <td className="px-4 py-2 text-gray-500">{m.admittime ? new Date(m.admittime).toLocaleString() : '-'}</td>
                <td className="px-4 py-2">{m.admission_type || '-'}</td>
                {groupLabels.length > 0 && (
                  <td className="px-4 py-2">
                    <span className="bg-primary-50 text-primary-700 text-xs px-2 py-0.5 rounded">{m.group_label || '-'}</span>
                  </td>
                )}
                <td className="px-4 py-2">
                  {m.hospital_expire_flag ? <span className="text-red-600 font-medium">Yes</span> : 'No'}
                </td>
              </tr>
            ))}
            {members && members.results?.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                {cohort.patient_count ? 'No members match your filter' : 'Cohort not yet executed. Go back and click Execute.'}
              </td></tr>
            )}
          </tbody>
        </table>
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 p-3 border-t">
            <button onClick={() => setPage(p => p - 1)} disabled={page <= 1}
              className="px-3 py-1 border rounded text-sm disabled:opacity-30">Prev</button>
            <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages}
              className="px-3 py-1 border rounded text-sm disabled:opacity-30">Next</button>
          </div>
        )}
      </div>

      {/* Compare Panel */}
      <div className="bg-white border rounded-lg p-4 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">Compare with Another Cohort</h3>
        {allCohorts.length === 0 ? (
          <p className="text-sm text-gray-400">No other cohorts available to compare.</p>
        ) : (
          <div className="flex items-center gap-3">
            <select value={compareId} onChange={e => setCompareId(e.target.value)}
              className="border rounded px-2 py-1.5 text-sm w-64">
              <option value="">Select cohort...</option>
              {allCohorts.map((c: any) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button onClick={handleCompare} disabled={!compareId || comparing}
              className="px-4 py-1.5 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50">
              {comparing ? 'Comparing...' : 'Compare'}
            </button>
          </div>
        )}

        {comparison && (
          <div className="mt-4">
            <table className="w-full text-sm border rounded">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Metric</th>
                  <th className="text-right px-4 py-2 font-medium text-primary-700">{comparison.cohort_a.name}</th>
                  <th className="text-right px-4 py-2 font-medium text-cyan-700">{comparison.cohort_b.name}</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="px-4 py-2 text-gray-600">Patients</td>
                  <td className="px-4 py-2 text-right font-medium">{comparison.cohort_a.patient_count}</td>
                  <td className="px-4 py-2 text-right font-medium">{comparison.cohort_b.patient_count}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-600">Encounters</td>
                  <td className="px-4 py-2 text-right font-medium">{comparison.cohort_a.encounter_count}</td>
                  <td className="px-4 py-2 text-right font-medium">{comparison.cohort_b.encounter_count}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-600">Avg Age</td>
                  <td className="px-4 py-2 text-right">{comparison.cohort_a.avg_age ?? '-'}</td>
                  <td className="px-4 py-2 text-right">{comparison.cohort_b.avg_age ?? '-'}</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-600">Gender (M/F)</td>
                  <td className="px-4 py-2 text-right">
                    {comparison.cohort_a.gender_distribution?.M ?? 0} / {comparison.cohort_a.gender_distribution?.F ?? 0}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {comparison.cohort_b.gender_distribution?.M ?? 0} / {comparison.cohort_b.gender_distribution?.F ?? 0}
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-600">Mortality Rate</td>
                  <td className="px-4 py-2 text-right">{comparison.cohort_a.mortality_rate}%</td>
                  <td className="px-4 py-2 text-right">{comparison.cohort_b.mortality_rate}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
