# MIMIC Explorer API Reference

All endpoints return JSON (`application/json`) unless otherwise noted. No authentication required.

Paginated endpoints accept `page` (default 1) and `page_size` (default 50) query parameters and return:

```json
{ "count": 100, "page": 1, "page_size": 50, "results": [...] }
```

---

## Expected Data Structure

MIMIC Explorer imports the standard MIMIC-IV CSV files from PhysioNet. Point the app at a folder with this layout:

```
mimic-iv/
├── hosp/                          ← Required (Hospital module)
│   ├── patients.csv.gz            Patient demographics (subject_id, gender, anchor_age, dod)
│   ├── admissions.csv.gz          Hospital admissions (hadm_id, admit/discharge times, type, location, insurance, race)
│   ├── diagnoses_icd.csv.gz       ICD-9/10 diagnosis codes per admission (seq_num, icd_code, icd_version)
│   ├── procedures_icd.csv.gz      ICD-9/10 procedure codes per admission
│   ├── labevents.csv.gz           Lab results (itemid, charttime, value, valuenum, valueuom, ref ranges, flag)
│   ├── prescriptions.csv.gz       Medication orders (drug, dose_val_rx, dose_unit_rx, route, start/stop times)
│   ├── d_labitems.csv.gz          Reference: lab itemid → label, fluid, category
│   ├── d_icd_diagnoses.csv.gz     Reference: icd_code → long_title
│   ├── d_icd_procedures.csv.gz    Reference: icd_code → long_title
│   ├── transfers.csv.gz           (optional) Ward transfers (transfer_id, eventtype, careunit, in/out times)
│   └── emar.csv.gz                (optional) Medication administrations (emar_id, medication, event_txt, charttime)
├── icu/                           ← Optional (ICU module)
│   ├── icustays.csv.gz            ICU stays (stay_id, first/last careunit, LOS, in/out times)
│   ├── chartevents.csv.gz         Charted observations — filtered to vital signs (HR, BP, SpO2, temp, RR)
│   └── d_items.csv.gz             Reference: chart itemid → label
└── note/                          ← Optional (Notes module — separate PhysioNet download)
    ├── discharge.csv.gz           Discharge summary notes (note_id, charttime, free text)
    └── radiology.csv.gz           Radiology report notes (note_id, charttime, free text)
```

### File format

- Files can be `.csv` or `.csv.gz` (gzip compressed). The importer checks for `.csv.gz` first.
- All files use the standard MIMIC-IV column names from PhysioNet.

### How import works

1. **Reference tables** (`d_labitems`, `d_icd_*`, `d_items`) are loaded into temporary lookup tables.
2. **Patients** from `patients.csv` are inserted (respecting `patient_limit` if set).
3. **All downstream stages** (admissions, diagnoses, labs, etc.) JOIN on `patient.subject_id`, so only data for imported patients is loaded.
4. Existing rows are never duplicated — every INSERT uses `ON CONFLICT ... DO NOTHING` on unique keys.

### Key columns linking files

| Column | Meaning | Present in |
|--------|---------|-----------|
| `subject_id` | Patient identifier | All files |
| `hadm_id` | Hospital admission identifier | admissions, diagnoses, procedures, labs, prescriptions, notes, transfers, emar |
| `stay_id` | ICU stay identifier | icustays, chartevents |
| `itemid` | Measurement type identifier | labevents, chartevents, d_labitems, d_items |

