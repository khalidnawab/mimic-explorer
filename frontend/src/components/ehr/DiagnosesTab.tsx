import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import DataTable, { Column } from '../common/DataTable'

interface DiagnosesTabProps {
  hadmId: number
}

export default function DiagnosesTab({ hadmId }: DiagnosesTabProps) {
  const [diagnoses, setDiagnoses] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterDiagnoses(hadmId)
      .then((data) => {
        const results = data.results || data
        setDiagnoses(results.sort((a: any, b: any) => (a.seq_num || 999) - (b.seq_num || 999)))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />

  const columns: Column<any>[] = [
    { key: 'seq_num', label: '#', className: 'w-12' },
    { key: 'icd_code', label: 'ICD Code', className: 'w-28' },
    { key: 'icd_version', label: 'Ver', className: 'w-12' },
    { key: 'long_title', label: 'Description' },
  ]

  return (
    <DataTable
      columns={columns}
      data={diagnoses}
      emptyMessage="No diagnoses for this encounter"
      rowKey={(r) => r.id}
    />
  )
}
