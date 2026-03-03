import Button from '../common/Button'

interface DataAcquisitionGuideProps {
  onClose: () => void
}

export default function DataAcquisitionGuide({ onClose }: DataAcquisitionGuideProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">How to Get MIMIC-IV Data</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>

        <div className="px-6 py-4 space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800">
              You'll need the MIMIC-IV dataset to use MIMIC Explorer. It's free but requires a short credentialing process (typically 3-7 days).
            </p>
          </div>

          <GuideStep
            number={1}
            title="Create a PhysioNet Account"
            description="Create a free account with your institutional email."
            link="https://physionet.org/register/"
            linkText="PhysioNet Registration"
          />

          <GuideStep
            number={2}
            title="Complete CITI Training"
            description='Complete the "Data or Specimens Only Research" course under Human Subjects Research. This takes approximately 3-5 hours.'
            link="https://about.citiprogram.org/"
            linkText="CITI Program"
          />

          <GuideStep
            number={3}
            title="Submit Credentialing Application"
            description="Upload your CITI training completion report and fill in your research purpose. Wait for approval (typically 1-5 business days)."
            link="https://physionet.org/settings/credentialing/"
            linkText="PhysioNet Credentialing"
          />

          <GuideStep
            number={4}
            title="Sign the Data Use Agreement"
            description="Once credentialed, request access to MIMIC-IV and sign the DUA. Access is typically granted immediately."
            link="https://physionet.org/content/mimiciv/"
            linkText="MIMIC-IV on PhysioNet"
          />

          <GuideStep
            number={5}
            title="Download the Dataset"
            description="Download the MIMIC-IV Clinical Data (hosp + icu modules). Optionally also download MIMIC-IV-Note for clinical notes."
          />

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">Expected Folder Structure</h3>
            <pre className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 overflow-x-auto">{`mimic-iv/
├── hosp/
│   ├── patients.csv.gz        ✅ Required
│   ├── admissions.csv.gz      ✅ Required
│   ├── diagnoses_icd.csv.gz   ✅ Required
│   ├── procedures_icd.csv.gz  ✅ Required
│   ├── labevents.csv.gz       ✅ Required
│   ├── prescriptions.csv.gz   ✅ Required
│   ├── d_labitems.csv.gz      ✅ Required
│   ├── d_icd_diagnoses.csv.gz ✅ Required
│   └── d_icd_procedures.csv.gz ✅ Required
├── icu/                        (Optional)
│   ├── icustays.csv.gz
│   ├── chartevents.csv.gz
│   └── d_items.csv.gz
└── note/                       (Optional)
    ├── discharge.csv.gz
    └── radiology.csv.gz`}</pre>
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-2">What Each File Contains</h3>
            <div className="space-y-3 text-sm">
              <div>
                <h4 className="font-medium text-gray-700">Hospital Module (hosp/)</h4>
                <ul className="mt-1 space-y-1 text-gray-600 text-xs">
                  <li><strong>patients</strong> — Patient demographics: ID, gender, anchor age, date of death</li>
                  <li><strong>admissions</strong> — Hospital admissions: admit/discharge times, type, location, insurance, language, marital status, race</li>
                  <li><strong>diagnoses_icd</strong> — ICD-9/10 diagnosis codes assigned per admission</li>
                  <li><strong>procedures_icd</strong> — ICD-9/10 procedure codes performed per admission</li>
                  <li><strong>labevents</strong> — Lab test results: test name, value, units, reference ranges, flags</li>
                  <li><strong>prescriptions</strong> — Medication orders: drug name, dose, route, start/stop times</li>
                  <li><strong>d_labitems / d_icd_*</strong> — Reference tables mapping code IDs to human-readable names</li>
                  <li><strong>transfers</strong> — (optional) Ward-to-ward transfers within a hospital stay</li>
                  <li><strong>emar</strong> — (optional) Electronic medication administration records</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">ICU Module (icu/)</h4>
                <ul className="mt-1 space-y-1 text-gray-600 text-xs">
                  <li><strong>icustays</strong> — ICU stays: care unit, length of stay, in/out times</li>
                  <li><strong>chartevents</strong> — Charted observations including vital signs (heart rate, blood pressure, SpO2, temperature, respiratory rate)</li>
                  <li><strong>d_items</strong> — Reference table mapping chart item IDs to names</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-700">Notes Module (note/) — separate PhysioNet download</h4>
                <ul className="mt-1 space-y-1 text-gray-600 text-xs">
                  <li><strong>discharge</strong> — Discharge summary notes (free-text clinical narratives)</li>
                  <li><strong>radiology</strong> — Radiology report notes (free-text imaging reports)</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-700">
            <strong>How import works:</strong> All files are linked by <code className="bg-gray-200 px-1 rounded">subject_id</code> (patient) and{' '}
            <code className="bg-gray-200 px-1 rounded">hadm_id</code> (hospital admission). The importer first loads patients, then joins all other data
            against existing patients. If you set a patient limit, only that many patients are loaded and all downstream data is automatically scoped to those patients.
            Files can be <code className="bg-gray-200 px-1 rounded">.csv</code> or <code className="bg-gray-200 px-1 rounded">.csv.gz</code> (gzip compressed).
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-amber-800 text-sm">
              <strong>Disk space:</strong> The full dataset is ~6-7 GB compressed.
              After import, the database will be 200 MB to 15 GB depending on import settings.
              Ensure at least 25 GB of free disk space for a full import.
            </p>
          </div>
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4">
          <Button onClick={onClose} className="w-full">Got it</Button>
        </div>
      </div>
    </div>
  )
}

function GuideStep({
  number,
  title,
  description,
  link,
  linkText,
}: {
  number: number
  title: string
  description: string
  link?: string
  linkText?: string
}) {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">
        {number}
      </div>
      <div>
        <h3 className="font-semibold text-gray-800">{title}</h3>
        <p className="text-gray-600 text-sm mt-1">{description}</p>
        {link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-sm mt-1 inline-block"
          >
            {linkText || link} →
          </a>
        )}
      </div>
    </div>
  )
}