---

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status/` | System configuration and import state |
| POST | `/api/import/browse-folder/` | Open native folder picker dialog |
| POST | `/api/import/validate-folder/` | Validate MIMIC-IV folder structure |
| POST | `/api/import/start/` | Start data import in background |
| GET | `/api/import/status/` | Poll import progress |
| POST | `/api/import/cancel/` | Cancel running import |
| POST | `/api/import/supplement/` | Import additional modules into existing data |
| POST | `/api/reset/` | Wipe all data and reset to initial state |

### GET /api/status/

Returns current system configuration.

**Response:**

```json
{
  "mimic_data_path": "/path/to/mimic-iv",
  "import_status": "completed",
  "import_progress": {},
  "imported_modules": ["hosp", "icu"],
  "total_patients": 1000,
  "total_encounters": 5000,
  "import_started_at": "2025-01-01T00:00:00Z",
  "import_completed_at": "2025-01-01T00:05:00Z",
  "mimic_version": ""
}
```

### POST /api/import/browse-folder/

Opens a native OS folder picker dialog. Blocks until the user selects a folder or cancels.

**Response:** `{ "path": "/selected/path" }` (empty string if cancelled)

### POST /api/import/validate-folder/

**Request body:** `{ "folder_path": "/path/to/mimic-iv" }`

**Response:**

```json
{
  "valid": true,
  "available_modules": ["hosp", "icu"],
  "files_found": { "hosp": [...], "icu": [...] },
  "missing_files": {}
}
```

### POST /api/import/start/

**Request body:**

```json
{
  "folder_path": "/path/to/mimic-iv",
  "modules": ["hosp", "icu"],
  "patient_limit": 1000,
  "generate_fhir": false,
  "existing_patients_only": false
}
```

- `patient_limit` — optional, null for all patients
- `generate_fhir` — optional, default false
- `existing_patients_only` — optional, default false. When true, skips the patient import stage (no new patients added)

**Response:** `{ "status": "started" }` (HTTP 202)

Returns 409 if an import is already running.

### GET /api/import/status/

**Response:**

```json
{
  "import_status": "in_progress",
  "import_progress": { "current_stage": "labs", "stage_progress": 45 },
  "imported_modules": ["hosp"],
  "total_patients": 500,
  "total_encounters": 2000,
  "import_started_at": "2025-01-01T00:00:00Z",
  "import_completed_at": null
}
```

### POST /api/import/cancel/

**Response:** `{ "status": "cancel_requested" }`

### POST /api/import/supplement/

Import additional modules into an existing completed import. The importer re-runs all stages idempotently — existing rows are skipped via unique constraints and `ON CONFLICT DO NOTHING`. After completion, `imported_modules` is updated to the union of old and new modules.

**Request body:**

```json
{
  "folder_path": "/path/to/mimic-iv",
  "modules": ["hosp", "icu"],
  "patient_limit": 1000,
  "generate_fhir": false,
  "existing_patients_only": false
}
```

- `existing_patients_only` — optional, default false. When true, the patient import stage is skipped so no new patients are added. All other stages only import data for patients already in the database. Returns 400 if enabled but no patients exist.

**Response:** `{ "status": "started" }` (HTTP 202)

Returns 409 if an import is already running. Returns 400 if the initial import has not completed.

### POST /api/reset/

Deletes all imported data and resets system configuration to defaults. Returns 409 if an import is in progress.

**Response:** `{ "status": "reset_complete" }`

---

## Patients

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/patients/` | List patients (paginated) |
| GET | `/api/patients/:subject_id/` | Patient detail with encounters |
| GET | `/api/patients/:subject_id/timeline/` | Patient event timeline |

### GET /api/patients/

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Search by subject_id |
| `gender` | string | Filter by gender (M/F) |
| `age_min` | int | Minimum anchor_age |
| `age_max` | int | Maximum anchor_age |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response item:**

```json
{
  "id": 1,
  "subject_id": 10001,
  "gender": "M",
  "anchor_age": 65,
  "anchor_year": 2150,
  "anchor_year_group": "2014 - 2016",
  "dod": null,
  "encounter_count": 3
}
```

### GET /api/patients/:subject_id/

**Response:**

```json
{
  "id": 1,
  "subject_id": 10001,
  "gender": "M",
  "anchor_age": 65,
  "anchor_year": 2150,
  "anchor_year_group": "2014 - 2016",
  "dod": null,
  "encounters": [
    {
      "id": 1,
      "hadm_id": 20001,
      "admittime": "2150-01-01T00:00:00Z",
      "dischtime": "2150-01-05T00:00:00Z",
      "admission_type": "EMERGENCY",
      "discharge_location": "HOME",
      "hospital_expire_flag": false
    }
  ]
}
```

### GET /api/patients/:subject_id/timeline/

**Response:** Array of timeline events.

```json
[
  {
    "event_type": "admission",
    "timestamp": "2150-01-01T00:00:00Z",
    "description": "Emergency admission",
    "encounter_id": 20001,
    "detail": {}
  }
]
```

