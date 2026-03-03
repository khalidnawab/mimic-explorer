import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import Badge from '../common/Badge'

interface OverviewTabProps {
  hadmId: number
}

export default function OverviewTab({ hadmId }: OverviewTabProps) {
  const [encounter, setEncounter] = useState<any>(null)
  const [diagnoses, setDiagnoses] = useState<any[]>([])
  const [vitals, setVitals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.getEncounter(hadmId),
      api.getEncounterDiagnoses(hadmId),
      api.getEncounterVitals(hadmId, { page_size: '200' }),
    ]).then(([enc, diag, vit]) => {
      setEncounter(enc)
      setDiagnoses((diag.results || diag).slice(0, 10))
      setVitals(vit.results || vit)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <LoadingPlaceholder />
  if (!encounter) return <p className="text-gray-500 text-sm">No encounter data</p>

  const latestVital = (label: string) => {
    const matches = vitals
      .filter((v: any) => v.label?.toLowerCase().includes(label.toLowerCase()) && v.valuenum != null)
      .sort((a: any, b: any) => new Date(b.charttime).getTime() - new Date(a.charttime).getTime())
    return matches[0]
  }

  const hr = latestVital('heart rate')
  const sbp = latestVital('systolic')
  const dbp = latestVital('diastolic')
  const spo2 = latestVital('spo2')
  const temp = latestVital('temperature')
  const rr = latestVital('respiratory rate')

  const vitalSnapshots = [
    hr && { label: 'HR', value: `${Math.round(hr.valuenum)} bpm` },
    sbp && dbp && { label: 'BP', value: `${Math.round(sbp.valuenum)}/${Math.round(dbp.valuenum)} mmHg` },
    sbp && !dbp && { label: 'SBP', value: `${Math.round(sbp.valuenum)} mmHg` },
    spo2 && { label: 'SpO2', value: `${Math.round(spo2.valuenum)}%` },
    temp && { label: 'Temp', value: `${temp.valuenum.toFixed(1)} ${temp.valueuom || '\u00b0F'}` },
    rr && { label: 'RR', value: `${Math.round(rr.valuenum)} /min` },
  ].filter(Boolean) as { label: string; value: string }[]

  return (
    <div className="space-y-6">
      {/* Admission Summary */}
      <div>
        <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Admission Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InfoItem label="Admitted" value={formatDate(encounter.admittime)} />
          <InfoItem label="Discharged" value={encounter.dischtime ? formatDate(encounter.dischtime) : 'In hospital'} />
          <InfoItem label="Type" value={encounter.admission_type} />
          <InfoItem label="Disposition" value={encounter.discharge_location || '\u2014'} />
        </div>
      </div>

      {/* Vitals Snapshot */}
      {vitalSnapshots.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Latest Vitals</h4>
          <div className="flex flex-wrap gap-3">
            {vitalSnapshots.map((v) => (
              <div key={v.label} className="bg-blue-50 rounded-lg px-4 py-2">
                <p className="text-xs text-blue-600 font-medium">{v.label}</p>
                <p className="text-lg font-semibold text-blue-900">{v.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Diagnoses */}
      {diagnoses.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Top Diagnoses
          </h4>
          <div className="space-y-1.5">
            {diagnoses.map((dx: any, i: number) => (
              <div key={dx.id || i} className="flex items-start gap-2 text-sm">
                <Badge label={`#${dx.seq_num}`} variant="info" />
                <span className="text-gray-700">{dx.long_title || dx.icd_code}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-800">{value}</p>
    </div>
  )
}

function LoadingPlaceholder() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-16 bg-gray-100 rounded" />
      ))}
    </div>
  )
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
