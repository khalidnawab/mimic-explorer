# MIMIC Explorer

A locally installable EHR research sandbox for the MIMIC-IV clinical dataset.

## Features

- **EHR Viewer** — Patient search, encounter detail, clinical timeline
- **Dashboards** — Demographics, utilization, lab/medication summaries, data completeness
- **Research Workbench** — Cohort builder with criteria engine, structured search, CSV/JSON export
- **FHIR R4 API** — On-the-fly transformation to FHIR resources with search and `$everything`

## Quick Start

```bash
pip install mimic-explorer
mimic-explorer
```

Open `http://localhost:8765` and follow the setup wizard to point at your MIMIC-IV CSV files.

## Prerequisites

- **Python 3.10+**
- **MIMIC-IV dataset** — requires credentialed access via [PhysioNet](https://physionet.org/content/mimiciv/)

## Dependencies

| Package | Purpose |
|---------|---------|
| Django 6.x + DRF | REST API backend |
| DuckDB | High-performance analytical queries over clinical data |
| fhir.resources | FHIR R4 resource validation and serialization |
| orjson | Fast JSON serialization |
| django-cors-headers | CORS support for local development |

All dependencies are installed automatically via `pip install mimic-explorer`.

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

## Architecture

| Layer | Technology |
|-------|-----------|
| Backend | Django + Django REST Framework |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| App Database | SQLite (WAL mode) |
| Clinical Database | DuckDB |
| FHIR | On-the-fly R4 transformation (no stored resources) |

## Security

MIMIC Explorer is designed as a **single-user local application**. It binds to `localhost` only and makes no external network calls. There is no authentication layer — do not expose it to the public internet. Set the `MIMIC_DEBUG=true` environment variable to enable Django debug mode during development.

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

## License

[MIT](LICENSE)
