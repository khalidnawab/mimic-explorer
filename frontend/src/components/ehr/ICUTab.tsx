import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import Badge from '../common/Badge'

interface ICUTabProps {
  hadmId: number
}

export default function ICUTab({ hadmId }: ICUTabProps) {
  const [stays, setStays] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterICUStays(hadmId)
      .then((data) => {
        setStays(data.results || data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />
  if (stays.length === 0) return <p className="text-gray-500 text-sm py-4">No ICU stays for this encounter</p>

  return (
    <div className="space-y-4">
      {stays.map((stay: any) => (
        <div key={stay.id} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <Badge label={`Stay ${stay.stay_id}`} variant="info" />
            {stay.los != null && (
              <span className="text-sm text-gray-500">
                LOS: {Number(stay.los).toFixed(1)} days
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-xs text-gray-500">First Care Unit</p>
              <p className="font-medium text-gray-800">{stay.first_careunit || '\u2014'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Last Care Unit</p>
              <p className="font-medium text-gray-800">{stay.last_careunit || '\u2014'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Admitted to ICU</p>
              <p className="font-medium text-gray-800">{formatDate(stay.intime)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Discharged from ICU</p>
              <p className="font-medium text-gray-800">{stay.outtime ? formatDate(stay.outtime) : 'Active'}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
