import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import Badge from '../common/Badge'

interface LabsTabProps {
  hadmId: number
}

export default function LabsTab({ hadmId }: LabsTabProps) {
  const [labs, setLabs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterLabs(hadmId, { page_size: '500' })
      .then((data) => {
        setLabs(data.results || data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />
  if (labs.length === 0) return <p className="text-gray-500 text-sm py-4">No lab results for this encounter</p>

  // Group by category
  const groups: Record<string, any[]> = {}
  for (const lab of labs) {
    const cat = lab.category || 'Other'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(lab)
  }

  const sortedCategories = Object.keys(groups).sort()

  return (
    <div className="space-y-6">
      {sortedCategories.map((cat) => (
        <div key={cat}>
          <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">{cat}</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Test</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Value</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Units</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Ref Range</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Flag</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Time</th>
                </tr>
              </thead>
              <tbody>
                {groups[cat]
                  .sort((a, b) => new Date(a.charttime).getTime() - new Date(b.charttime).getTime())
                  .map((lab, i) => {
                    const isAbnormal = lab.flag && lab.flag.toLowerCase() === 'abnormal'
                    return (
                      <tr key={lab.id || i} className="border-b border-gray-100">
                        <td className="px-3 py-1.5 text-gray-700 font-medium">{lab.label}</td>
                        <td className={`px-3 py-1.5 ${isAbnormal ? 'text-red-600 font-semibold' : 'text-gray-700'}`}>
                          {lab.value ?? lab.valuenum ?? '\u2014'}
                        </td>
                        <td className="px-3 py-1.5 text-gray-500">{lab.valueuom || '\u2014'}</td>
                        <td className="px-3 py-1.5 text-gray-500">
                          {lab.ref_range_lower != null || lab.ref_range_upper != null
                            ? `${lab.ref_range_lower ?? ''} - ${lab.ref_range_upper ?? ''}`
                            : '\u2014'}
                        </td>
                        <td className="px-3 py-1.5">
                          {lab.flag ? (
                            <Badge label={lab.flag} variant={isAbnormal ? 'danger' : 'default'} />
                          ) : '\u2014'}
                        </td>
                        <td className="px-3 py-1.5 text-gray-500 whitespace-nowrap">{formatTime(lab.charttime)}</td>
                      </tr>
                    )
                  })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}

function formatTime(dateStr: string): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