---

## Encounters

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/encounters/` | List encounters (paginated) |
| GET | `/api/encounters/:hadm_id/` | Encounter detail |
| GET | `/api/encounters/:hadm_id/labs/` | Labs for encounter |
| GET | `/api/encounters/:hadm_id/vitals/` | Vitals for encounter |
| GET | `/api/encounters/:hadm_id/diagnoses/` | Diagnoses for encounter |
| GET | `/api/encounters/:hadm_id/procedures/` | Procedures for encounter |
| GET | `/api/encounters/:hadm_id/medications/` | Medications for encounter |
| GET | `/api/encounters/:hadm_id/notes/` | Notes for encounter |
| GET | `/api/encounters/:hadm_id/icu-stays/` | ICU stays for encounter |

### GET /api/encounters/

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `patient` | int | Filter by patient subject_id |
| `admission_type` | string | Filter by admission type |
| `date_from` | datetime | admittime >= value |
| `date_to` | datetime | admittime <= value |

**Response item:**

```json
{
  "id": 1,
  "hadm_id": 20001,
  "patient_id": 1,
  "subject_id": 10001,
  "admittime": "2150-01-01T00:00:00Z",
  "dischtime": "2150-01-05T00:00:00Z",
  "deathtime": null,
  "admission_type": "EMERGENCY",
  "admission_location": "EMERGENCY ROOM",
  "discharge_location": "HOME",
  "insurance": "Medicare",
  "language": "ENGLISH",
  "marital_status": "MARRIED",
  "race": "WHITE",
  "hospital_expire_flag": false
}
```

### GET /api/encounters/:hadm_id/

Returns single encounter with all fields above plus: `edregtime`, `edouttime`, `admit_provider_id`.

### Sub-resource endpoints

`/labs/`, `/vitals/`, `/diagnoses/`, `/procedures/`, `/medications/`, `/notes/`, `/icu-stays/` — all return paginated lists. See the Clinical section for field details.

---

## Clinical

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/labs/` | List lab events (paginated) |
| GET | `/api/vitals/` | List vital signs (paginated) |
| GET | `/api/diagnoses/` | List diagnoses (paginated) |
| GET | `/api/procedures/` | List procedures (paginated) |
| GET | `/api/medications/` | List medications (paginated) |
| GET | `/api/notes/` | List notes (paginated) |
| GET | `/api/lab-items/` | Distinct lab item IDs and labels |
| GET | `/api/vital-items/` | Distinct vital sign item IDs and labels |

### GET /api/labs/

**Query parameters:** `patient`, `encounter`, `label`, `itemid`, `date_from`, `date_to`, `abnormal_only`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "labevent_id": 12345,
  "itemid": 50912,
  "label": "Creatinine",
  "fluid": "Blood",
  "category": "Chemistry",
  "charttime": "2150-01-02T06:00:00Z",
  "value": "1.2",
  "valuenum": 1.2,
  "valueuom": "mg/dL",
  "ref_range_lower": 0.6,
  "ref_range_upper": 1.3,
  "flag": "",
  "priority": "ROUTINE"
}
```

### GET /api/vitals/

**Query parameters:** `patient`, `encounter`, `label`, `itemid`, `date_from`, `date_to`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "stay_id": 30001,
  "charttime": "2150-01-02T06:00:00Z",
  "itemid": 220045,
  "label": "Heart Rate",
  "value": "72",
  "valuenum": 72.0,
  "valueuom": "bpm"
}
```

### GET /api/diagnoses/

**Query parameters:** `patient`, `encounter`, `icd_code`, `search`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "seq_num": 1,
  "icd_code": "I2510",
  "icd_version": 10,
  "long_title": "Atherosclerotic heart disease of native coronary artery"
}
```

### GET /api/procedures/

**Query parameters:** `patient`, `encounter`, `icd_code`, `search`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "seq_num": 1,
  "icd_code": "0210093",
  "icd_version": 10,
  "long_title": "Bypass coronary artery"
}
```

### GET /api/medications/

