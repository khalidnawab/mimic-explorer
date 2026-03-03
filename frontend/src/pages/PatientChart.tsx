import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'
import Badge from '../components/common/Badge'
import Tabs from '../components/common/Tabs'
import OverviewTab from '../components/ehr/OverviewTab'
import LabsTab from '../components/ehr/LabsTab'
import VitalsTab from '../components/ehr/VitalsTab'
import MedicationsTab from '../components/ehr/MedicationsTab'
import DiagnosesTab from '../components/ehr/DiagnosesTab'
import ProceduresTab from '../components/ehr/ProceduresTab'
import NotesTab from '../components/ehr/NotesTab'
import ICUTab from '../components/ehr/ICUTab'

export default function PatientChart() {
  const { subjectId } = useParams<{ subjectId: string }>()
  const [patient, setPatient] = useState<any>(null)
  const [icuStayMap, setIcuStayMap] = useState<Record<number, boolean>>({})
  const [selectedEncounter, setSelectedEncounter] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!subjectId) return
    setLoading(true)
    api.getPatient(Number(subjectId))
      .then((data) => {
        setPatient(data)
        // Sort encounters by date desc
        const encounters = (data.encounters || []).sort(
          (a: any, b: any) => new Date(b.admittime).getTime() - new Date(a.admittime).getTime()
        )
        if (encounters.length > 0) {
          setSelectedEncounter(encounters[0])
        }
        // Check which encounters have ICU stays
        Promise.allSettled(
          encounters.map((enc: any) =>
            api.getEncounterICUStays(enc.hadm_id).then((data) => ({
              hadmId: enc.hadm_id,
              hasICU: (data.results || data).length > 0,
            }))
          )
        ).then((results) => {
          const map: Record<number, boolean> = {}
          for (const r of results) {
            if (r.status === 'fulfilled') {
              map[r.value.hadmId] = r.value.hasICU
            }
          }
          setIcuStayMap(map)
        })
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [subjectId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full border-2 border-gray-300 border-t-primary-600 h-8 w-8" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500">Patient not found</p>
        <Link to="/patients" className="text-primary-600 hover:underline text-sm mt-2 inline-block">
          Back to search
        </Link>
      </div>
    )
  }

  const encounters = (patient.encounters || []).sort(
    (a: any, b: any) => new Date(b.admittime).getTime() - new Date(a.admittime).getTime()
  )

  return (
    <div className="space-y-4">
      {/* Back link */}
      <Link to="/patients" className="text-sm text-primary-600 hover:underline">
        &larr; Back to patients
      </Link>

      {/* Header Banner */}
      <div className="bg-white rounded-lg border border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-800">Patient {patient.subject_id}</h2>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  label={patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : patient.gender}
                  variant={patient.gender === 'M' ? 'info' : 'default'}
                />
                <span className="text-sm text-gray-600">Age {patient.anchor_age}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            {patient.dod ? (
              <div>
                <Badge label="Deceased" variant="danger" />
                <p className="text-xs text-gray-500 mt-1">{formatDate(patient.dod)}</p>
              </div>
            ) : (
              <Badge label="Alive" variant="success" />
            )}
          </div>
        </div>
      </div>

      {/* Main Layout: Sidebar + Content */}
      <div className="flex gap-4">
        {/* Left Sidebar — Encounter List */}
        <div className="w-[280px] flex-shrink-0 space-y-2">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide px-1">
            Encounters ({encounters.length})
          </h3>
          {encounters.length === 0 ? (
            <p className="text-sm text-gray-400 px-1">No encounters</p>
          ) : (
            <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
              {encounters.map((enc: any) => {
                const isSelected = selectedEncounter?.hadm_id === enc.hadm_id
                const admitDate = new Date(enc.admittime)
                const dischDate = enc.dischtime ? new Date(enc.dischtime) : null
                const los = dischDate
                  ? Math.round((dischDate.getTime() - admitDate.getTime()) / (1000 * 60 * 60 * 24) * 10) / 10
                  : null

                return (
                  <button
                    key={enc.hadm_id}
                    onClick={() => setSelectedEncounter(enc)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-gray-800">#{enc.hadm_id}</span>
                      {enc.hospital_expire_flag && (
                        <Badge label="Expired" variant="danger" />
                      )}
                    </div>
                    <p className="text-xs text-gray-500">
                      {formatDateShort(enc.admittime)}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                        {enc.admission_type}
                      </span>
                      {los != null && (
                        <span className="text-xs text-gray-400">{los}d</span>
                      )}
                    </div>
                    {enc.discharge_location && (
                      <p className="text-xs text-gray-400 mt-1 truncate">{enc.discharge_location}</p>
                    )}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Main Content — Tabbed View */}
        <div className="flex-1 min-w-0 bg-white rounded-lg border border-gray-200 p-4">
          {selectedEncounter ? (
            <Tabs
              key={selectedEncounter.hadm_id}
              tabs={[
                {
                  key: 'overview',
                  label: 'Overview',
                  content: <OverviewTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'labs',
                  label: 'Labs',
                  content: <LabsTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'vitals',
                  label: 'Vitals',
                  content: <VitalsTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'medications',
                  label: 'Medications',
                  content: <MedicationsTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'diagnoses',
                  label: 'Diagnoses',
                  content: <DiagnosesTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'procedures',
                  label: 'Procedures',
                  content: <ProceduresTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'notes',
                  label: 'Notes',
                  content: <NotesTab hadmId={selectedEncounter.hadm_id} />,
                },
                {
                  key: 'icu',
                  label: 'ICU',
                  content: <ICUTab hadmId={selectedEncounter.hadm_id} />,
                  hidden: !icuStayMap[selectedEncounter.hadm_id],
                },
              ]}
            />
          ) : (
            <p className="text-gray-500 text-sm py-8 text-center">
              Select an encounter from the sidebar
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}

function formatDateShort(dateStr: string): string {
  if (!dateStr) return '\u2014'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
