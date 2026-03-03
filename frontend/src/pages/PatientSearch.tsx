import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Badge from '../components/common/Badge'

export default function PatientSearch() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [gender, setGender] = useState('')
  const [ageMin, setAgeMin] = useState('')
  const [ageMax, setAgeMax] = useState('')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)

  const fetchPatients = useCallback((pageNum: number) => {
    setLoading(true)
    const params: Record<string, string> = { page: String(pageNum) }
    if (search.trim()) params.search = search.trim()
    if (gender) params.gender = gender
    if (ageMin) params.anchor_age_min = ageMin
    if (ageMax) params.anchor_age_max = ageMax

    api.getPatients(params)
      .then((data) => {
        setResults(data)
        setPage(pageNum)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [search, gender, ageMin, ageMax])

  useEffect(() => {
    fetchPatients(1)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchPatients(1)
  }

  const patients = results?.results || []
  const totalCount = results?.count || 0

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">Patients</h2>

      {/* Search + Filters */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Subject ID</label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by subject ID..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div className="w-32">
            <label className="block text-xs font-medium text-gray-500 mb-1">Gender</label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>
          <div className="w-24">
            <label className="block text-xs font-medium text-gray-500 mb-1">Age Min</label>
            <input
              type="number"
              value={ageMin}
              onChange={(e) => setAgeMin(e.target.value)}
              placeholder="Min"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="w-24">
            <label className="block text-xs font-medium text-gray-500 mb-1">Age Max</label>
            <input
              type="number"
              value={ageMax}
              onChange={(e) => setAgeMax(e.target.value)}
              placeholder="Max"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Results */}
      <div className="bg-white rounded-lg border border-gray-200">
        {loading && patients.length === 0 ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full border-2 border-gray-300 border-t-primary-600 h-8 w-8 mx-auto" />
          </div>
        ) : patients.length === 0 ? (
          <p className="p-8 text-center text-gray-500 text-sm">No patients found</p>
        ) : (
          <>
            <div className="px-4 py-2 border-b border-gray-100 text-xs text-gray-500">
              {totalCount} patient{totalCount !== 1 ? 's' : ''} found
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Subject ID</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Gender</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Age</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Encounters</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Deceased</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((p: any) => (
                    <tr
                      key={p.subject_id}
                      onClick={() => navigate(`/patients/${p.subject_id}`)}
                      className="border-b border-gray-100 cursor-pointer hover:bg-primary-50 transition-colors"
                    >
                      <td className="px-4 py-2.5 font-medium text-primary-700">{p.subject_id}</td>
                      <td className="px-4 py-2.5">
                        <Badge
                          label={p.gender === 'M' ? 'Male' : p.gender === 'F' ? 'Female' : p.gender}
                          variant={p.gender === 'M' ? 'info' : 'default'}
                        />
                      </td>
                      <td className="px-4 py-2.5 text-gray-700">{p.anchor_age}</td>
                      <td className="px-4 py-2.5 text-gray-700">{p.encounter_count ?? '\u2014'}</td>
                      <td className="px-4 py-2.5">
                        {p.dod ? (
                          <Badge label="Yes" variant="danger" />
                        ) : (
                          <Badge label="No" variant="success" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {(results?.next || results?.previous) && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <button
                  onClick={() => fetchPatients(page - 1)}
                  disabled={!results?.previous}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-30 hover:bg-gray-50"
                >
                  Previous
                </button>
                <span className="text-xs text-gray-500">Page {page}</span>
                <button
                  onClick={() => fetchPatients(page + 1)}
                  disabled={!results?.next}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-30 hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
