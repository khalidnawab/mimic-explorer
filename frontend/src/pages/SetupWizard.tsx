import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import StepIndicator from '../components/common/StepIndicator'
import ProgressBar from '../components/common/ProgressBar'
import Button from '../components/common/Button'
import DataAcquisitionGuide from '../components/wizard/DataAcquisitionGuide'

interface SetupWizardProps {
  onComplete: () => void
}

const STEPS = [
  { label: 'Welcome' },
  { label: 'Data Path' },
  { label: 'Validate' },
  { label: 'Configure' },
  { label: 'Import' },
  { label: 'Complete' },
]

interface ValidationResult {
  valid: boolean
  required: Array<{ file: string; found: boolean }>
  optional: Array<{ file: string; found: boolean }>
  icu: Array<{ file: string; found: boolean }>
  note: Array<{ file: string; found: boolean }>
  missing_required: string[]
}

interface ImportProgress {
  import_status: string
  import_progress: {
    stage?: string
    percent?: number
    detail?: string
    rows_imported?: number
    stage_index?: number
    stages_total?: number
    error?: string
  }
  total_patients: number
  total_encounters: number
}

export default function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(0)
  const [showGuide, setShowGuide] = useState(false)
  const [folderPath, setFolderPath] = useState('')
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [validating, setValidating] = useState(false)
  const [modules, setModules] = useState<string[]>(['hosp'])
  const [patientLimit, setPatientLimit] = useState<number | null>(1000)
  const [generateFhir] = useState(false)
  const [importProgress, setImportProgress] = useState<ImportProgress | null>(null)
  const [browsing, setBrowsing] = useState(false)
  const [error, setError] = useState('')

  const handleBrowse = async () => {
    setBrowsing(true)
    setError('')
    try {
      const result = await api.browseFolder()
      if (result.path) {
        setFolderPath(result.path)
      }
    } catch (e: any) {
      setError(e.message || 'Failed to open folder picker')
    } finally {
      setBrowsing(false)
    }
  }

  // Poll import status
  useEffect(() => {
    if (step !== 4) return
    const interval = setInterval(async () => {
      try {
        const status = await api.getImportStatus()
        setImportProgress(status)
        if (status.import_status === 'completed') {
          clearInterval(interval)
          setStep(5)
        } else if (status.import_status === 'failed') {
          clearInterval(interval)
          setError(status.import_progress?.error || 'Import failed')
        } else if (status.import_status === 'cancelled') {
          clearInterval(interval)
          setError('Import was cancelled')
        }
      } catch {
        // Ignore polling errors
      }
    }, 500)
    return () => clearInterval(interval)
  }, [step])

  const handleValidate = async () => {
    setValidating(true)
    setError('')
    try {
      const result = await api.validateFolder(folderPath)
      setValidation(result)
      if (result.valid) {
        setStep(2)
      }
    } catch (e: any) {
      setError(e.message || 'Failed to validate folder')
    } finally {
      setValidating(false)
    }
  }

  const [importing, setImporting] = useState(false)

  const handleStartImport = async () => {
    setError('')
    setImporting(true)
    try {
      await api.startImport({
        folder_path: folderPath,
        modules,
        patient_limit: patientLimit,
        generate_fhir: generateFhir,
      })
      setStep(4)
      // Poll immediately instead of waiting 2s
      try {
        const status = await api.getImportStatus()
        setImportProgress(status)
        if (status.import_status === 'completed') {
          setStep(5)
        }
      } catch {}
    } catch (e: any) {
      setError(e.message || 'Failed to start import')
    } finally {
      setImporting(false)
    }
  }

  const handleCancel = async () => {
    try {
      await api.cancelImport()
    } catch {
      // Ignore
    }
  }

  const toggleModule = (mod: string) => {
    setModules(prev =>
      prev.includes(mod) ? prev.filter(m => m !== mod) : [...prev, mod]
    )
  }

  const patientLimitOptions = [
    { value: 100, label: '100 patients (quick test)', time: '< 30 seconds' },
    { value: 1000, label: '1,000 patients (lite)', time: '~1-2 minutes' },
    { value: 5000, label: '5,000 patients (medium)', time: '~5-10 minutes' },
    { value: 10000, label: '10,000 patients (large)', time: '~10-20 minutes' },
    { value: null as number | null, label: 'All patients (full dataset)', time: '~30-60+ minutes' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">MIMIC Explorer</h1>
          <p className="text-gray-500">Setup Wizard</p>
        </div>

        {/* Step indicator */}
        <StepIndicator steps={STEPS} currentStep={step} className="justify-center mb-8" />

        {/* Step content */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {/* Step 0: Welcome */}
          {step === 0 && (
            <div className="text-center space-y-6">
              <div className="text-6xl mb-4">🏥</div>
              <h2 className="text-2xl font-bold text-gray-800">Welcome to MIMIC Explorer</h2>
              <p className="text-gray-600 max-w-md mx-auto">
                MIMIC Explorer is a research sandbox for the MIMIC-IV clinical dataset.
                You'll need the MIMIC-IV data files to get started.
              </p>
              <div className="flex justify-center gap-3">
                <Button onClick={() => setStep(1)}>I have the data</Button>
                <Button variant="outline" onClick={() => setShowGuide(true)}>
                  How to get MIMIC data
                </Button>
              </div>
            </div>
          )}

          {/* Step 1: Folder path */}
          {step === 1 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800">Select MIMIC-IV Data Folder</h2>
              <p className="text-gray-600">
                Enter the path to your MIMIC-IV data folder. It should contain <code className="bg-gray-100 px-1 rounded">hosp/</code> and optionally <code className="bg-gray-100 px-1 rounded">icu/</code> and <code className="bg-gray-100 px-1 rounded">note/</code> subdirectories.
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Folder path</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={folderPath}
                    onChange={e => setFolderPath(e.target.value)}
                    placeholder="e.g., C:\Users\you\mimic-iv or /home/you/mimic-iv"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <Button variant="outline" onClick={handleBrowse} disabled={browsing}>
                    {browsing ? 'Opening...' : 'Browse'}
                  </Button>
                </div>
              </div>

              <DataStructureReference />

              {error && <p className="text-red-600 text-sm">{error}</p>}
              <div className="flex justify-between">
                <Button variant="ghost" onClick={() => setStep(0)}>Back</Button>
                <Button onClick={handleValidate} disabled={!folderPath || validating}>
                  {validating ? 'Validating...' : 'Validate Folder'}
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Validation results */}
          {step === 2 && validation && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800">Validation Results</h2>
              {validation.valid ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-green-800 font-medium">All required files found!</p>
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800 font-medium">Missing required files:</p>
                  <ul className="mt-2 list-disc list-inside text-red-700 text-sm">
                    {validation.missing_required.map(f => <li key={f}>{f}</li>)}
                  </ul>
                </div>
              )}

              <div className="space-y-3">
                <h3 className="font-semibold text-gray-700">Required Files</h3>
                {validation.required.map(f => (
                  <FileStatus key={f.file} file={f.file} found={f.found} required />
                ))}

                <h3 className="font-semibold text-gray-700 mt-4">Optional Files</h3>
                {validation.optional.map(f => (
                  <FileStatus key={f.file} file={f.file} found={f.found} />
                ))}

                <h3 className="font-semibold text-gray-700 mt-4">ICU Module</h3>
                {validation.icu.map(f => (
                  <FileStatus key={f.file} file={f.file} found={f.found} />
                ))}

                <h3 className="font-semibold text-gray-700 mt-4">Notes Module</h3>
                {validation.note.map(f => (
                  <FileStatus key={f.file} file={f.file} found={f.found} />
                ))}
              </div>

              <div className="flex justify-between">
                <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
                <Button onClick={() => setStep(3)} disabled={!validation.valid}>
                  Configure Import
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Configuration */}
          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800">Import Configuration</h2>

              <div className="space-y-4">
                <h3 className="font-semibold text-gray-700">Modules</h3>
                <label className="flex items-center gap-2 text-gray-600">
                  <input type="checkbox" checked disabled className="rounded" />
                  <span>Hospital data (required)</span>
                </label>
                <label className="flex items-center gap-2 text-gray-600">
                  <input
                    type="checkbox"
                    checked={modules.includes('icu')}
                    onChange={() => toggleModule('icu')}
                    className="rounded"
                    disabled={!validation?.icu.every(f => f.found)}
                  />
                  <span>ICU data (vitals, ICU stays)</span>
                  {!validation?.icu.every(f => f.found) && (
                    <span className="text-xs text-gray-400">— files not found</span>
                  )}
                </label>
                <label className="flex items-center gap-2 text-gray-600">
                  <input
                    type="checkbox"
                    checked={modules.includes('note')}
                    onChange={() => toggleModule('note')}
                    className="rounded"
                    disabled={!validation?.note.some(f => f.found)}
                  />
                  <span>Clinical notes</span>
                  {!validation?.note.some(f => f.found) && (
                    <span className="text-xs text-gray-400">— files not found</span>
                  )}
                </label>
              </div>

              <div className="space-y-3">
                <h3 className="font-semibold text-gray-700">Patient Limit</h3>
                <p className="text-sm text-gray-500">
                  Limit the number of patients to import. Smaller numbers import faster. You can always import more later using the supplement import feature.
                </p>
                <div className="space-y-2">
                  {patientLimitOptions.map(opt => (
                    <label key={String(opt.value)} className="flex items-center gap-2 text-gray-600">
                      <input
                        type="radio"
                        name="patientLimit"
                        checked={patientLimit === opt.value}
                        onChange={() => setPatientLimit(opt.value)}
                        className="rounded-full"
                      />
                      <span>{opt.label}</span>
                      <span className="text-xs text-gray-400">{opt.time}</span>
                    </label>
                  ))}
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                  <strong>Heads up:</strong> Importing the full dataset (~300k patients) can take <strong>30-60+ minutes</strong> depending
                  on your hardware and disk speed. Lab events and chart events are the largest stages. We recommend starting
                  with 1,000 patients to verify everything works, then importing more later — you won't lose any data.
                </div>
              </div>

{error && <p className="text-red-600 text-sm">{error}</p>}

              <div className="flex justify-between">
                <Button variant="ghost" onClick={() => setStep(2)} disabled={importing}>Back</Button>
                <Button onClick={handleStartImport} disabled={importing}>
                  {importing ? 'Starting...' : 'Start Import'}
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Import progress */}
          {step === 4 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800">Importing Data</h2>
              <p className="text-gray-600">
                This may take a while depending on the dataset size. You can safely leave this page open.
              </p>

              {/* Always show something — spinner if no progress data yet */}
              {!importProgress?.import_progress?.stage && !error && (
                <div className="flex items-center gap-3 bg-blue-50 rounded-lg p-4">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-300 border-t-blue-600" />
                  <p className="text-blue-800 font-medium">Starting import...</p>
                </div>
              )}

              {importProgress?.import_progress?.stage && (
                <div className="space-y-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-blue-800 font-medium capitalize">
                      Stage: {importProgress.import_progress.stage?.replace(/_/g, ' ') || 'Starting...'}
                    </p>
                    {importProgress.import_progress.detail && (
                      <p className="text-blue-600 text-sm mt-1">{importProgress.import_progress.detail}</p>
                    )}
                  </div>

                  {/* Overall progress */}
                  <ProgressBar
                    percent={
                      importProgress.import_progress.stages_total
                        ? ((importProgress.import_progress.stage_index || 0) / importProgress.import_progress.stages_total) * 100
                        : 0
                    }
                    label="Overall progress"
                  />

                  {/* Stage progress */}
                  <ProgressBar
                    percent={importProgress.import_progress.percent || 0}
                    label="Current stage"
                  />

                  {importProgress.import_progress.rows_imported ? (
                    <p className="text-sm text-gray-500">
                      Rows imported: {importProgress.import_progress.rows_imported.toLocaleString()}
                    </p>
                  ) : null}
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800">{error}</p>
                  <Button variant="outline" className="mt-2" onClick={() => { setError(''); setStep(3); }}>
                    Try Again
                  </Button>
                </div>
              )}

              {!error && (
                <div className="flex justify-end">
                  <Button variant="outline" onClick={handleCancel}>Cancel Import</Button>
                </div>
              )}
            </div>
          )}

          {/* Step 5: Complete */}
          {step === 5 && (
            <div className="text-center space-y-6">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold text-gray-800">Import Complete!</h2>
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-left max-w-sm mx-auto">
                <dl className="space-y-2">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Patients</dt>
                    <dd className="font-semibold">{importProgress?.total_patients?.toLocaleString()}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Encounters</dt>
                    <dd className="font-semibold">{importProgress?.total_encounters?.toLocaleString()}</dd>
                  </div>
                </dl>
              </div>
              <Button size="lg" onClick={onComplete}>Start Exploring</Button>
            </div>
          )}
        </div>

        {/* Data acquisition guide modal */}
        {showGuide && <DataAcquisitionGuide onClose={() => setShowGuide(false)} />}
      </div>
    </div>
  )
}