**Query parameters:** `patient`, `encounter`, `drug`, `date_from`, `date_to`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "drug": "Aspirin",
  "drug_type": "MAIN",
  "starttime": "2150-01-01T08:00:00Z",
  "stoptime": "2150-01-05T00:00:00Z",
  "dose_val_rx": "325",
  "dose_unit_rx": "mg",
  "route": "PO",
  "prod_strength": "325mg Tab"
}
```

### GET /api/notes/

**Query parameters:** `patient`, `encounter`, `note_type`

**Response item:**

```json
{
  "id": 1,
  "patient_id": 1,
  "encounter_id": 1,
  "note_id": "N001",
  "note_type": "Discharge summary",
  "charttime": "2150-01-05T12:00:00Z",
  "text": "Patient was admitted for..."
}
```

### GET /api/lab-items/

**Response:** `[{ "itemid": 50912, "label": "Creatinine" }, ...]`

### GET /api/vital-items/

**Response:** `[{ "itemid": 220045, "label": "Heart Rate" }, ...]`

---

## Dashboards

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboards/demographics/` | Age, gender, race distributions |
| GET | `/api/dashboards/utilization/` | Admissions, LOS, ICU stats |
| GET | `/api/dashboards/clinical/` | Top diagnoses, labs, medications |
| GET | `/api/dashboards/missingness/` | Data completeness metrics |

### GET /api/dashboards/demographics/

```json
{
  "age_distribution": [{ "age": 65, "count": 10 }],
  "gender_distribution": [{ "gender": "M", "count": 500 }],
  "race_distribution": [{ "race": "WHITE", "count": 400 }],
  "mortality": { "alive": 900, "deceased": 100 }
}
```

### GET /api/dashboards/utilization/

```json
{
  "admissions_by_month": [{ "month": "2150-01", "count": 50 }],
  "los_by_admission_type": [{ "admission_type": "EMERGENCY", "avg_los": 5.2 }],
  "icu_stats": {
    "total_icu_stays": 200,
    "avg_icu_los": 3.1,
    "patients_with_icu": 150,
    "total_patients": 1000
  }
}
```

### GET /api/dashboards/clinical/

```json
{
  "top_diagnoses": [{ "icd_code": "I2510", "long_title": "...", "count": 50 }],
  "top_labs": [{ "label": "Creatinine", "count": 5000 }],
  "top_medications": [{ "drug": "Aspirin", "count": 300 }]
}
```

### GET /api/dashboards/missingness/

```json
{
  "completeness": [
    { "data_type": "Lab values", "total": 10000, "non_null": 9500, "pct": 95.0 }
  ]
}
```

---

