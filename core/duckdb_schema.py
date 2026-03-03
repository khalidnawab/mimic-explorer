"""
DuckDB schema definitions for clinical data tables.

All 11 clinical tables with columns, indexes, and unique constraints
matching the previous Django model definitions.
"""

# Sequences for auto-incrementing IDs
SEQUENCES = [
    "CREATE SEQUENCE IF NOT EXISTS patient_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS encounter_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS icu_stay_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS transfer_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS lab_event_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS vital_sign_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS diagnosis_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS procedure_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS medication_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS med_admin_id_seq START 1",
    "CREATE SEQUENCE IF NOT EXISTS note_id_seq START 1",
]

TABLES = {
    'patient': """
        CREATE TABLE IF NOT EXISTS patient (
            id INTEGER PRIMARY KEY DEFAULT nextval('patient_id_seq'),
            subject_id INTEGER NOT NULL UNIQUE,
            gender VARCHAR NOT NULL,
            anchor_age INTEGER NOT NULL,
            anchor_year INTEGER NOT NULL,
            anchor_year_group VARCHAR NOT NULL,
            dod DATE
        )
    """,
    'encounter': """
        CREATE TABLE IF NOT EXISTS encounter (
            id INTEGER PRIMARY KEY DEFAULT nextval('encounter_id_seq'),
            patient_id INTEGER NOT NULL,
            hadm_id INTEGER NOT NULL UNIQUE,
            admittime TIMESTAMP NOT NULL,
            dischtime TIMESTAMP,
            deathtime TIMESTAMP,
            admission_type VARCHAR NOT NULL,
            admit_provider_id VARCHAR DEFAULT '',
            admission_location VARCHAR DEFAULT '',
            discharge_location VARCHAR DEFAULT '',
            insurance VARCHAR DEFAULT '',
            language VARCHAR DEFAULT '',
            marital_status VARCHAR DEFAULT '',
            race VARCHAR DEFAULT '',
            edregtime TIMESTAMP,
            edouttime TIMESTAMP,
            hospital_expire_flag BOOLEAN DEFAULT FALSE
        )
    """,
    'icu_stay': """
        CREATE TABLE IF NOT EXISTS icu_stay (
            id INTEGER PRIMARY KEY DEFAULT nextval('icu_stay_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            stay_id INTEGER NOT NULL UNIQUE,
            first_careunit VARCHAR NOT NULL,
            last_careunit VARCHAR NOT NULL,
            intime TIMESTAMP NOT NULL,
            outtime TIMESTAMP,
            los DOUBLE
        )
    """,
    'transfer': """
        CREATE TABLE IF NOT EXISTS transfer (
            id INTEGER PRIMARY KEY DEFAULT nextval('transfer_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER,
            transfer_id INTEGER NOT NULL UNIQUE,
            eventtype VARCHAR NOT NULL,
            careunit VARCHAR DEFAULT '',
            intime TIMESTAMP NOT NULL,
            outtime TIMESTAMP
        )
    """,
    'lab_event': """
        CREATE TABLE IF NOT EXISTS lab_event (
            id INTEGER PRIMARY KEY DEFAULT nextval('lab_event_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER,
            labevent_id BIGINT NOT NULL UNIQUE,
            specimen_id INTEGER,
            itemid INTEGER NOT NULL,
            label VARCHAR NOT NULL,
            fluid VARCHAR DEFAULT '',
            category VARCHAR DEFAULT '',
            charttime TIMESTAMP NOT NULL,
            storetime TIMESTAMP,
            value VARCHAR,
            valuenum DOUBLE,
            valueuom VARCHAR DEFAULT '',
            ref_range_lower DOUBLE,
            ref_range_upper DOUBLE,
            flag VARCHAR DEFAULT '',
            priority VARCHAR DEFAULT '',
            comments VARCHAR DEFAULT ''
        )
    """,
    'vital_sign': """
        CREATE TABLE IF NOT EXISTS vital_sign (
            id INTEGER PRIMARY KEY DEFAULT nextval('vital_sign_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER,
            icu_stay_id INTEGER,
            stay_id INTEGER,
            charttime TIMESTAMP NOT NULL,
            itemid INTEGER NOT NULL,
            label VARCHAR NOT NULL,
            value VARCHAR,
            valuenum DOUBLE,
            valueuom VARCHAR DEFAULT '',
            UNIQUE (patient_id, stay_id, charttime, itemid)
        )
    """,
    'diagnosis': """
        CREATE TABLE IF NOT EXISTS diagnosis (
            id INTEGER PRIMARY KEY DEFAULT nextval('diagnosis_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            seq_num INTEGER NOT NULL,
            icd_code VARCHAR NOT NULL,
            icd_version INTEGER NOT NULL,
            long_title VARCHAR NOT NULL,
            UNIQUE (encounter_id, seq_num)
        )
    """,
    'procedure': """
        CREATE TABLE IF NOT EXISTS procedure (
            id INTEGER PRIMARY KEY DEFAULT nextval('procedure_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            seq_num INTEGER NOT NULL,
            icd_code VARCHAR NOT NULL,
            icd_version INTEGER NOT NULL,
            long_title VARCHAR NOT NULL,
            UNIQUE (encounter_id, seq_num)
        )
    """,
    'medication': """
        CREATE TABLE IF NOT EXISTS medication (
            id INTEGER PRIMARY KEY DEFAULT nextval('medication_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER NOT NULL,
            pharmacy_id INTEGER,
            poe_id VARCHAR DEFAULT '',
            starttime TIMESTAMP,
            stoptime TIMESTAMP,
            drug_type VARCHAR DEFAULT '',
            drug VARCHAR NOT NULL,
            gsn VARCHAR DEFAULT '',
            ndc VARCHAR DEFAULT '',
            prod_strength VARCHAR DEFAULT '',
            form_rx VARCHAR DEFAULT '',
            dose_val_rx VARCHAR DEFAULT '',
            dose_unit_rx VARCHAR DEFAULT '',
            form_val_disp VARCHAR DEFAULT '',
            form_unit_disp VARCHAR DEFAULT '',
            doses_per_24_hrs DOUBLE,
            route VARCHAR DEFAULT '',
            UNIQUE (encounter_id, pharmacy_id, drug, starttime)
        )
    """,
    'medication_administration': """
        CREATE TABLE IF NOT EXISTS medication_administration (
            id INTEGER PRIMARY KEY DEFAULT nextval('med_admin_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER,
            icu_stay_id INTEGER,
            emar_id VARCHAR DEFAULT '',
            pharmacy_id INTEGER,
            charttime TIMESTAMP NOT NULL,
            medication VARCHAR NOT NULL,
            event_txt VARCHAR DEFAULT '',
            dose_given VARCHAR DEFAULT '',
            dose_given_unit VARCHAR DEFAULT '',
            route VARCHAR DEFAULT '',
            UNIQUE (patient_id, emar_id)
        )
    """,
    'note': """
        CREATE TABLE IF NOT EXISTS note (
            id INTEGER PRIMARY KEY DEFAULT nextval('note_id_seq'),
            patient_id INTEGER NOT NULL,
            encounter_id INTEGER,
            note_id VARCHAR NOT NULL UNIQUE,
            note_type VARCHAR NOT NULL,
            note_seq INTEGER,
            charttime TIMESTAMP,
            storetime TIMESTAMP,
            text VARCHAR NOT NULL
        )
    """,
}

