from django.db import models

# Clinical models (LabEvent, VitalSign, Diagnosis, Procedure, Medication,
# MedicationAdministration, Note) have been migrated to DuckDB.
# See core/duckdb_schema.py for table definitions.

VITAL_SIGN_ITEMIDS = {
    220045: 'Heart Rate',
    220050: 'Arterial Blood Pressure systolic',
    220051: 'Arterial Blood Pressure diastolic',
    220052: 'Arterial Blood Pressure mean',
    220179: 'Non Invasive Blood Pressure systolic',
    220180: 'Non Invasive Blood Pressure diastolic',
    220181: 'Non Invasive Blood Pressure mean',
    220210: 'Respiratory Rate',
    220277: 'SpO2',
    223761: 'Temperature Fahrenheit',
    223762: 'Temperature Celsius',
    226512: 'Weight (kg)',
    226730: 'Height (cm)',
}
