import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Badge from '../components/common/Badge'

export default function EncounterBrowser() {
  const navigate = useNavigate()
  const [patientSearch, setPatientSearch] = useState('')
  const [admissionType, setAdmissionType] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)

  const fetchEncounters = useCallback((pageNum: number) => {
    setLoading(true)
    const params: Record<string, string> = { page: String(pageNum) }
    if (patientSearch.trim()) params.patient = patientSearch.trim()
    if (admissionType) params.admission_type = admissionType
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo

    api.getEncounters(params)
      .then((data) => {
        setResults(data)
        setPage(pageNum)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [patientSearch, admissionType, dateFrom, dateTo])

  useEffect(() => {
    fetchEncounters(1)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchEncounters(1)
  }

  const encounters = results?.results || []
  const totalCount = results?.count || 0

  const formatDate = (dt: string | null) => {
    if (!dt) return '\u2014'
    return new Date(dt).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  }

  const formatLOS = (admit: string, disch: string | null) => {
    if (!admit || !disch) return '\u2014'
    const days = (new Date(disch).getTime() - new Date(admit).getTime()) / (1000 * 60 * 60 * 24)
    return `${days.toFixed(1)}d`
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800">Encounters</h2>

      {/* Search + Filters */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="w-40">
            <label className="block text-xs font-medium text-gray-500 mb-1">Subject ID</label>
            <input
              type="text"
              value={patientSearch}
              onChange={(e) => setPatientSearch(e.target.value)}
              placeholder="Filter by patient..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div className="w-44">
            <label className="block text-xs font-medium text-gray-500 mb-1">Admission Type</label>
            <select
              value={admissionType}
              onChange={(e) => setAdmissionType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All</option>
              <option value="EMERGENCY">Emergency</option>
              <option value="ELECTIVE">Elective</option>
              <option value="URGENT">Urgent</option>
              <option value="OBSERVATION ADMIT">Observation</option>
              <option value="SURGICAL SAME DAY ADMISSION">Surgical Same Day</option>
              <option value="DIRECT EMER.">Direct Emergency</option>
              <option value="EU OBSERVATION">EU Observation</option>
              <option value="AMBULATORY OBSERVATION">Ambulatory Obs.</option>
              <option value="DIRECT OBSERVATION">Direct Observation</option>
            </select>
          </div>
          <div className="w-40">
            <label className="block text-xs font-medium text-gray-500 mb-1">Admit From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="w-40">
            <label className="block text-xs font-medium text-gray-500 mb-1">Admit To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
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
        {loading && encounters.length === 0 ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full border-2 border-gray-300 border-t-primary-600 h-8 w-8 mx-auto" />
          </div>
        ) : encounters.length === 0 ? (
          <p className="p-8 text-center text-gray-500 text-sm">No encounters found</p>
        ) : (
          <>
            <div className="px-4 py-2 border-b border-gray-100 text-xs text-gray-500">
              {totalCount} encounter{totalCount !== 1 ? 's' : ''} found
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">HADM ID</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Subject ID</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Admission</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Discharge</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">LOS</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Type</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Discharge Location</th>
                    <th className="px-4 py-2.5 text-left font-medium text-gray-500">Expired</th>
                  </tr>
                </thead>
                <tbody>
                  {encounters.map((e: any) => (
                    <tr
                      key={e.hadm_id}
                      onClick={() => navigate(`/patients/${e.subject_id}`)}
                      className="border-b border-gray-100 cursor-pointer hover:bg-primary-50 transition-colors"
                    >
                      <td className="px-4 py-2.5 font-medium text-primary-700">{e.hadm_id}</td>
                      <td className="px-4 py-2.5 text-gray-700">{e.subject_id}</td>
                      <td className="px-4 py-2.5 text-gray-700">{formatDate(e.admittime)}</td>
                      <td className="px-4 py-2.5 text-gray-700">{formatDate(e.dischtime)}</td>
                      <td className="px-4 py-2.5 text-gray-700">{formatLOS(e.admittime, e.dischtime)}</td>
                      <td className="px-4 py-2.5">
                        <Badge
                          label={e.admission_type}
                          variant={e.admission_type === 'EMERGENCY' ? 'danger' :
                                   e.admission_type === 'ELECTIVE' ? 'info' :
                                   e.admission_type === 'URGENT' ? 'warning' : 'default'}
                        />
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 text-xs">{e.discharge_location || '\u2014'}</td>
                      <td className="px-4 py-2.5">
                        {e.hospital_expire_flag ? (
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
                  onClick={() => fetchEncounters(page - 1)}
                  disabled={!results?.previous}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-md disabled:opacity-30 hover:bg-gray-50"
                >
                  Previous
                </button>
                <span className="text-xs text-gray-500">Page {page}</span>
                <button
                  onClick={() => fetchEncounters(page + 1)}
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