## Research

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/research/cohorts/` | List cohort definitions |
| POST | `/api/research/cohorts/` | Create cohort |
| GET | `/api/research/cohorts/:id/` | Cohort detail |
| PUT | `/api/research/cohorts/:id/` | Update cohort |
| DELETE | `/api/research/cohorts/:id/` | Delete cohort |
| POST | `/api/research/cohorts/:id/execute/` | Execute cohort criteria |
| GET | `/api/research/cohorts/:id/stats/` | Cohort statistics |
| GET | `/api/research/cohorts/:id/members/` | Cohort members |
| POST | `/api/research/cohorts/compare/` | Compare two cohorts |
| GET | `/api/research/queries/` | List saved queries |
| POST | `/api/research/queries/` | Create saved query |
| DELETE | `/api/research/queries/:id/` | Delete saved query |
| POST | `/api/research/queries/:id/run/` | Execute saved query |
| POST | `/api/research/search/` | Structured patient search |
| POST | `/api/research/export/` | Export data |

### POST /api/research/cohorts/

**Request body:**

```json
{
  "name": "Sepsis cohort",
  "description": "Patients with sepsis diagnosis",
  "criteria": {
    "diagnosis_codes": ["A41"],
    "age_min": 18,
    "age_max": 90
  }
}
```

### POST /api/research/cohorts/:id/execute/

**Response:**

```json
{
  "patient_count": 150,
  "encounter_count": 200,
  "members": [
    { "id": 1, "cohort": 1, "subject_id": 10001, "hadm_id": 20001, "group_label": "" }
  ]
}
```

### GET /api/research/cohorts/:id/stats/

**Response:**

```json
{
  "name": "Sepsis cohort",
  "patient_count": 150,
  "encounter_count": 200,
  "avg_age": 62.5,
  "gender_distribution": { "M": 80, "F": 70 },
  "age_distribution": { "18-30": 10, "31-45": 20, "46-60": 40, "61-75": 50, "76-90": 30 },
  "mortality_rate": 15.0,
  "mortality_count": 22,
  "group_distribution": {}
}
```

### GET /api/research/cohorts/:id/members/

**Query parameters:** `page`, `page_size`, `search`, `group`

**Response item:**

```json
{
  "subject_id": 10001,
  "gender": "M",
  "anchor_age": 65,
  "group_label": "",
  "hadm_id": 20001,
  "admittime": "2150-01-01T00:00:00Z",
  "admission_type": "EMERGENCY",
  "hospital_expire_flag": false
}
```

### POST /api/research/cohorts/compare/

**Request body:** `{ "cohort_a": 1, "cohort_b": 2 }`

**Response:** `{ "cohort_a": { ...stats }, "cohort_b": { ...stats } }`

### POST /api/research/queries/:id/run/

**Response:**

```json
{
  "total_results": 50,
  "encounters": [
    { "hadm_id": 20001, "subject_id": 10001, "admittime": "...", "dischtime": "...", "admission_type": "EMERGENCY" }
  ]
}
```

### POST /api/research/search/

**Request body:**

```json
{
  "criteria": { "diagnosis_codes": ["I25"], "gender": "M" },
  "page": 1,
  "page_size": 50
}
```

**Response:**

```json
{
  "count": 100,
  "page": 1,
  "page_size": 50,
  "results": [
    {
      "patient_id": 1,
      "subject_id": 10001,
      "hadm_id": 20001,
      "admittime": "...",
      "dischtime": "...",
      "admission_type": "EMERGENCY",
      "group_label": "",
      "diagnoses": [{ "icd_code": "I2510", "title": "..." }]
    }
  ]
}
```

### POST /api/research/export/

**Request body:**

```json
{
  "format": "json",
  "cohort_id": 1,
  "patient_ids": [10001, 10002],
  "data_types": ["demographics", "encounters", "labs", "vitals", "diagnoses", "medications", "notes"]
}
```

- `format` — `"json"` or `"csv"`
- `cohort_id` — optional, filter by cohort
- `patient_ids` — optional, filter by specific patients
- `data_types` — required, one or more of: demographics, encounters, labs, vitals, diagnoses, medications, notes

**Response (JSON):** Object with keys matching data_types, each containing arrays of records.

**Response (CSV):** Streaming CSV file download.

---

## FHIR R4

FHIR endpoints are served at `/fhir/` (not `/api/`). Responses use `application/fhir+json`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/fhir/metadata` | CapabilityStatement |
| GET | `/fhir/Patient/` | Search patients |
| GET | `/fhir/Patient/:id/` | Read patient |
| GET | `/fhir/Patient/:id/$everything` | All resources for patient |
| GET | `/fhir/Encounter/` | Search encounters |
| GET | `/fhir/Encounter/:id/` | Read encounter |
| GET | `/fhir/Observation/` | Search observations |
| GET | `/fhir/Observation/:id/` | Read observation |
| GET | `/fhir/Condition/` | Search conditions |
| GET | `/fhir/Condition/:id/` | Read condition |
| GET | `/fhir/Procedure/` | Search procedures |
| GET | `/fhir/Procedure/:id/` | Read procedure |
| GET | `/fhir/MedicationRequest/` | Search medication requests |
| GET | `/fhir/MedicationRequest/:id/` | Read medication request |
| GET | `/fhir/DocumentReference/` | Search document references |
| GET | `/fhir/DocumentReference/:id/` | Read document reference |

### Search Parameters

| Resource | Parameters |
|----------|-----------|
| Patient | `_id`, `gender`, `_page` |
| Encounter | `patient`, `date` (supports `ge`/`le` prefix), `_page` |
| Observation | `patient`, `encounter`, `category` (laboratory, vital-signs), `code`, `date`, `_page` |
| Condition | `patient`, `encounter`, `code`, `_page` |
| Procedure | `patient`, `encounter`, `_page` |
| MedicationRequest | `patient`, `encounter`, `_page` |
| DocumentReference | `patient`, `encounter`, `type`, `_page` |

