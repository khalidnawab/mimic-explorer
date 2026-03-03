import { useState, useEffect } from 'react'
import { api } from '../../api/client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

interface VitalsTabProps {
  hadmId: number
}

const VITAL_GROUPS = [
  { key: 'heart rate', label: 'Heart Rate', unit: 'bpm', color: '#ef4444' },
  { key: 'systolic', label: 'Blood Pressure (Systolic)', unit: 'mmHg', color: '#3b82f6' },
  { key: 'diastolic', label: 'Blood Pressure (Diastolic)', unit: 'mmHg', color: '#6366f1' },
  { key: 'spo2', label: 'SpO2', unit: '%', color: '#10b981' },
  { key: 'temperature', label: 'Temperature', unit: '', color: '#f59e0b' },
  { key: 'respiratory rate', label: 'Respiratory Rate', unit: '/min', color: '#8b5cf6' },
]

export default function VitalsTab({ hadmId }: VitalsTabProps) {
  const [vitals, setVitals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getEncounterVitals(hadmId, { page_size: '1000' })
      .then((data) => {
        setVitals(data.results || data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [hadmId])

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded" />
  if (vitals.length === 0) return <p className="text-gray-500 text-sm py-4">No vitals for this encounter</p>

  const charts = VITAL_GROUPS.map((group) => {
    const data = vitals
      .filter((v) => v.label?.toLowerCase().includes(group.key) && v.valuenum != null)
      .sort((a, b) => new Date(a.charttime).getTime() - new Date(b.charttime).getTime())
      .map((v) => ({
        time: new Date(v.charttime).getTime(),
        timeLabel: formatTime(v.charttime),
        value: v.valuenum,
      }))
    return { ...group, data }
  }).filter((g) => g.data.length > 0)

  if (charts.length === 0) return <p className="text-gray-500 text-sm py-4">No charted vitals data</p>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {charts.map((chart) => (
        <div key={chart.key} className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            {chart.label}
            {chart.unit && <span className="text-gray-400 font-normal ml-1">({chart.unit})</span>}
          </h4>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="timeLabel"
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10 }}
                domain={['auto', 'auto']}
                width={40}
              />
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.timeLabel || ''}
                formatter={(val: number) => [val.toFixed(1), chart.label]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={chart.color}
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  )
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${(d.getMonth() + 1)}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