function DataStructureReference() {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <span>Expected data structure</span>
        <span className="text-gray-400">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4 text-sm">
          <p className="text-gray-500">
            MIMIC Explorer expects the standard MIMIC-IV directory layout from PhysioNet.
            Files can be <code className="bg-gray-100 px-1 rounded">.csv</code> or <code className="bg-gray-100 px-1 rounded">.csv.gz</code> (compressed).
          </p>

          <div>
            <h4 className="font-semibold text-gray-700 mb-1.5">hosp/ — Hospital module (required)</h4>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-gray-100">
                <DataFileRow file="patients.csv.gz" desc="Demographics: subject_id, gender, anchor_age, date of death" required />
                <DataFileRow file="admissions.csv.gz" desc="Hospital admissions: admit/discharge times, type, location, insurance" required />
                <DataFileRow file="diagnoses_icd.csv.gz" desc="ICD diagnosis codes per admission" required />
                <DataFileRow file="procedures_icd.csv.gz" desc="ICD procedure codes per admission" required />
                <DataFileRow file="labevents.csv.gz" desc="Laboratory test results with values and reference ranges" required />
                <DataFileRow file="prescriptions.csv.gz" desc="Medication prescriptions: drug name, dose, route, timing" required />
                <DataFileRow file="d_labitems.csv.gz" desc="Reference table: lab item IDs to names" required />
                <DataFileRow file="d_icd_diagnoses.csv.gz" desc="Reference table: ICD diagnosis code descriptions" required />
                <DataFileRow file="d_icd_procedures.csv.gz" desc="Reference table: ICD procedure code descriptions" required />
                <DataFileRow file="transfers.csv.gz" desc="Ward transfers within hospital stays" />
                <DataFileRow file="emar.csv.gz" desc="Medication administration records (eMAR)" />
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="font-semibold text-gray-700 mb-1.5">icu/ — ICU module (optional)</h4>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-gray-100">
                <DataFileRow file="icustays.csv.gz" desc="ICU stays: care unit, length of stay, in/out times" />
                <DataFileRow file="chartevents.csv.gz" desc="Charted vital signs: heart rate, BP, SpO2, temperature, respiratory rate" />
                <DataFileRow file="d_items.csv.gz" desc="Reference table: chart item IDs to names" />
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="font-semibold text-gray-700 mb-1.5">note/ — Notes module (optional, separate PhysioNet download)</h4>
            <table className="w-full text-xs">
              <tbody className="divide-y divide-gray-100">
                <DataFileRow file="discharge.csv.gz" desc="Discharge summary notes (free text)" />
                <DataFileRow file="radiology.csv.gz" desc="Radiology report notes (free text)" />
              </tbody>
            </table>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded p-3 text-xs text-blue-800">
            <strong>Tip:</strong> All files are linked by <code className="bg-blue-100 px-0.5 rounded">subject_id</code> (patient) and <code className="bg-blue-100 px-0.5 rounded">hadm_id</code> (admission).
            The importer only loads data for patients present in <code className="bg-blue-100 px-0.5 rounded">patients.csv</code>, so downstream files are automatically filtered.
          </div>
        </div>
      )}
    </div>
  )
}

function DataFileRow({ file, desc, required = false }: { file: string; desc: string; required?: boolean }) {
  return (
    <tr>
      <td className="py-1 pr-2 whitespace-nowrap font-mono text-gray-600">
        {file}
        {required && <span className="text-red-400 ml-1">*</span>}
      </td>
      <td className="py-1 text-gray-500">{desc}</td>
    </tr>
  )
}

function FileStatus({ file, found, required = false }: { file: string; found: boolean; required?: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={found ? 'text-green-500' : required ? 'text-red-500' : 'text-gray-400'}>
        {found ? '✓' : '✗'}
      </span>
      <code className="bg-gray-50 px-1 rounded text-xs">{file}</code>
      {required && !found && <span className="text-red-500 text-xs">required</span>}
    </div>
  )
}
