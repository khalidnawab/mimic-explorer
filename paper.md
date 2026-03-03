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
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 1 January 2025
bibliography: references.bib
---

# Summary

MIMIC Explorer is a locally installable, single-user web application that
provides an interactive research sandbox for the MIMIC-IV clinical dataset
[@johnson2023mimic]. It combines a Django REST backend with a React frontend
to offer an EHR viewer, research workbench, analytics dashboards, and a
FHIR R4 API [@hl7fhir] — all running entirely on the researcher's own machine
with no cloud dependencies or authentication requirements.

# Statement of Need

The MIMIC-IV dataset is one of the most widely used freely available electronic
health record datasets in clinical informatics research. However, researchers
who wish to explore and analyze MIMIC-IV data face a significant setup burden:
they must configure database servers, write custom SQL queries, and build their
own visualization pipelines before any substantive analysis can begin.

Existing tools such as MIMIC-Extract and other pipeline-oriented packages focus
on producing analysis-ready flat files but do not provide an interactive
exploration interface. Cloud-hosted platforms like Google BigQuery offer SQL
access but require data uploads and ongoing costs, and they do not support
FHIR-based interoperability.

MIMIC Explorer fills this gap by providing a turnkey, pip-installable application
that lets researchers import MIMIC-IV CSV files, browse patient records in an
EHR-like interface, build cohorts with a visual criteria engine, run structured
queries, and export data — all within minutes of installation.

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
- **Hybrid database architecture**: SQLite for application state via Django ORM
  [@django], DuckDB [@raasveldt2019duckdb] for high-performance analytical
  queries over clinical data.

# References
