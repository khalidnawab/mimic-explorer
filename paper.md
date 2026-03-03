---
title: "MIMIC Explorer: A Locally Installable EHR Research Sandbox for MIMIC-IV"
tags:
  - Python
  - electronic health records
  - MIMIC-IV
  - FHIR
  - clinical research
authors:
  - name: Khalid Nawab
    email: khalid.nwb@gmail.com
    orcid: 0000-0002-1824-413X
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 3 March 2026
bibliography: references.bib
---

# Summary

MIMIC Explorer is a locally installable, single-user web application that
provides an interactive research sandbox for the MIMIC-IV clinical dataset
[@johnson2023mimic]. It combines a Django REST backend [@django] with a React
frontend to offer an EHR viewer, research workbench, analytics dashboards, and
a FHIR R4 API [@hl7fhir] — all running entirely on the researcher's own
machine with no cloud dependencies or authentication requirements.

# Statement of Need

The MIMIC-IV dataset is one of the most widely used freely available electronic
health record datasets in clinical informatics research. However, researchers
who wish to explore and analyze MIMIC-IV data face a significant setup burden:
they must configure database servers, write custom SQL queries, and build their
own visualization pipelines before any substantive analysis can begin.

MIMIC Explorer fills this gap by providing a turnkey, pip-installable
application that lets researchers import MIMIC-IV CSV files, browse patient
records in an EHR-like interface, build cohorts with a visual criteria engine,
run structured queries, and export data — all within minutes of installation.

# State of the Field

Several tools exist for working with MIMIC data, each addressing different
parts of the research workflow:

- **MIMIC-Extract** [@wang2020mimicextract] provides a data extraction and
  preprocessing pipeline that produces analysis-ready flat files from MIMIC-III.
  It focuses on machine learning readiness rather than interactive exploration,
  and it does not support MIMIC-IV natively.

- **MIMIC-Code** [@johnson2018mimiccode] offers a community-maintained
  repository of SQL queries and analysis scripts. It is invaluable as a
  reference but requires researchers to set up their own database server
  (typically PostgreSQL) and execute queries manually.

- **Google BigQuery** hosts MIMIC-IV in the cloud, offering SQL access without
  local database setup. However, it requires data use agreements to be
  re-executed through Google, incurs query costs at scale, and does not provide
  a graphical exploration interface or FHIR interoperability.

- **FHIR servers** (e.g., HAPI FHIR) can represent clinical data in a
  standards-based format but require a separate ETL pipeline to load MIMIC data
  and do not include built-in exploration or cohort-building tools.

MIMIC Explorer is unique in combining four capabilities in a single,
pip-installable package: (1) a graphical EHR viewer for patient-level
exploration, (2) a visual cohort builder for research workflows, (3) analytics
dashboards for population-level summaries, and (4) a FHIR R4 API for
standards-based data access. Its hybrid SQLite and DuckDB
[@raasveldt2019duckdb] architecture enables fast analytical queries without
requiring an external database server. The application is designed for
individual researchers and runs entirely on localhost, keeping protected health
information on the researcher's own machine.

# Key Features

- **One-command installation**: `pip install mimic-explorer` followed by
  `mimic-explorer` launches the application with a guided setup wizard.
- **EHR Viewer**: Patient search, encounter browser, and clinical timeline
  displaying labs, vitals, medications, diagnoses, and procedures.
- **Research Workbench**: Visual cohort builder with demographic, diagnostic,
  and temporal criteria; structured search across all clinical domains;
  CSV and JSON export.
- **Analytics Dashboards**: Demographics distributions, utilization statistics,
  lab and medication summaries, and data completeness (missingness) analysis.
- **FHIR R4 API**: On-the-fly transformation of MIMIC-IV data to FHIR R4
  resources (Patient, Encounter, Observation, Condition, Procedure,
  MedicationRequest) with search parameters and `$everything` operation.
- **Hybrid database architecture**: SQLite for application state via Django ORM,
  DuckDB for high-performance analytical queries over clinical data.
- **Synthetic test dataset**: A 10-patient fictional dataset is included for
  testing and demonstration without requiring MIMIC-IV access.

# Acknowledgements

Development of MIMIC Explorer was assisted by Claude Code (Anthropic), an
AI-powered software engineering tool used for code generation, testing, and
documentation.

# References
