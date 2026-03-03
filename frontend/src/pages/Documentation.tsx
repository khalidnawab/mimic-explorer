import { useState } from 'react'
import { api } from '../api/client'

function Section({ id, title, children }: { id?: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="mb-12">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b border-gray-200 pb-2">{title}</h2>
      {children}
    </section>
  )
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <h3 className="text-base font-semibold text-gray-700 mb-3">{title}</h3>
      {children}
    </div>
  )
}

function Code({ children }: { children: string }) {
  return <code className="bg-gray-100 px-1 rounded text-xs">{children}</code>
}

function Kbd({ children }: { children: string }) {
  return <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono">{children}</kbd>
}

function InfoBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800 mb-4">
      {children}
    </div>
  )
}

function TipBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800 mb-4">
      {children}
    </div>
  )
}

function EndpointTable({ rows }: { rows: [string, string, string][] }) {
  return (
    <div className="overflow-x-auto mb-6">
      <table className="w-full text-sm border border-gray-200 rounded">
        <thead>
          <tr className="bg-gray-50 text-left">
            <th className="px-3 py-2 font-semibold text-gray-700 border-b">Method</th>
            <th className="px-3 py-2 font-semibold text-gray-700 border-b">Path</th>
            <th className="px-3 py-2 font-semibold text-gray-700 border-b">Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([method, path, desc], i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-3 py-1.5 font-mono text-xs">
                <span className={`px-1.5 py-0.5 rounded font-bold ${
                  method === 'GET' ? 'bg-green-100 text-green-700' :
                  method === 'POST' ? 'bg-blue-100 text-blue-700' :
                  method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>{method}</span>
              </td>
              <td className="px-3 py-1.5 font-mono text-xs text-gray-800">{path}</td>
              <td className="px-3 py-1.5 text-gray-600">{desc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SimpleTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto mb-4">
      <table className="w-full text-sm border border-gray-200 rounded">
        <thead>
          <tr className="bg-gray-50 text-left">
            {headers.map((h, i) => (
              <th key={i} className="px-3 py-2 font-semibold text-gray-700 border-b">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, j) => (
                <td key={j} className={`px-3 py-1.5 ${j === 0 ? 'font-medium text-gray-800' : 'text-gray-600'} ${j === row.length - 1 && headers.length > 2 ? 'text-xs' : ''}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Table of contents navigation
function TOC() {
  const sections = [
    { id: 'about', label: 'About MIMIC Explorer' },
    { id: 'mimic-iv', label: 'What is MIMIC-IV?' },
    { id: 'getting-access', label: 'Getting Access to MIMIC-IV' },
    { id: 'installation', label: 'Installation & Setup' },
    { id: 'data-structure', label: 'Expected Data Structure' },
    { id: 'importing-data', label: 'Importing Data' },
    { id: 'dashboard', label: 'Using the Dashboard' },
    { id: 'patient-search', label: 'Patient Search' },
    { id: 'patient-chart', label: 'Patient Chart (EHR Viewer)' },
    { id: 'encounter-browser', label: 'Encounter Browser' },
    { id: 'research-cohorts', label: 'Research: Cohort Builder' },
    { id: 'research-search', label: 'Research: Structured Search' },
    { id: 'research-plots', label: 'Research: Plot Builder' },
    { id: 'research-export', label: 'Research: Data Export' },
    { id: 'fhir', label: 'FHIR R4 API' },
    { id: 'api-reference', label: 'REST API Reference' },
    { id: 'cli', label: 'Command Line Interface' },
    { id: 'testing', label: 'Testing' },
    { id: 'reset', label: 'Reset Application' },
  ]
  return (
    <nav className="bg-gray-50 border border-gray-200 rounded-lg p-5 mb-10">
      <h2 className="font-bold text-gray-800 mb-3">Table of Contents</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1">
        {sections.map(({ id, label }, i) => (
          <a key={id} href={`#${id}`} className="text-sm text-indigo-600 hover:text-indigo-800 hover:underline">
            {i + 1}. {label}
          </a>
        ))}
      </div>
    </nav>
  )
}

export default function Documentation() {
  const [confirmText, setConfirmText] = useState('')
  const [resetting, setResetting] = useState(false)
  const [showResetDialog, setShowResetDialog] = useState(false)

  const handleReset = async () => {
    setResetting(true)
    try {
      await api.resetApp()
      window.location.reload()
    } catch (e: any) {
      alert(`Reset failed: ${e.message}`)
      setResetting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">MIMIC Explorer Documentation</h1>
      <p className="text-gray-500 mb-8">User manual and reference guide</p>

      <TOC />

      {/* ================================================================ */}
      {/* ABOUT */}
      {/* ================================================================ */}
      <Section id="about" title="1. About MIMIC Explorer">
        <p className="text-gray-700 leading-relaxed mb-4">
          MIMIC Explorer is a locally installable EHR (Electronic Health Record) research sandbox for the MIMIC-IV
          clinical dataset. It provides a web-based interface for browsing patient records, visualizing clinical data,
          building research cohorts, and accessing data through a FHIR R4-compliant API — all running entirely on your
          local machine with no external network calls.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {([
            ['EHR Viewer', 'Browse patient records, encounters, lab results, vitals, diagnoses, procedures, medications, and clinical notes with a familiar chart-style interface.'],
            ['Dashboards', 'Visualize population demographics, hospital utilization, top diagnoses/labs/medications, and data completeness at a glance.'],
            ['Research Workbench', 'Build patient cohorts with inclusion/exclusion criteria, run structured searches, generate distribution plots, and export data in CSV or JSON.'],
            ['FHIR R4 API', 'Query your data via standards-compliant FHIR resources — Patient, Encounter, Observation, Condition, Procedure, MedicationRequest, and DocumentReference.'],
          ] as [string, string][]).map(([title, desc]) => (
            <div key={title} className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-1">{title}</h3>
              <p className="text-sm text-gray-600">{desc}</p>
            </div>
          ))}
        </div>
        <SubSection title="Key Design Principles">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Fully local</strong> — No cloud, no accounts, no network calls. All data stays on your machine.</li>
            <li><strong>Single-user</strong> — Designed for individual researchers; no authentication or multi-user access controls. Do not expose this application to the public internet.</li>
            <li><strong>Zero configuration</strong> — Install with pip, point at your MIMIC-IV files, and start exploring.</li>
            <li><strong>Research-first</strong> — Built for academic researchers working with MIMIC-IV for publications (e.g., JAMIA, JMIR).</li>
          </ul>
        </SubSection>
        <SubSection title="Architecture Overview">
          <SimpleTable
            headers={['Layer', 'Technology', 'Purpose']}
            rows={[
              ['Backend', 'Django 6.x + Django REST Framework', 'REST API, import pipeline, data queries'],
              ['Frontend', 'React 18 + TypeScript + Tailwind CSS', 'Interactive web interface (SPA)'],
              ['App Database', 'SQLite (WAL mode)', 'System config, saved queries, cohort definitions'],
              ['Clinical Database', 'DuckDB', 'Patient data, encounters, labs, vitals (fast analytics)'],
              ['FHIR', 'fhir.resources (Python)', 'On-the-fly R4 resource transformation'],
            ]}
          />
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* WHAT IS MIMIC-IV */}
      {/* ================================================================ */}
      <Section id="mimic-iv" title="2. What is MIMIC-IV?">
        <p className="text-gray-700 leading-relaxed mb-4">
          <strong>MIMIC-IV</strong> (Medical Information Mart for Intensive Care, version IV) is a large, freely available
          database of de-identified health records from patients admitted to the Beth Israel Deaconess Medical Center
          (BIDMC) in Boston, Massachusetts. It is one of the most widely used clinical research datasets in the world.
        </p>
        <SubSection title="What the Dataset Contains">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Patient demographics</strong> — Gender, age (anchor year system for de-identification), date of death</li>
            <li><strong>Hospital admissions</strong> — Admit/discharge times, admission type (emergency, elective, etc.), insurance, language, marital status, race</li>
            <li><strong>Diagnoses</strong> — ICD-9 and ICD-10 diagnosis codes assigned during each admission</li>
            <li><strong>Procedures</strong> — ICD-9 and ICD-10 procedure codes for surgeries and interventions</li>
            <li><strong>Laboratory results</strong> — Blood tests, chemistry panels, microbiology — with values, units, reference ranges, and abnormal flags</li>
            <li><strong>Medications</strong> — Prescriptions (drug name, dose, route, timing) and electronic medication administration records (eMAR)</li>
            <li><strong>ICU data</strong> — ICU stays, charted vital signs (heart rate, blood pressure, SpO2, temperature, respiratory rate)</li>
            <li><strong>Clinical notes</strong> — Discharge summaries and radiology reports (free-text narratives) via the separate MIMIC-IV-Note module</li>
          </ul>
        </SubSection>
        <SubSection title="Dataset Scale">
          <SimpleTable
            headers={['Metric', 'Approximate Count']}
            rows={[
              ['Patients', '~300,000+'],
              ['Hospital admissions', '~500,000+'],
              ['ICU stays', '~70,000+'],
              ['Lab events', '~120 million+'],
              ['Prescriptions', '~16 million+'],
              ['Diagnoses', '~5 million+'],
              ['Clinical notes', '~300,000+'],
            ]}
          />
          <p className="text-sm text-gray-500">
            Counts are approximate and vary by MIMIC-IV version. MIMIC Explorer lets you import any subset using patient limits.
          </p>
        </SubSection>
        <SubSection title="How De-identification Works">
          <p className="text-sm text-gray-700 mb-2">
            MIMIC-IV uses date-shifting and anchor years to protect patient privacy. Each patient is assigned a random
            "anchor year" that maps their actual admission dates to a shifted timeline. The <Code>anchor_age</Code> field
            represents the patient's age at their first hospital visit in the anchor year. All dates in the dataset are
            shifted consistently so that temporal relationships (e.g., time between admissions) are preserved, but actual
            calendar dates are not recoverable.
          </p>
        </SubSection>
        <SubSection title="Citing MIMIC-IV">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-700 font-mono">
            Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R. (2023).<br />
            MIMIC-IV (version 2.2). PhysioNet. https://doi.org/10.13026/6mm1-ek67
          </div>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* GETTING ACCESS */}
      {/* ================================================================ */}
      <Section id="getting-access" title="3. Getting Access to MIMIC-IV">
        <p className="text-gray-700 leading-relaxed mb-4">
          MIMIC-IV is freely available but requires a credentialing process to ensure responsible use of clinical data.
          The process typically takes <strong>3 to 7 business days</strong> from start to data download.
        </p>

        <div className="space-y-4 mb-6">
          <StepBlock number={1} title="Create a PhysioNet Account">
            <p className="text-sm text-gray-600">
              Go to <a href="https://physionet.org/register/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">physionet.org/register</a> and
              create a free account. Use your <strong>institutional email address</strong> (e.g., university or hospital email) — this is
              required for credentialing approval.
            </p>
          </StepBlock>

          <StepBlock number={2} title="Complete CITI Training">
            <p className="text-sm text-gray-600 mb-2">
              Complete the <strong>"Data or Specimens Only Research"</strong> course under Human Subjects Research through
              the <a href="https://about.citiprogram.org/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">CITI Program</a>.
              This online course covers ethical use of research data and typically takes <strong>3-5 hours</strong>.
            </p>
            <TipBox>
              When enrolling, select your institution first. If your institution isn't listed, select
              "Massachusetts Institute of Technology Affiliates" as the organization and choose the "Data or
              Specimens Only Research" course.
            </TipBox>
          </StepBlock>

          <StepBlock number={3} title="Submit Credentialing Application">
            <p className="text-sm text-gray-600">
              Go to <a href="https://physionet.org/settings/credentialing/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">PhysioNet Credentialing</a>,
              upload your CITI training completion report, and fill in your research purpose. Approval typically takes
              <strong> 1-5 business days</strong>.
            </p>
          </StepBlock>

          <StepBlock number={4} title="Sign the Data Use Agreement">
            <p className="text-sm text-gray-600">
              Once credentialed, visit the <a href="https://physionet.org/content/mimiciv/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">MIMIC-IV project page</a> on
              PhysioNet, request access, and sign the Data Use Agreement (DUA). Access is usually granted immediately after signing.
            </p>
          </StepBlock>

          <StepBlock number={5} title="Download the Dataset">
            <p className="text-sm text-gray-600 mb-2">
              Download the files you need. MIMIC-IV is split into separate modules on PhysioNet:
            </p>
            <SimpleTable
              headers={['Module', 'PhysioNet Project', 'Contents']}
              rows={[
                ['Hospital (hosp)', 'mimic-iv (main project)', 'Demographics, admissions, diagnoses, labs, medications — Required'],
                ['ICU (icu)', 'mimic-iv (main project)', 'ICU stays and charted vital signs — Optional'],
                ['Notes (note)', 'mimic-iv-note (separate project)', 'Discharge summaries and radiology reports — Optional, requires separate DUA'],
              ]}
            />
            <p className="text-sm text-gray-600">
              You can download via the PhysioNet website, <Code>wget</Code>, or the Google Cloud / AWS mirrors.
              Place all downloaded folders in a single parent directory (see Data Structure section below).
            </p>
          </StepBlock>
        </div>

        <InfoBox>
          <strong>Disk space:</strong> The full MIMIC-IV dataset is approximately 6-7 GB compressed (.csv.gz files).
          After import into MIMIC Explorer, the database will be 200 MB to 15 GB depending on how many patients
          and modules you import. We recommend at least <strong>25 GB of free disk space</strong> for a full import.
        </InfoBox>
      </Section>

      {/* ================================================================ */}
      {/* INSTALLATION */}
      {/* ================================================================ */}
      <Section id="installation" title="4. Installation & Setup">
        <SubSection title="Prerequisites">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Python 3.10 or later</strong> (see installation instructions below)</li>
            <li><strong>MIMIC-IV data files</strong> (see section 3 above)</li>
            <li>A modern web browser (Chrome, Firefox, Edge, Safari)</li>
          </ul>
        </SubSection>

        <SubSection title="Installing Python">
          <p className="text-sm text-gray-700 mb-4">
            If you don't already have Python installed, follow the instructions for your operating system below.
          </p>

          {/* Windows */}
          <div className="border border-gray-200 rounded-lg mb-4">
            <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 font-semibold text-gray-700 text-sm">
              Windows
            </div>
            <div className="px-4 py-3 space-y-3 text-sm text-gray-700">
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  Go to <a href="https://www.python.org/downloads/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">python.org/downloads</a> and
                  click the yellow <strong>"Download Python 3.x.x"</strong> button to download the installer.
                </li>
                <li>
                  Run the downloaded <Code>.exe</Code> installer. <strong>Important:</strong> On the first screen, check the box that says
                  <strong> "Add python.exe to PATH"</strong> at the bottom before clicking "Install Now". This allows you to run Python from the command line.
                </li>
                <li>
                  Click <strong>"Install Now"</strong> and wait for the installation to complete. Click "Close" when finished.
                </li>
                <li>
                  Verify the installation by opening a command prompt and typing:
                  <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs mt-2">
                    python --version
                  </div>
                  <p className="text-gray-500 text-xs mt-1">You should see something like <Code>Python 3.12.0</Code> or later.</p>
                </li>
              </ol>
              <TipBox>
                <strong>How to open Command Prompt:</strong> Press <Kbd>Win</Kbd> + <Kbd>R</Kbd>, type <Code>cmd</Code>, and press Enter.
                Or search for "Command Prompt" in the Start menu.
              </TipBox>
            </div>
          </div>

          {/* macOS */}
          <div className="border border-gray-200 rounded-lg mb-4">
            <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 font-semibold text-gray-700 text-sm">
              macOS
            </div>
            <div className="px-4 py-3 space-y-3 text-sm text-gray-700">
              <p className="text-gray-600 mb-2">
                macOS comes with an older version of Python. You'll need Python 3.10 or later. The easiest ways to install it:
              </p>
              <div className="mb-3">
                <p className="font-medium text-gray-800 mb-1">Option A: Official installer (easiest)</p>
                <ol className="list-decimal list-inside space-y-1 ml-2">
                  <li>Go to <a href="https://www.python.org/downloads/macos/" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">python.org/downloads/macos</a> and download the macOS installer (.pkg).</li>
                  <li>Double-click the downloaded <Code>.pkg</Code> file and follow the installation prompts.</li>
                  <li>The installer adds Python to your PATH automatically.</li>
                </ol>
              </div>
              <div className="mb-3">
                <p className="font-medium text-gray-800 mb-1">Option B: Homebrew</p>
                <p className="mb-1">If you have <a href="https://brew.sh" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">Homebrew</a> installed, run:</p>
                <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs">
                  brew install python
                </div>
              </div>
              <p>Verify the installation by opening Terminal and typing:</p>
              <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs">
                python3 --version
              </div>
              <p className="text-gray-500 text-xs mt-1">You should see <Code>Python 3.10.0</Code> or later.</p>
              <TipBox>
                <strong>How to open Terminal:</strong> Press <Kbd>Cmd</Kbd> + <Kbd>Space</Kbd> to open Spotlight, type <Code>Terminal</Code>, and press Enter.
                Or find it in Applications → Utilities → Terminal.
              </TipBox>
            </div>
          </div>
        </SubSection>

        <SubSection title="Installing MIMIC Explorer">
          <p className="text-sm text-gray-700 mb-3">
            Once Python is installed, open your terminal (Command Prompt on Windows, Terminal on macOS) and run:
          </p>

          {/* Windows install */}
          <div className="border border-gray-200 rounded-lg mb-4">
            <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 font-semibold text-gray-700 text-sm">
              Windows — Command Prompt
            </div>
            <div className="px-4 py-3 space-y-2 text-sm text-gray-700">
              <ol className="list-decimal list-inside space-y-2">
                <li>Press <Kbd>Win</Kbd> + <Kbd>R</Kbd>, type <Code>cmd</Code>, and press Enter to open Command Prompt.</li>
                <li>
                  Type the following command and press Enter:
                  <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs mt-2">
                    pip install mimic-explorer
                  </div>
                </li>
                <li>Wait for the installation to complete. You'll see "Successfully installed" when it's done.</li>
                <li>
                  Launch the application by typing:
                  <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs mt-2">
                    mimic-explorer
                  </div>
                </li>
              </ol>
              <InfoBox>
                If you see <Code>'pip' is not recognized</Code>, try <Code>python -m pip install mimic-explorer</Code> instead.
                If that also fails, Python may not be on your PATH — reinstall Python and make sure to check "Add python.exe to PATH".
              </InfoBox>
              <TipBox>
                If <Code>mimic-explorer</Code> is not recognized after installation, your Python Scripts folder may not be on
                your PATH. You can always use the module form instead: <Code>python -m mimic_explorer</Code>. This accepts
                all the same flags (<Code>--test</Code>, <Code>--version</Code>, <Code>--port</Code>, <Code>--data</Code>, etc.).
              </TipBox>
            </div>
          </div>

          {/* macOS install */}
          <div className="border border-gray-200 rounded-lg mb-4">
            <div className="bg-gray-50 px-4 py-2.5 border-b border-gray-200 font-semibold text-gray-700 text-sm">
              macOS — Terminal
            </div>
            <div className="px-4 py-3 space-y-2 text-sm text-gray-700">
              <ol className="list-decimal list-inside space-y-2">
                <li>Press <Kbd>Cmd</Kbd> + <Kbd>Space</Kbd>, type <Code>Terminal</Code>, and press Enter.</li>
                <li>
                  Type the following command and press Enter:
                  <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs mt-2">
                    pip3 install mimic-explorer
                  </div>
                </li>
                <li>Wait for the installation to complete. You'll see "Successfully installed" when it's done.</li>
                <li>
                  Launch the application by typing:
                  <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-xs mt-2">
                    mimic-explorer
                  </div>
                </li>
              </ol>
              <InfoBox>
                On macOS, use <Code>pip3</Code> (not <Code>pip</Code>) to ensure you're using Python 3.
                If you see a permissions error, try <Code>pip3 install --user mimic-explorer</Code>.
              </InfoBox>
              <TipBox>
                If <Code>mimic-explorer</Code> is not recognized after installation,
                use <Code>python3 -m mimic_explorer</Code> instead. This accepts all the same flags.
              </TipBox>
            </div>
          </div>

          <p className="text-sm text-gray-700">
            After running <Code>mimic-explorer</Code>, your default browser will open automatically to the setup wizard.
            If it doesn't, open your browser and go to <Code>http://localhost:8765</Code>.
          </p>
        </SubSection>

        <SubSection title="Start the Application">
          <p className="text-sm text-gray-700 mb-2">
            After installation, you can start MIMIC Explorer at any time by opening your terminal and running:
          </p>
          <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm mb-4">
            mimic-explorer
          </div>
          <p className="text-sm text-gray-700 mb-2">
            The application starts a local web server and opens your browser automatically. On first launch, you will see the
            <strong> Setup Wizard</strong> which guides you through the import process.
          </p>
        </SubSection>

        <SubSection title="Sample Test Dataset">
          <p className="text-sm text-gray-700 mb-2">
            A synthetic dataset with 10 fictional patients is included for testing and demonstration at:
          </p>
          <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm mb-2">
            tests/fixtures/mimic-iv-test/
          </div>
          <p className="text-sm text-gray-700 mb-2">
            This data is entirely made up and contains no real patient information. To try MIMIC Explorer
            without MIMIC-IV access, point the setup wizard at this folder. It includes hospital data
            (patients, admissions, labs, medications, diagnoses, procedures), ICU data (stays, vital signs),
            and discharge notes.
          </p>
          <p className="text-sm text-gray-700">
            You can also run the automated test suite against this data
            with <Code>mimic-explorer --test</Code>.
          </p>
        </SubSection>

        <SubSection title="Setup Wizard">
          <p className="text-sm text-gray-700 mb-3">
            The wizard walks you through 6 steps:
          </p>
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
            <li><strong>Welcome</strong> — Introduction with a link to the data acquisition guide if you haven't downloaded MIMIC-IV yet.</li>
            <li><strong>Data Path</strong> — Enter or browse to your MIMIC-IV data folder. An expandable reference panel shows the expected folder structure.</li>
            <li><strong>Validate</strong> — The app checks for all required and optional files, showing a checklist of what was found.</li>
            <li><strong>Configure</strong> — Choose which modules to import (Hospital is required; ICU and Notes are optional) and set a patient limit.
              Start small (100-1,000 patients) to test quickly, then import more later with the supplement import feature.</li>
            <li><strong>Import</strong> — Real-time progress bars show overall and per-stage progress. You can cancel at any time.</li>
            <li><strong>Complete</strong> — Summary of what was imported. Click "Start Exploring" to enter the main application.</li>
          </ol>
        </SubSection>

        <SubSection title="Where Data is Stored">
          <p className="text-sm text-gray-700 mb-2">
            MIMIC Explorer stores all application data in a dedicated directory:
          </p>
          <SimpleTable
            headers={['File', 'Purpose']}
            rows={[
              ['~/.mimic_explorer/mimic_explorer.db', 'SQLite database — system config, saved queries, cohort definitions'],
              ['~/.mimic_explorer/clinical.duckdb', 'DuckDB database — imported clinical data (patients, labs, etc.)'],
              ['~/.mimic_explorer/secret_key', 'Django secret key (auto-generated)'],
            ]}
          />
          <p className="text-sm text-gray-500">
            Your original MIMIC-IV CSV files are never modified. The importer reads from them and stores processed data in the databases above.
          </p>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* DATA STRUCTURE */}
      {/* ================================================================ */}
      <Section id="data-structure" title="5. Expected Data Structure">
        <p className="text-sm text-gray-700 mb-4">
          MIMIC Explorer expects the standard MIMIC-IV directory layout from PhysioNet. Files can be <Code>.csv</Code> or <Code>.csv.gz</Code> (gzip compressed).
        </p>

        <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 text-xs font-mono overflow-x-auto mb-6">{`mimic-iv/
├── hosp/                            ← Required
│   ├── patients.csv.gz              Demographics (subject_id, gender, anchor_age, dod)
│   ├── admissions.csv.gz            Hospital admissions (times, type, location, insurance)
│   ├── diagnoses_icd.csv.gz         ICD-9/10 diagnosis codes per admission
│   ├── procedures_icd.csv.gz        ICD-9/10 procedure codes per admission
│   ├── labevents.csv.gz             Lab results (value, units, reference ranges, flags)
│   ├── prescriptions.csv.gz         Medication orders (drug, dose, route, timing)
│   ├── d_labitems.csv.gz            Reference: lab item IDs → names
│   ├── d_icd_diagnoses.csv.gz       Reference: ICD diagnosis code descriptions
│   ├── d_icd_procedures.csv.gz      Reference: ICD procedure code descriptions
│   ├── transfers.csv.gz             (optional) Ward transfers within hospital stays
│   └── emar.csv.gz                  (optional) Medication administration records
├── icu/                             ← Optional
│   ├── icustays.csv.gz              ICU stays (care unit, LOS, in/out times)
│   ├── chartevents.csv.gz           Vital signs (HR, BP, SpO2, temp, RR)
│   └── d_items.csv.gz              Reference: chart item IDs → names
└── note/                            ← Optional (separate PhysioNet download)
    ├── discharge.csv.gz             Discharge summary notes (free text)
    └── radiology.csv.gz             Radiology report notes (free text)`}</pre>

        <SubSection title="File Details">
          <div className="overflow-x-auto mb-6">
            <table className="w-full text-sm border border-gray-200 rounded">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-3 py-2 font-semibold text-gray-700 border-b">File</th>
                  <th className="px-3 py-2 font-semibold text-gray-700 border-b">Contents</th>
                  <th className="px-3 py-2 font-semibold text-gray-700 border-b">Key Columns</th>
                </tr>
              </thead>
              <tbody>
                {([
                  ['hosp/patients', 'Patient demographics', 'subject_id, gender, anchor_age, anchor_year, dod'],
                  ['hosp/admissions', 'Hospital admissions', 'subject_id, hadm_id, admittime, dischtime, admission_type, insurance, race'],
                  ['hosp/diagnoses_icd', 'ICD diagnosis codes', 'subject_id, hadm_id, seq_num, icd_code, icd_version'],
                  ['hosp/procedures_icd', 'ICD procedure codes', 'subject_id, hadm_id, seq_num, icd_code, icd_version'],
                  ['hosp/labevents', 'Laboratory test results', 'subject_id, hadm_id, itemid, charttime, value, valuenum, valueuom, flag'],
                  ['hosp/prescriptions', 'Medication prescriptions', 'subject_id, hadm_id, drug, dose_val_rx, dose_unit_rx, route, starttime'],
                  ['hosp/transfers', 'Ward transfers (optional)', 'subject_id, hadm_id, transfer_id, eventtype, careunit, intime, outtime'],
                  ['hosp/emar', 'Medication admin (optional)', 'subject_id, hadm_id, emar_id, medication, charttime, event_txt'],
                  ['hosp/d_labitems', 'Lab reference table', 'itemid, label, fluid, category'],
                  ['hosp/d_icd_diagnoses', 'Diagnosis code reference', 'icd_code, icd_version, long_title'],
                  ['hosp/d_icd_procedures', 'Procedure code reference', 'icd_code, icd_version, long_title'],
                  ['icu/icustays', 'ICU stay records', 'subject_id, hadm_id, stay_id, first_careunit, last_careunit, los'],
                  ['icu/chartevents', 'Charted vital signs', 'subject_id, hadm_id, stay_id, itemid, charttime, value, valuenum'],
                  ['icu/d_items', 'Chart item reference', 'itemid, label'],
                  ['note/discharge', 'Discharge summaries', 'subject_id, hadm_id, note_id, charttime, text'],
                  ['note/radiology', 'Radiology reports', 'subject_id, hadm_id, note_id, charttime, text'],
                ] as [string, string, string][]).map(([file, desc, cols], i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-3 py-1.5 font-mono text-xs text-gray-800 whitespace-nowrap">{file}</td>
                    <td className="px-3 py-1.5 text-gray-600">{desc}</td>
                    <td className="px-3 py-1.5 font-mono text-xs text-gray-500">{cols}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SubSection>

        <SubSection title="Key Linking Columns">
          <SimpleTable
            headers={['Column', 'Meaning', 'Present In']}
            rows={[
              ['subject_id', 'Unique patient identifier', 'All files'],
              ['hadm_id', 'Hospital admission identifier', 'admissions, diagnoses, procedures, labs, prescriptions, notes, transfers, emar'],
              ['stay_id', 'ICU stay identifier', 'icustays, chartevents'],
              ['itemid', 'Measurement type identifier', 'labevents, chartevents, d_labitems, d_items'],
            ]}
          />
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* IMPORTING DATA */}
      {/* ================================================================ */}
      <Section id="importing-data" title="6. Importing Data">
        <SubSection title="How the Import Pipeline Works">
          <p className="text-sm text-gray-700 mb-3">The importer runs 13 stages in sequence:</p>
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1 mb-4">
            <li><strong>Reference tables</strong> — Loads <Code>d_labitems</Code>, <Code>d_icd_diagnoses</Code>, <Code>d_icd_procedures</Code>, and <Code>d_items</Code> as lookup tables</li>
            <li><strong>Patients</strong> — Loads patient demographics, respecting the patient limit if set</li>
            <li><strong>Admissions</strong> — Hospital admissions, joined to imported patients</li>
            <li><strong>Transfers</strong> — Ward transfers (optional file)</li>
            <li><strong>ICU stays</strong> — ICU admissions (requires ICU module)</li>
            <li><strong>Diagnoses</strong> — ICD codes with reference lookup for descriptions</li>
            <li><strong>Procedures</strong> — Procedure codes with reference lookup</li>
            <li><strong>Prescriptions</strong> — Medication orders</li>
            <li><strong>Lab events</strong> — Laboratory results (largest stage, may take several minutes)</li>
            <li><strong>Chart events</strong> — Vital signs from ICU charting (requires ICU module)</li>
            <li><strong>eMAR</strong> — Medication administration records (optional file)</li>
            <li><strong>Notes</strong> — Discharge and radiology notes (requires Note module)</li>
            <li><strong>Finalize</strong> — Updates patient/encounter counts</li>
          </ol>
          <InfoBox>
            All downstream stages (3-12) JOIN on <Code>subject_id</Code> against the patient table. This means only data for
            imported patients is loaded — if you set a patient limit of 1,000, you get exactly 1,000 patients and all
            their associated data.
          </InfoBox>
        </SubSection>

        <SubSection title="Patient Limit">
          <p className="text-sm text-gray-700 mb-2">
            You can limit how many patients to import. This is useful for quick testing or when you don't need the full dataset:
          </p>
          <SimpleTable
            headers={['Limit', 'Use Case', 'Approximate Import Time']}
            rows={[
              ['100 patients', 'Quick test, verify setup works', '< 30 seconds'],
              ['1,000 patients', 'Lite exploration, development', '1-2 minutes'],
              ['5,000 patients', 'Medium research subset', '5-10 minutes'],
              ['10,000 patients', 'Large subset', '10-20 minutes'],
              ['All patients', 'Full dataset (~300k patients)', '30-60+ minutes'],
            ]}
          />
          <p className="text-sm text-gray-500">
            Times are approximate and depend on your hardware and disk speed.
          </p>
        </SubSection>

        <SubSection title="Supplement Import (Adding More Data Later)">
          <p className="text-sm text-gray-700 mb-3">
            After your initial import, you can add more data without starting over. From the Dashboard, click
            <strong> "+ Import More Data"</strong> to open the supplement import panel.
          </p>
          <p className="text-sm text-gray-700 mb-2">Common use cases:</p>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1 mb-3">
            <li><strong>Add a module</strong> — Imported hosp-only? Add ICU or Note data for your existing patients.</li>
            <li><strong>Import more patients</strong> — Started with 1,000? Add more by running a supplement with a higher limit.</li>
            <li><strong>Existing patients only</strong> — Check "Import for existing patients only" to add missing data types (e.g., notes, ICU vitals) without importing new patients.</li>
          </ul>
          <TipBox>
            The import is fully <strong>idempotent</strong> — every row uses <Code>ON CONFLICT DO NOTHING</Code>,
            so re-importing the same data never creates duplicates. You can safely re-run imports without worrying about data corruption.
          </TipBox>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* DASHBOARD */}
      {/* ================================================================ */}
      <Section id="dashboard" title="7. Using the Dashboard">
        <p className="text-sm text-gray-700 mb-4">
          The Dashboard is the first page you see after importing data. It provides a population-level overview of your dataset
          across four collapsible panels. Click any panel header to expand or collapse it.
        </p>

        <SubSection title="Header Bar">
          <p className="text-sm text-gray-700">
            Shows imported module badges (hosp, icu, note), the "+ Import More Data" button, and summary stat cards
            for total patients and encounters.
          </p>
        </SubSection>

        <SubSection title="Demographics Panel">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Age Distribution</strong> — Histogram of patient ages at first admission (anchor_age)</li>
            <li><strong>Gender Distribution</strong> — Pie chart showing male/female breakdown</li>
            <li><strong>Race/Ethnicity</strong> — Horizontal bar chart of all race categories</li>
            <li><strong>Mortality</strong> — Side-by-side cards showing alive vs. deceased counts</li>
          </ul>
        </SubSection>

        <SubSection title="Utilization Panel">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>ICU Stat Cards</strong> — Total ICU stays, average ICU length of stay, patients with ICU, percentage with ICU stay</li>
            <li><strong>Admissions Over Time</strong> — Line chart showing monthly admission trends</li>
            <li><strong>Average LOS by Admission Type</strong> — Bar chart comparing length of stay across emergency, elective, urgent, etc.</li>
          </ul>
        </SubSection>

        <SubSection title="Clinical Distributions Panel">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Top 20 Diagnoses</strong> — Most frequent ICD codes (hover for full description)</li>
            <li><strong>Top 20 Labs</strong> — Most frequently ordered lab tests</li>
            <li><strong>Top 20 Medications</strong> — Most prescribed drugs</li>
          </ul>
        </SubSection>

        <SubSection title="Data Completeness Panel">
          <p className="text-sm text-gray-700">
            Horizontal progress bars for each data type showing the percentage of non-null values. Color-coded:
            green ({'>'} 80%), yellow (50-80%), red ({'<'} 50%). Useful for understanding which data types are
            well-populated vs. sparse in your imported subset.
          </p>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* PATIENT SEARCH */}
      {/* ================================================================ */}
      <Section id="patient-search" title="8. Patient Search">
        <p className="text-sm text-gray-700 mb-4">
          The Patients page lets you find patients by demographics and view their records.
        </p>

        <SubSection title="Filters">
          <SimpleTable
            headers={['Filter', 'Description']}
            rows={[
              ['Subject ID', 'Search by exact patient ID number'],
              ['Gender', 'Filter by Male or Female'],
              ['Age Min / Age Max', 'Filter by anchor_age range (age at first admission)'],
            ]}
          />
          <p className="text-sm text-gray-700">
            Combine filters to narrow results — for example, female patients aged 65-80. Click "Search" to apply.
          </p>
        </SubSection>

        <SubSection title="Results Table">
          <p className="text-sm text-gray-700 mb-2">
            Shows matching patients with their Subject ID, Gender, Age, number of Encounters, and Deceased status.
            Results are paginated (50 per page) with Previous/Next navigation.
          </p>
          <TipBox>
            Click any row to open that patient's full chart in the EHR Viewer.
          </TipBox>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* PATIENT CHART */}
      {/* ================================================================ */}
      <Section id="patient-chart" title="9. Patient Chart (EHR Viewer)">
        <p className="text-sm text-gray-700 mb-4">
          The Patient Chart provides a full electronic health record view for a single patient, similar to what
          clinicians see in hospital EHR systems.
        </p>

        <SubSection title="Layout">
          <p className="text-sm text-gray-700 mb-2">The page has two main areas:</p>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Left sidebar</strong> — Lists all encounters (hospital admissions) for this patient, sorted by date.
              Each entry shows the encounter ID, admit date, admission type, length of stay, and discharge location.
              Click an encounter to view its details. An "Expired" badge appears if the patient died during that admission.</li>
            <li><strong>Main content area</strong> — Tabbed view of clinical data for the selected encounter.</li>
          </ul>
        </SubSection>

        <SubSection title="Patient Banner">
          <p className="text-sm text-gray-700">
            At the top of the page, a banner shows the patient's Subject ID, gender, anchor age, and mortality status (Alive or Deceased with date of death).
          </p>
        </SubSection>

        <SubSection title="Clinical Data Tabs">
          <SimpleTable
            headers={['Tab', 'What It Shows']}
            rows={[
              ['Overview', 'Encounter summary — admission/discharge times, type, locations, insurance, language, marital status, race'],
              ['Labs', 'Laboratory results with test name, value, units, reference range, and abnormal flags'],
              ['Vitals', 'Charted vital signs — heart rate, blood pressure, SpO2, temperature, respiratory rate (requires ICU module)'],
              ['Medications', 'Prescribed medications with drug name, dose, route, and start/stop times'],
              ['Diagnoses', 'ICD diagnosis codes with sequence number and full description'],
              ['Procedures', 'ICD procedure codes with description'],
              ['Notes', 'Clinical narrative text — discharge summaries and radiology reports (requires Note module)'],
              ['ICU', 'ICU stay details — care unit, length of stay, in/out times (only appears for encounters with ICU stays)'],
            ]}
          />
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* ENCOUNTER BROWSER */}
      {/* ================================================================ */}
      <Section id="encounter-browser" title="10. Encounter Browser">
        <p className="text-sm text-gray-700 mb-4">
          The Encounters page lets you search and browse hospital admissions across all patients.
        </p>

        <SubSection title="Filters">
          <SimpleTable
            headers={['Filter', 'Description']}
            rows={[
              ['Subject ID', 'Show encounters for a specific patient'],
              ['Admission Type', 'Filter by type: Emergency, Elective, Urgent, Observation, Surgical Same Day, etc.'],
              ['Admit From / To', 'Filter by admission date range'],
            ]}
          />
        </SubSection>

        <SubSection title="Results Table">
          <p className="text-sm text-gray-700">
            Shows HADM ID, Subject ID, admission/discharge timestamps, length of stay (days), admission type
            (color-coded badge), discharge location, and expired status. Click the HADM ID or Subject ID to
            navigate to the full patient chart.
          </p>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* RESEARCH: COHORT BUILDER */}
      {/* ================================================================ */}
      <Section id="research-cohorts" title="11. Research: Cohort Builder">
        <p className="text-sm text-gray-700 mb-4">
          The Cohort Builder lets you define patient populations using clinical inclusion and exclusion criteria,
          then analyze and compare them.
        </p>

        <SubSection title="Creating a Cohort">
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
            <li>Go to <strong>Research → Cohorts</strong> and click "New Cohort".</li>
            <li>Enter a <strong>name</strong> and optional description.</li>
            <li>Add <strong>inclusion criteria</strong> (AND logic — all must be true). Click "Add" and choose a criterion type:
              <SimpleTable
                headers={['Type', 'How It Works', 'Example']}
                rows={[
                  ['Diagnosis', 'Matches patients with an ICD code starting with your prefix', 'ICD prefix "I25" → all ischemic heart disease'],
                  ['Lab', 'Matches patients with a lab result meeting your threshold', 'Creatinine > 2.0'],
                  ['Vital', 'Matches patients with a vital sign value meeting your threshold', 'Heart Rate > 120'],
                  ['Medication', 'Matches patients prescribed a drug containing your search term', '"Aspirin"'],
                  ['Age', 'Matches patients by anchor_age', 'Age >= 65'],
                  ['Gender', 'Matches patients by gender', 'Female'],
                ]}
              />
            </li>
            <li>Optionally add <strong>exclusion criteria</strong> — patients matching any exclusion criterion are removed.</li>
            <li>Click <strong>"Preview Count"</strong> to see how many encounters match before saving.</li>
            <li>Click <strong>"Create Cohort"</strong> to save the definition.</li>
          </ol>
        </SubSection>

        <SubSection title="Executing a Cohort">
          <p className="text-sm text-gray-700">
            After creating a cohort, click <strong>"Execute"</strong> in the cohort list to run the criteria against the database.
            This populates the cohort with matching patients and encounters. You can re-execute after importing more data.
          </p>
        </SubSection>

        <SubSection title="Cohort Detail Page">
          <p className="text-sm text-gray-700 mb-2">
            Click a cohort name to view its detail page, which shows:
          </p>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Summary statistics</strong> — Patient count, encounter count, average age, mortality rate</li>
            <li><strong>Demographics charts</strong> — Gender distribution pie chart and age distribution histogram</li>
            <li><strong>Criteria summary</strong> — Human-readable badges showing all inclusion/exclusion criteria</li>
            <li><strong>Members table</strong> — Searchable, paginated list of all patients in the cohort</li>
            <li><strong>Cohort comparison</strong> — Select another cohort to see side-by-side demographic and mortality statistics</li>
          </ul>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* RESEARCH: SEARCH */}
      {/* ================================================================ */}
      <Section id="research-search" title="12. Research: Structured Search">
        <p className="text-sm text-gray-700 mb-4">
          The Search tab lets you run ad-hoc queries without creating a full cohort definition.
        </p>

        <SubSection title="Search Filters">
          <SimpleTable
            headers={['Filter', 'Description']}
            rows={[
              ['Diagnosis', 'ICD code prefix (e.g., "428" for heart failure, "A41" for sepsis)'],
              ['Lab label + operator + value', 'Lab test threshold (e.g., Glucose > 200)'],
              ['Medication', 'Drug name search (e.g., "Heparin")'],
              ['Age + operator', 'Age filter (e.g., >= 65)'],
              ['Gender', 'Male or Female'],
            ]}
          />
        </SubSection>

        <SubSection title="Working with Results">
          <p className="text-sm text-gray-700 mb-2">After searching, you can:</p>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>Browse results</strong> — Paginated table showing matching encounters with patient ID, admission details, and diagnosis codes</li>
            <li><strong>Save as Query</strong> — Enter a name and save the search criteria for later reuse</li>
            <li><strong>Create Cohort</strong> — Convert the search results directly into a named cohort for further analysis</li>
          </ul>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* RESEARCH: PLOTS */}
      {/* ================================================================ */}
      <Section id="research-plots" title="13. Research: Plot Builder">
        <p className="text-sm text-gray-700 mb-4">
          The Plot Builder generates distribution visualizations for lab results and vital signs, optionally filtered to a specific cohort.
        </p>

        <SubSection title="How to Use">
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
            <li>Select <strong>Data Type</strong> — Labs or Vitals</li>
            <li>Select <strong>Item</strong> — Choose a specific lab test (e.g., Creatinine) or vital sign (e.g., Heart Rate) from the dropdown</li>
            <li>Select <strong>Plot Type</strong>:
              <ul className="list-disc list-inside ml-6 mt-1 space-y-1">
                <li><strong>Histogram</strong> — Distribution of values across bins</li>
                <li><strong>Time Series</strong> — Values plotted over time (up to 500 measurements)</li>
                <li><strong>Summary Stats</strong> — Table of N, Mean, Median, Min, Q1, Q3, Max</li>
              </ul>
            </li>
            <li>Optionally filter by <strong>Cohort</strong> to see distributions for a specific patient population</li>
            <li>Click <strong>"Generate"</strong></li>
          </ol>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* RESEARCH: EXPORT */}
      {/* ================================================================ */}
      <Section id="research-export" title="14. Research: Data Export">
        <p className="text-sm text-gray-700 mb-4">
          The Export tab lets you download clinical data for external analysis in tools like R, Python (pandas), Stata, or Excel.
        </p>

        <SubSection title="Export Options">
          <SimpleTable
            headers={['Option', 'Description']}
            rows={[
              ['Data Source', 'Choose a saved cohort or enter comma-separated patient IDs'],
              ['Data Types', 'Select which data to include: Demographics, Encounters, Lab Results, Vital Signs, Diagnoses, Medications, Clinical Notes'],
              ['Format', 'CSV (for spreadsheets and statistical software) or JSON (for programmatic use)'],
            ]}
          />
          <p className="text-sm text-gray-700">
            Click <strong>"Download"</strong> to generate and save the file. CSV exports create a downloadable file;
            JSON exports return structured data with one key per selected data type.
          </p>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* FHIR */}
      {/* ================================================================ */}
      <Section id="fhir" title="15. FHIR R4 API">
        <p className="text-sm text-gray-700 mb-4">
          MIMIC Explorer includes a FHIR R4-compliant API that transforms clinical data into standard FHIR resources on the fly.
          This is useful for testing FHIR-based applications, learning the FHIR standard, or integrating with tools that consume FHIR data.
        </p>

        <SubSection title="FHIR Explorer (In-App)">
          <p className="text-sm text-gray-700 mb-3">
            The FHIR page in the app provides an interactive query builder:
          </p>
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
            <li>Select a <strong>Resource Type</strong> (Patient, Encounter, Observation, Condition, Procedure, MedicationRequest, DocumentReference)</li>
            <li>Optionally enter a <strong>Resource ID</strong> to read a specific resource, or leave empty to search</li>
            <li>Fill in <strong>search parameters</strong> (vary by resource type — patient ID, date ranges, category, codes)</li>
            <li>A URL preview shows the exact GET request being constructed</li>
            <li>Click <strong>"Execute"</strong> to see the formatted FHIR JSON response</li>
          </ol>
        </SubSection>

        <SubSection title="Resource Types">
          <SimpleTable
            headers={['FHIR Resource', 'Maps To', 'ID Format']}
            rows={[
              ['Patient', 'MIMIC patient demographics', 'mimic-{subject_id}'],
              ['Encounter', 'Hospital admissions', 'mimic-{hadm_id}'],
              ['Observation (laboratory)', 'Lab results', 'mimic-lab-{labevent_id}'],
              ['Observation (vital-signs)', 'Vital signs from ICU', 'mimic-vital-{pk}'],
              ['Condition', 'Diagnoses (ICD codes)', 'mimic-dx-{hadm_id}-{seq_num}'],
              ['Procedure', 'Procedures (ICD codes)', 'mimic-proc-{hadm_id}-{seq_num}'],
              ['MedicationRequest', 'Prescriptions', 'mimic-med-{pk}'],
              ['DocumentReference', 'Clinical notes', 'mimic-note-{note_id}'],
            ]}
          />
        </SubSection>

        <SubSection title="Direct API Access">
          <p className="text-sm text-gray-700 mb-2">
            You can also query the FHIR API directly from any HTTP client. FHIR endpoints are served at <Code>/fhir/</Code> (not <Code>/api/</Code>):
          </p>
          <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-xs space-y-1 mb-3">
            <p className="text-gray-400"># Read a patient</p>
            <p>curl http://localhost:8765/fhir/Patient/mimic-10001/</p>
            <p className="mt-2 text-gray-400"># Search for lab observations</p>
            <p>curl "http://localhost:8765/fhir/Observation/?category=laboratory&patient=mimic-10001"</p>
            <p className="mt-2 text-gray-400"># Get everything for a patient</p>
            <p>curl http://localhost:8765/fhir/Patient/mimic-10001/\$everything</p>
          </div>
        </SubSection>

        <SubSection title="Search Parameters">
          <SimpleTable
            headers={['Resource', 'Supported Parameters']}
            rows={[
              ['Patient', '_id, gender, _page'],
              ['Encounter', 'patient, date (supports ge/le prefix), _page'],
              ['Observation', 'patient, encounter, category (laboratory, vital-signs), code, date, _page'],
              ['Condition', 'patient, encounter, code, _page'],
              ['Procedure', 'patient, encounter, _page'],
              ['MedicationRequest', 'patient, encounter, _page'],
              ['DocumentReference', 'patient, encounter, type, _page'],
            ]}
          />
        </SubSection>

        <SubSection title="$everything Operation">
          <p className="text-sm text-gray-700">
            <Code>GET /fhir/Patient/:id/$everything</Code> returns a FHIR Bundle containing the Patient resource and up to
            500 each of: Encounters, Observations (labs + vitals), Conditions, Procedures, MedicationRequests, and DocumentReferences.
            This is useful for getting a complete patient record in a single request.
          </p>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* API REFERENCE */}
      {/* ================================================================ */}
      <Section id="api-reference" title="16. REST API Reference">
        <p className="text-sm text-gray-500 mb-4">
          All endpoints return JSON. Paginated endpoints accept <Code>page</Code> and <Code>page_size</Code> (default 50) query parameters. No authentication required.
        </p>

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">System</h3>
        <EndpointTable rows={[
          ['GET', '/api/status/', 'System configuration and import state'],
          ['POST', '/api/import/browse-folder/', 'Open native folder picker dialog'],
          ['POST', '/api/import/validate-folder/', 'Validate MIMIC-IV folder structure'],
          ['POST', '/api/import/start/', 'Start data import (background)'],
          ['GET', '/api/import/status/', 'Poll import progress'],
          ['POST', '/api/import/cancel/', 'Cancel running import'],
          ['POST', '/api/import/supplement/', 'Import additional modules into existing data'],
          ['POST', '/api/reset/', 'Wipe all data and reset to initial state'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Patients</h3>
        <EndpointTable rows={[
          ['GET', '/api/patients/', 'List patients (filter: search, gender, age_min, age_max)'],
          ['GET', '/api/patients/:subject_id/', 'Patient detail with encounters'],
          ['GET', '/api/patients/:subject_id/timeline/', 'Patient event timeline'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Encounters</h3>
        <EndpointTable rows={[
          ['GET', '/api/encounters/', 'List encounters (filter: patient, admission_type, date_from, date_to)'],
          ['GET', '/api/encounters/:hadm_id/', 'Encounter detail'],
          ['GET', '/api/encounters/:hadm_id/labs/', 'Labs for encounter'],
          ['GET', '/api/encounters/:hadm_id/vitals/', 'Vitals for encounter'],
          ['GET', '/api/encounters/:hadm_id/diagnoses/', 'Diagnoses for encounter'],
          ['GET', '/api/encounters/:hadm_id/procedures/', 'Procedures for encounter'],
          ['GET', '/api/encounters/:hadm_id/medications/', 'Medications for encounter'],
          ['GET', '/api/encounters/:hadm_id/notes/', 'Notes for encounter'],
          ['GET', '/api/encounters/:hadm_id/icu-stays/', 'ICU stays for encounter'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Clinical</h3>
        <EndpointTable rows={[
          ['GET', '/api/labs/', 'List lab events (filter: patient, encounter, label, itemid, date_from, date_to, abnormal_only)'],
          ['GET', '/api/vitals/', 'List vital signs (filter: patient, encounter, label, itemid, date_from, date_to)'],
          ['GET', '/api/diagnoses/', 'List diagnoses (filter: patient, encounter, icd_code, search)'],
          ['GET', '/api/procedures/', 'List procedures (filter: patient, encounter, icd_code, search)'],
          ['GET', '/api/medications/', 'List medications (filter: patient, encounter, drug, date_from, date_to)'],
          ['GET', '/api/notes/', 'List notes (filter: patient, encounter, note_type)'],
          ['GET', '/api/lab-items/', 'Distinct lab item IDs and labels'],
          ['GET', '/api/vital-items/', 'Distinct vital sign item IDs and labels'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Dashboards</h3>
        <EndpointTable rows={[
          ['GET', '/api/dashboards/demographics/', 'Age, gender, race distributions and mortality'],
          ['GET', '/api/dashboards/utilization/', 'Admissions by month, LOS by type, ICU stats'],
          ['GET', '/api/dashboards/clinical/', 'Top 20 diagnoses, labs, and medications'],
          ['GET', '/api/dashboards/missingness/', 'Data completeness percentages'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">Research</h3>
        <EndpointTable rows={[
          ['GET', '/api/research/cohorts/', 'List cohort definitions'],
          ['POST', '/api/research/cohorts/', 'Create cohort (body: name, description, criteria)'],
          ['GET', '/api/research/cohorts/:id/', 'Cohort detail'],
          ['PUT', '/api/research/cohorts/:id/', 'Update cohort'],
          ['DELETE', '/api/research/cohorts/:id/', 'Delete cohort'],
          ['POST', '/api/research/cohorts/:id/execute/', 'Execute cohort criteria and populate members'],
          ['GET', '/api/research/cohorts/:id/stats/', 'Cohort statistics (demographics, mortality)'],
          ['GET', '/api/research/cohorts/:id/members/', 'Cohort members (filter: search, group)'],
          ['POST', '/api/research/cohorts/compare/', 'Compare two cohorts (body: cohort_a, cohort_b)'],
          ['GET', '/api/research/queries/', 'List saved queries'],
          ['POST', '/api/research/queries/', 'Create saved query (body: name, query_definition)'],
          ['DELETE', '/api/research/queries/:id/', 'Delete saved query'],
          ['POST', '/api/research/queries/:id/run/', 'Execute saved query'],
          ['POST', '/api/research/search/', 'Structured patient search (body: criteria, page)'],
          ['POST', '/api/research/export/', 'Export data (body: format, cohort_id, patient_ids, data_types)'],
        ]} />

        <h3 className="text-lg font-semibold text-gray-700 mt-6 mb-3">FHIR R4</h3>
        <EndpointTable rows={[
          ['GET', '/fhir/metadata', 'FHIR CapabilityStatement'],
          ['GET', '/fhir/Patient/', 'Search patients (params: _id, gender, _page)'],
          ['GET', '/fhir/Patient/:id/', 'Read patient resource'],
          ['GET', '/fhir/Patient/:id/$everything', 'All resources for a patient'],
          ['GET', '/fhir/Encounter/', 'Search encounters (params: patient, date, _page)'],
          ['GET', '/fhir/Encounter/:id/', 'Read encounter resource'],
          ['GET', '/fhir/Observation/', 'Search observations (params: patient, encounter, category, code, date, _page)'],
          ['GET', '/fhir/Observation/:id/', 'Read observation resource'],
          ['GET', '/fhir/Condition/', 'Search conditions (params: patient, encounter, code, _page)'],
          ['GET', '/fhir/Condition/:id/', 'Read condition resource'],
          ['GET', '/fhir/Procedure/', 'Search procedures (params: patient, encounter, _page)'],
          ['GET', '/fhir/Procedure/:id/', 'Read procedure resource'],
          ['GET', '/fhir/MedicationRequest/', 'Search medication requests (params: patient, encounter, _page)'],
          ['GET', '/fhir/MedicationRequest/:id/', 'Read medication request resource'],
          ['GET', '/fhir/DocumentReference/', 'Search documents (params: patient, encounter, type, _page)'],
          ['GET', '/fhir/DocumentReference/:id/', 'Read document reference resource'],
        ]} />
      </Section>

      {/* ================================================================ */}
      {/* CLI */}
      {/* ================================================================ */}
      <Section id="cli" title="17. Command Line Interface">
        <p className="text-sm text-gray-700 mb-4">
          MIMIC Explorer is launched via the <Code>mimic-explorer</Code> command after installation.
          If the command is not found, you can use <Code>python -m mimic_explorer</Code> instead — it accepts
          all the same flags.
        </p>
        <SimpleTable
          headers={['Option', 'Description']}
          rows={[
            ['(no flags)', 'Start the server and open browser automatically'],
            ['--test', 'Run the built-in test suite to verify your installation'],
            ['--version, -V', 'Show version number'],
            ['--port PORT, -p PORT', 'Run the server on a specific port (default: auto-detect)'],
            ['--data PATH', 'Path to MIMIC-IV data folder — validates and imports on startup'],
            ['--no-browser', 'Start the server without opening a browser'],
            ['--help, -h', 'Show help message'],
          ]}
        />
        <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm space-y-1">
          <p className="text-gray-400"># Start the app (opens browser automatically)</p>
          <p>mimic-explorer</p>
          <p className="mt-2 text-gray-400"># Start on a specific port without opening a browser</p>
          <p>mimic-explorer --port 8080 --no-browser</p>
          <p className="mt-2 text-gray-400"># Verify your installation is working</p>
          <p>mimic-explorer --test</p>
          <p className="mt-2 text-gray-400"># Alternative: use the module form (always works, even if Scripts isn't on PATH)</p>
          <p>python -m mimic_explorer</p>
        </div>
      </Section>

      {/* ================================================================ */}
      {/* TESTING */}
      {/* ================================================================ */}
      <Section id="testing" title="18. Testing">
        <p className="text-sm text-gray-700 mb-4">
          MIMIC Explorer includes a built-in test suite with 62 tests that verify the entire application
          stack — models, import pipeline, REST API, and FHIR endpoints. Tests run against bundled
          fixture data (10 patients) and do not affect your imported data.
        </p>
        <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm mb-4">
          mimic-explorer --test
        </div>

        <SubSection title="What the Tests Cover">
          <SimpleTable
            headers={['Category', 'Tests', "What's verified"]}
            rows={[
              ['Models', '12', 'Patient, Encounter, Diagnosis, LabEvent, Note creation; SystemConfig singleton; unique constraints'],
              ['Import Pipeline', '11', 'Folder validation, full import with all modules, per-stage row counts, patient_limit, module-selective imports'],
              ['REST API', '22', 'Status, folder validation, patient/encounter CRUD, clinical endpoints, timeline, reset, supplement import idempotency'],
              ['FHIR R4', '17', 'CapabilityStatement, Patient/Encounter/Observation/Condition/Procedure/MedicationRequest/DocumentReference read & search, $everything, 404 handling'],
            ]}
          />
        </SubSection>

        <SubSection title="Interpreting Results">
          <p className="text-sm text-gray-700 mb-2">
            Each passing test shows what it verified. If a test fails, it shows a diagnostic message
            explaining what went wrong and which file to check:
          </p>
          <div className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-xs space-y-1 mb-4">
            <p><span className="text-green-400">PASS</span>  GET /api/patients/ should return paginated patient list.</p>
            <p><span className="text-green-400">PASS</span>  Import should create exactly 10 patients from fixtures.</p>
            <p><span className="text-red-400">FAIL</span>  GET /api/labs/ should return paginated lab events.</p>
            <p className="text-gray-400 pl-6">GET /api/labs/ failed. Check clinical/urls.py for the labs</p>
            <p className="text-gray-400 pl-6">list endpoint and clinical/views.py for the view.</p>
          </div>
        </SubSection>

        <SubSection title="Common Issues">
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li><strong>0 patients imported</strong> — Check that <Code>tests/fixtures/mimic-iv-test/</Code> exists with CSV files</li>
            <li><strong>Database errors</strong> — Tests use an in-memory database and won't affect your imported data</li>
            <li><strong>Import failures</strong> — The error message will point to the specific stage in <Code>core/importer.py</Code></li>
          </ul>
        </SubSection>
      </Section>

      {/* ================================================================ */}
      {/* RESET */}
      {/* ================================================================ */}
      <Section id="reset" title="19. Reset Application">
        <p className="text-sm text-gray-700 mb-4">
          If you need to start fresh — for example, to re-import with different settings or clear all data — you can
          reset the entire application. This deletes all imported clinical data, saved cohorts, saved queries, and
          resets the system configuration to defaults.
        </p>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">Danger Zone</h3>
          <p className="text-sm text-red-700 mb-4">
            Resetting will permanently delete all imported patient data, encounters, clinical records,
            cohorts, saved queries, and FHIR resources. You will need to re-import your MIMIC-IV data
            after resetting. Your original MIMIC-IV CSV files are never modified.
          </p>
          {!showResetDialog ? (
            <button
              onClick={() => setShowResetDialog(true)}
              className="px-4 py-2 bg-red-600 text-white rounded font-medium hover:bg-red-700 transition-colors"
            >
              Reset All Data
            </button>
          ) : (
            <div className="bg-white border border-red-300 rounded p-4">
              <p className="text-sm text-gray-700 mb-3">
                Type <strong>reset</strong> to confirm:
              </p>
              <div className="flex gap-3 items-center">
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="Type 'reset' to confirm"
                  className="px-3 py-1.5 border border-gray-300 rounded text-sm flex-1 max-w-xs focus:outline-none focus:ring-2 focus:ring-red-500"
                  autoFocus
                />
                <button
                  onClick={handleReset}
                  disabled={confirmText !== 'reset' || resetting}
                  className="px-4 py-1.5 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {resetting ? 'Resetting...' : 'Confirm Reset'}
                </button>
                <button
                  onClick={() => { setShowResetDialog(false); setConfirmText('') }}
                  className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </Section>
    </div>
  )
}

function StepBlock({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm flex-shrink-0 mt-0.5">
        {number}
      </div>
      <div className="flex-1">
        <h4 className="font-semibold text-gray-800 mb-1">{title}</h4>
        {children}
      </div>
    </div>
  )
}