### Resource ID Formats

| Resource | Format | Example |
|----------|--------|---------|
| Patient | `mimic-{subject_id}` | `mimic-10001` |
| Encounter | `mimic-{hadm_id}` | `mimic-20001` |
| Observation (lab) | `mimic-lab-{labevent_id}` | `mimic-lab-12345` |
| Observation (vital) | `mimic-vital-{pk}` | `mimic-vital-1` |
| Condition | `mimic-dx-{hadm_id}-{seq_num}` | `mimic-dx-20001-1` |
| Procedure | `mimic-proc-{hadm_id}-{seq_num}` | `mimic-proc-20001-1` |
| MedicationRequest | `mimic-med-{pk}` | `mimic-med-1` |
| DocumentReference | `mimic-note-{note_id}` | `mimic-note-N001` |

### GET /fhir/Patient/:id/$everything

Returns a FHIR Bundle containing the Patient resource and up to 500 each of: Encounters, Observations (labs + vitals), Conditions, Procedures, MedicationRequests, and DocumentReferences.

---

## CLI Reference

MIMIC Explorer is launched via the `mimic-explorer` command after installation.

```
mimic-explorer [options]
```

| Option | Description |
|--------|-------------|
| `--test` | Run the built-in test suite to verify your installation |
| `--version`, `-V` | Show version number |
| `--port PORT`, `-p PORT` | Run the server on a specific port (default: auto-detect) |
| `--no-browser` | Start the server without opening a browser |
| `--help`, `-h` | Show help message |

### Examples

```bash
# Start the app (opens browser automatically)
mimic-explorer

# Start on a specific port without opening a browser
mimic-explorer --port 8080 --no-browser

# Verify your installation is working
mimic-explorer --test
```

---

## Testing

MIMIC Explorer includes a built-in test suite with 62 tests that verify the entire application stack — models, import pipeline, REST API, and FHIR endpoints.

### Running Tests

```bash
mimic-explorer --test
```

This runs all tests against a bundled set of small fixture files (10 patients) and displays results in a readable format. Each passing test shows what it verified; each failing test shows a diagnostic message explaining what went wrong and where to look.

### What the Tests Cover

| Category | Tests | What's verified |
|----------|-------|-----------------|
| **Models** | 12 | Patient, Encounter, Diagnosis, LabEvent, Note, VitalSign creation; SystemConfig singleton; unique constraints; VITAL_SIGN_ITEMIDS lookup |
| **Import Pipeline** | 11 | Folder validation, full import with all modules, per-stage row counts, patient_limit filtering, module-selective imports (hosp-only skips ICU) |
| **REST API** | 22 | Status endpoint, folder validation, patient list/detail/filter, encounter list/detail/sub-resources, clinical endpoints (labs, diagnoses, medications, vitals), timeline, reset, supplement import (idempotency, 400/202 responses) |
| **FHIR R4** | 17 | CapabilityStatement, Patient/Encounter/Observation/Condition/Procedure/MedicationRequest/DocumentReference read and search, Patient/$everything, 404 OperationOutcome |

### Interpreting Results

**All tests pass:**
```
  Results: 60 passed, 2 skipped (62 total)
  All tests passed! Your installation is working correctly.
```

**A test fails:**
```
  FAIL  Import should create exactly 10 patients from fixtures.
        Expected 10 patients, got 0. The fixture file
        tests/fixtures/mimic-iv-test/hosp/patients.csv should have exactly
        10 rows. If you see 0, the import pipeline may have failed silently.
```

Each failure message tells you:
1. What the expected result was
2. What actually happened
3. Which file or function to check

### Common Issues

- **0 patients imported**: Check that `tests/fixtures/mimic-iv-test/` exists and contains the CSV files. If you installed via pip, the fixtures should be bundled.
- **Database errors**: The tests use an in-memory SQLite database, so they won't affect your imported data.
- **Import failures**: Check `core/importer.py` — the error message will point to the specific import stage that failed.
