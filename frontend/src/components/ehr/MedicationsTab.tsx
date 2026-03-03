import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import DataTable, { Column } from '../common/DataTable'

interface MedicationsTabProps {
  hadmId: number
}

export default function MedicationsTab({ hadmId }: MedicationsTabProps) {
  const [meds, setMeds] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterMedications(hadmId)
      .then((data) => {
        const results = data.results || data
        setMeds(results.sort((a: any, b: any) => {
          if (!a.starttime) return 1
          if (!b.starttime) return -1
          return new Date(a.starttime).getTime() - new Date(b.starttime).getTime()
        }))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />

  const columns: Column<any>[] = [
    { key: 'drug', label: 'Drug', render: (r) => <span className="font-medium">{r.drug}</span> },
    { key: 'route', label: 'Route' },
    {
      key: 'dose',
      label: 'Dose',
      render: (r) => r.dose_val_rx ? `${r.dose_val_rx} ${r.dose_unit_rx || ''}`.trim() : '\u2014',
    },
    {
      key: 'starttime',
      label: 'Start',
      render: (r) => formatTime(r.starttime),
    },
    {
      key: 'stoptime',
      label: 'Stop',
      render: (r) => formatTime(r.stoptime),
    },
  ]

  return (
    <DataTable
      columns={columns}
      data={meds}
      emptyMessage="No medications for this encounter"
      rowKey={(r) => r.id}
    />
  )
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
