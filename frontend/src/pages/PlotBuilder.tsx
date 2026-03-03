import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts'
import { api } from '../api/client'

type PlotType = 'histogram' | 'boxplot' | 'timeseries'

export default function PlotBuilder() {
  const [dataType, setDataType] = useState<'labs' | 'vitals'>('labs')
  const [items, setItems] = useState<string[]>([])
  const [selectedItem, setSelectedItem] = useState('')
  const [plotType, setPlotType] = useState<PlotType>('histogram')
  const [cohorts, setCohorts] = useState<any[]>([])
  const [cohortId, setCohortId] = useState<string>('')
  const [chartData, setChartData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    async function loadItems() {
      try {
        const data = dataType === 'labs' ? await api.getLabItems() : await api.getVitalItems()
        setItems(data.items || data || [])
      } catch { setItems([]) }
    }
    loadItems()
  }, [dataType])

  useEffect(() => {
    async function loadCohorts() {
      try {
        const data = await api.getCohorts()
        setCohorts(data.results || data || [])
      } catch { /* empty */ }
    }
    loadCohorts()
  }, [])

  async function handleGenerate() {
    if (!selectedItem) return
    setLoading(true)

    try {
      const params: Record<string, string> = { label: selectedItem, page_size: '2000' }
      if (cohortId) params.cohort_id = cohortId

      const data = dataType === 'labs'
        ? await api.getLabs(params)
        : await api.getVitals(params)

      const rows = data.results || data || []
      const values = rows.map((r: any) => r.valuenum).filter((v: any) => v !== null && v !== undefined)

      if (plotType === 'histogram') {
        const bins = buildHistogram(values, 20)
        setChartData(bins)
      } else if (plotType === 'timeseries') {
        const tsData = rows
          .filter((r: any) => r.valuenum !== null && r.charttime)
          .sort((a: any, b: any) => new Date(a.charttime).getTime() - new Date(b.charttime).getTime())
          .map((r: any) => ({
            time: new Date(r.charttime).toLocaleDateString(),
            value: r.valuenum,
          }))
        setChartData(tsData.slice(0, 500))
      } else {
        // boxplot: show summary stats as bar
        setChartData([])
      }

      // Compute stats
      if (values.length > 0) {
        const sorted = [...values].sort((a, b) => a - b)
        setStats({
          count: values.length,
          mean: (values.reduce((a: number, b: number) => a + b, 0) / values.length).toFixed(1),
          median: sorted[Math.floor(sorted.length / 2)]?.toFixed(1),
          min: sorted[0]?.toFixed(1),
          max: sorted[sorted.length - 1]?.toFixed(1),
          q1: sorted[Math.floor(sorted.length * 0.25)]?.toFixed(1),
          q3: sorted[Math.floor(sorted.length * 0.75)]?.toFixed(1),
        })
      } else {
        setStats(null)
      }
    } catch { /* empty */ }
    setLoading(false)
  }

  function buildHistogram(values: number[], binCount: number) {
    if (values.length === 0) return []
    const min = Math.min(...values)
    const max = Math.max(...values)
    if (min === max) return [{ range: String(min), count: values.length }]
    const binWidth = (max - min) / binCount
    const bins = Array.from({ length: binCount }, (_, i) => ({
      range: `${(min + i * binWidth).toFixed(1)}`,
      count: 0,
    }))
    for (const v of values) {
      const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1)
      bins[idx].count++
    }
    return bins
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800">Plot Builder</h2>

      <div className="bg-white border rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Data Type</label>
            <select value={dataType} onChange={e => setDataType(e.target.value as any)}
              className="w-full border rounded px-2 py-1.5 text-sm">
              <option value="labs">Labs</option>
              <option value="vitals">Vitals</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Item</label>
            <select value={selectedItem} onChange={e => setSelectedItem(e.target.value)}
              className="w-full border rounded px-2 py-1.5 text-sm">
              <option value="">Select...</option>
              {items.map((item: any) => (
                <option key={typeof item === 'string' ? item : item.label} value={typeof item === 'string' ? item : item.label}>
                  {typeof item === 'string' ? item : item.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Plot Type</label>
            <select value={plotType} onChange={e => setPlotType(e.target.value as PlotType)}
              className="w-full border rounded px-2 py-1.5 text-sm">
              <option value="histogram">Histogram</option>
              <option value="timeseries">Time Series</option>
              <option value="boxplot">Summary Stats</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Cohort Filter</label>
            <select value={cohortId} onChange={e => setCohortId(e.target.value)}
              className="w-full border rounded px-2 py-1.5 text-sm">
              <option value="">All patients</option>
              {cohorts.map((c: any) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-4">
          <button onClick={handleGenerate} disabled={loading || !selectedItem}
            className="px-4 py-2 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50">
            {loading ? 'Loading...' : 'Generate Plot'}
          </button>
        </div>
      </div>

      {stats && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Summary Statistics</h3>
          <div className="grid grid-cols-7 gap-4 text-center text-sm">
            <div><div className="text-gray-500">N</div><div className="font-medium">{stats.count}</div></div>
            <div><div className="text-gray-500">Mean</div><div className="font-medium">{stats.mean}</div></div>
            <div><div className="text-gray-500">Median</div><div className="font-medium">{stats.median}</div></div>
            <div><div className="text-gray-500">Min</div><div className="font-medium">{stats.min}</div></div>
            <div><div className="text-gray-500">Q1</div><div className="font-medium">{stats.q1}</div></div>
            <div><div className="text-gray-500">Q3</div><div className="font-medium">{stats.q3}</div></div>
            <div><div className="text-gray-500">Max</div><div className="font-medium">{stats.max}</div></div>
          </div>
        </div>
      )}

      {chartData.length > 0 && (
        <div className="bg-white border rounded-lg p-4">
          <ResponsiveContainer width="100%" height={400}>
            {plotType === 'histogram' ? (
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" />
              </BarChart>
            ) : (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" angle={-45} textAnchor="end" height={80} tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#4f46e5" dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