INDEXES = [
    # patient
    "CREATE INDEX IF NOT EXISTS idx_patient_gender ON patient (gender)",
    "CREATE INDEX IF NOT EXISTS idx_patient_anchor_age ON patient (anchor_age)",
    # encounter
    "CREATE INDEX IF NOT EXISTS idx_encounter_admittime ON encounter (admittime)",
    "CREATE INDEX IF NOT EXISTS idx_encounter_admission_type ON encounter (admission_type)",
    "CREATE INDEX IF NOT EXISTS idx_encounter_patient_admittime ON encounter (patient_id, admittime)",
    # icu_stay
    "CREATE INDEX IF NOT EXISTS idx_icu_stay_intime ON icu_stay (intime)",
    "CREATE INDEX IF NOT EXISTS idx_icu_stay_patient_intime ON icu_stay (patient_id, intime)",
    # lab_event
    "CREATE INDEX IF NOT EXISTS idx_lab_event_itemid ON lab_event (itemid)",
    "CREATE INDEX IF NOT EXISTS idx_lab_event_charttime ON lab_event (charttime)",
    "CREATE INDEX IF NOT EXISTS idx_lab_event_patient_charttime ON lab_event (patient_id, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_lab_event_encounter_charttime ON lab_event (encounter_id, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_lab_event_itemid_charttime ON lab_event (itemid, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_lab_event_label ON lab_event (label)",
    # vital_sign
    "CREATE INDEX IF NOT EXISTS idx_vital_sign_patient_charttime ON vital_sign (patient_id, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_vital_sign_encounter_charttime ON vital_sign (encounter_id, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_vital_sign_stay_charttime ON vital_sign (stay_id, charttime)",
    "CREATE INDEX IF NOT EXISTS idx_vital_sign_label_charttime ON vital_sign (label, charttime)",
    # diagnosis
    "CREATE INDEX IF NOT EXISTS idx_diagnosis_icd_code ON diagnosis (icd_code)",
    "CREATE INDEX IF NOT EXISTS idx_diagnosis_encounter_seq ON diagnosis (encounter_id, seq_num)",
    # procedure
    "CREATE INDEX IF NOT EXISTS idx_procedure_icd_code ON procedure (icd_code)",
    "CREATE INDEX IF NOT EXISTS idx_procedure_encounter_seq ON procedure (encounter_id, seq_num)",
    # medication
    "CREATE INDEX IF NOT EXISTS idx_medication_drug ON medication (drug)",
    "CREATE INDEX IF NOT EXISTS idx_medication_encounter_starttime ON medication (encounter_id, starttime)",
    # medication_administration
    "CREATE INDEX IF NOT EXISTS idx_med_admin_medication ON medication_administration (medication)",
    "CREATE INDEX IF NOT EXISTS idx_med_admin_encounter_charttime ON medication_administration (encounter_id, charttime)",
    # note
    "CREATE INDEX IF NOT EXISTS idx_note_note_type ON note (note_type)",
    "CREATE INDEX IF NOT EXISTS idx_note_charttime ON note (charttime)",
    "CREATE INDEX IF NOT EXISTS idx_note_encounter_charttime ON note (encounter_id, charttime)",
]


def ensure_schema(conn):
    """Create all sequences, tables, and indexes if they don't exist."""
    for seq in SEQUENCES:
        conn.execute(seq)
    for ddl in TABLES.values():
        conn.execute(ddl)
    for idx in INDEXES:
        conn.execute(idx)


def drop_all_tables(conn):
    """Drop all clinical data tables and sequences."""
    for table_name in reversed(list(TABLES.keys())):
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    for seq in SEQUENCES:
        # Extract sequence name from CREATE SEQUENCE statement
        seq_name = seq.split('IF NOT EXISTS ')[1].split(' ')[0]
        conn.execute(f"DROP SEQUENCE IF EXISTS {seq_name}")
