# MIMIC Explorer

A locally installable EHR research sandbox for the MIMIC-IV clinical dataset.

## Features

- **EHR Viewer** — Patient search, encounter detail, clinical timeline
- **Dashboards** — Demographics, utilization, lab/medication summaries, data completeness
- **Research Workbench** — Cohort builder with criteria engine, structured search, CSV/JSON export
- **FHIR R4 API** — On-the-fly transformation to FHIR resources with search and `$everything`

## Installation

```bash
pip install mimic-explorer
```

This installs MIMIC Explorer and all its dependencies:

- **Django 6.x + Django REST Framework** — REST API backend
- **DuckDB** — High-performance analytical queries over clinical data
- **fhir.resources** — FHIR R4 resource validation and serialization
- **orjson** — Fast JSON serialization
- **django-cors-headers** — CORS support for local development

Python 3.10 or later is required. No external database server is needed.

## Quick Start

### With MIMIC-IV data

```bash
pip install mimic-explorer
mimic-explorer
```

Your browser will open to `http://localhost:8765`. The setup wizard guides you through selecting your MIMIC-IV data folder, validating files, and importing. Start with a small patient limit (100--1,000) to test quickly, then use supplement import to add more data later.

### Without MIMIC-IV data (demo with test fixtures)

A synthetic dataset with 10 fictional patients is included for testing and demonstration. This data is entirely made up and contains no real patient information.

```bash
pip install mimic-explorer
mimic-explorer --data tests/fixtures/mimic-iv-test/
```

Or start the app normally and point the setup wizard at the `tests/fixtures/mimic-iv-test/` folder.

### Example API calls

Once data is imported, you can query the REST and FHIR APIs:

```bash
# List patients
curl http://localhost:8765/api/patients/

# Patient detail
curl http://localhost:8765/api/patients/10001/

# Patient timeline
curl http://localhost:8765/api/patients/10001/timeline/

# FHIR Patient resource
curl http://localhost:8765/fhir/Patient/mimic-10001/

# FHIR lab observations
curl "http://localhost:8765/fhir/Observation/?category=laboratory&patient=mimic-10001"

# FHIR $everything (all resources for a patient)
curl http://localhost:8765/fhir/Patient/mimic-10001/\$everything
```

## Prerequisites

- **Python 3.10+**
- **MIMIC-IV dataset** — requires credentialed access via [PhysioNet](https://physionet.org/content/mimiciv/)

### Obtaining MIMIC-IV Data

MIMIC-IV is a freely available dataset, but access requires completion of a credentialing process:

1. Create a [PhysioNet](https://physionet.org/) account
2. Complete the required CITI training course on human subjects research
3. Sign the data use agreement for [MIMIC-IV](https://physionet.org/content/mimiciv/)
4. Download the CSV files (typically as `.csv.gz`)

The credentialing process typically takes 1--2 weeks. You can use the included synthetic test dataset in the meantime to explore the application.

## Expected Data Structure

MIMIC Explorer expects the standard MIMIC-IV directory layout from PhysioNet. Files can be `.csv` or `.csv.gz`.

```
mimic-iv/
├── hosp/                          ← Required
│   ├── patients.csv.gz            Demographics (subject_id, gender, age, date of death)
│   ├── admissions.csv.gz          Hospital admissions (times, type, location, insurance)
│   ├── diagnoses_icd.csv.gz       ICD diagnosis codes per admission
│   ├── procedures_icd.csv.gz      ICD procedure codes per admission
│   ├── labevents.csv.gz           Lab results (value, units, reference ranges)
│   ├── prescriptions.csv.gz       Medication orders (drug, dose, route, timing)
│   ├── d_labitems.csv.gz          Reference: lab item IDs → names
│   ├── d_icd_diagnoses.csv.gz     Reference: ICD diagnosis code descriptions
│   ├── d_icd_procedures.csv.gz    Reference: ICD procedure code descriptions
│   ├── transfers.csv.gz           (optional) Ward transfers
│   └── emar.csv.gz                (optional) Medication administration records
├── icu/                           ← Optional
│   ├── icustays.csv.gz            ICU stays (care unit, LOS, in/out times)
│   ├── chartevents.csv.gz         Vital signs (HR, BP, SpO2, temp, RR)
│   └── d_items.csv.gz             Reference: chart item IDs → names
└── note/                          ← Optional (separate PhysioNet download)
    ├── discharge.csv.gz           Discharge summary notes (free text)
    └── radiology.csv.gz           Radiology report notes (free text)
```

All files are linked by `subject_id` (patient) and `hadm_id` (hospital admission). The importer loads patients first, then joins all downstream data against existing patients — if you set a patient limit, everything is automatically scoped.

## Sample Test Dataset

A synthetic dataset with 10 fictional patients is included at `tests/fixtures/mimic-iv-test/` for testing and demonstration. This data is entirely made up and **does not contain any real patient information**.

```
tests/fixtures/mimic-iv-test/
├── hosp/       10 patients, 12 admissions, labs, meds, diagnoses, procedures
├── icu/        ICU stays, vital signs (chartevents)
└── note/       3 discharge notes
```

You can also run the automated test suite against this data:

```bash
mimic-explorer --test
```

All 62 tests run against this synthetic dataset using an in-memory DuckDB instance — no MIMIC-IV access is required to verify the installation.

## Architecture

| Layer | Technology |
|-------|-----------|
| Backend | Django + Django REST Framework |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| App Database | SQLite (WAL mode) |
| Clinical Database | DuckDB |
| FHIR | On-the-fly R4 transformation (no stored resources) |

## Security

> **Warning:** MIMIC Explorer is designed as a **single-user local application**. It binds to `localhost` only and makes no external network calls. There is no authentication layer — **never expose this application to the public internet or a shared network**.

- `DEBUG` mode is off by default. Set `MIMIC_DEBUG=true` to enable it during development.
- `CORS_ALLOW_ALL_ORIGINS` is off by default. It is automatically enabled in debug mode, or can be forced with `MIMIC_CORS_ALL=true`.
- The server binds to `127.0.0.1` only and `ALLOWED_HOSTS` is restricted to `localhost` and `127.0.0.1`.

If you are working with real MIMIC-IV data (which contains de-identified but sensitive clinical information), ensure your machine has appropriate access controls and disk encryption enabled per your institution's data use agreement.

## Documentation

Full API reference with all endpoints, parameters, and response shapes: **[docs/API.md](docs/API.md)**

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and PR guidelines.

## Citation

If you use MIMIC Explorer in your research, please cite it:

```bibtex
@software{nawab2025mimic_explorer,
  title  = {MIMIC Explorer},
  author = {Nawab, Khalid},
  year   = {2025},
  url    = {https://github.com/khalidnawab/mimic-explorer}
}
```

See [CITATION.cff](CITATION.cff) for the full citation metadata.

## Author

**Khalid Nawab** — khalid.nwb@gmail.com

Development assisted by [Claude Code](https://claude.ai/claude-code) (Anthropic).

## License

[MIT](LICENSE)
