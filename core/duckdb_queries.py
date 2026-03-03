"""
DuckDB query layer for clinical data.

All clinical data queries in one place. Functions return plain dicts/lists
matching the current API JSON contract.
"""
from core.duckdb_manager import get_connection

PAGE_SIZE = 50


def _conn():
    """Return a new cursor for thread-safe concurrent access."""
    return get_connection().cursor()


# ---------------------------------------------------------------------------
# Patient queries
# ---------------------------------------------------------------------------

def get_patient_list(search=None, gender=None, age_min=None, age_max=None,
                     page=1, page_size=PAGE_SIZE):
    """Return paginated patient list with encounter counts."""
    conn = _conn()
    conditions = []
    params = []

    if search:
        conditions.append("CAST(p.subject_id AS VARCHAR) LIKE ?")
        params.append(f"%{search}%")
    if gender:
        conditions.append("p.gender = ?")
        params.append(gender)
    if age_min is not None:
        conditions.append("p.anchor_age >= ?")
        params.append(int(age_min))
    if age_max is not None:
        conditions.append("p.anchor_age <= ?")
        params.append(int(age_max))

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT p.id, p.subject_id, p.gender, p.anchor_age, p.anchor_year,
               p.anchor_year_group, p.dod,
               COUNT(e.id) AS encounter_count,
               COUNT(*) OVER() AS _total
        FROM patient p
        LEFT JOIN encounter e ON e.patient_id = p.id
        {where}
        GROUP BY p.id, p.subject_id, p.gender, p.anchor_age, p.anchor_year,
                 p.anchor_year_group, p.dod
        ORDER BY p.subject_id
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    results = []
    for r in rows:
        results.append({
            'id': r[0], 'subject_id': r[1], 'gender': r[2],
            'anchor_age': r[3], 'anchor_year': r[4],
            'anchor_year_group': r[5],
            'dod': str(r[6]) if r[6] else None,
            'encounter_count': r[7],
        })
    return {'count': total, 'results': results}


def get_patient_detail(subject_id):
    """Return single patient with encounters, or None."""
    conn = _conn()
    row = conn.execute("""
        SELECT id, subject_id, gender, anchor_age, anchor_year,
               anchor_year_group, dod
        FROM patient WHERE subject_id = ?
    """, [subject_id]).fetchone()
    if not row:
        return None

    patient_id = row[0]
    data = {
        'id': row[0], 'subject_id': row[1], 'gender': row[2],
        'anchor_age': row[3], 'anchor_year': row[4],
        'anchor_year_group': row[5],
        'dod': str(row[6]) if row[6] else None,
    }

    encounters = conn.execute("""
        SELECT id, hadm_id, admittime, dischtime, admission_type,
               discharge_location, hospital_expire_flag
        FROM encounter WHERE patient_id = ?
        ORDER BY admittime DESC
    """, [patient_id]).fetchall()

    data['encounters'] = [{
        'id': e[0], 'hadm_id': e[1],
        'admittime': _ts(e[2]), 'dischtime': _ts(e[3]),
        'admission_type': e[4], 'discharge_location': e[5],
        'hospital_expire_flag': bool(e[6]),
    } for e in encounters]

    return data


def get_patient_timeline(subject_id):
    """Return all events for a patient chronologically."""
    conn = _conn()
    row = conn.execute("SELECT id FROM patient WHERE subject_id = ?", [subject_id]).fetchone()
    if not row:
        return None

    pid = row[0]
    events = []

    # Encounters
    for enc in conn.execute("""
        SELECT hadm_id, admittime, dischtime, admission_type,
               admission_location, discharge_location
        FROM encounter WHERE patient_id = ? ORDER BY admittime
    """, [pid]).fetchall():
        events.append({
            'event_type': 'admission',
            'timestamp': _ts(enc[1]),
            'description': f'{enc[3]} admission',
            'encounter_id': enc[0],
            'detail': {'admission_type': enc[3], 'location': enc[4]},
        })
        if enc[2]:
            events.append({
                'event_type': 'discharge',
                'timestamp': _ts(enc[2]),
                'description': f'Discharged to {enc[5]}',
                'encounter_id': enc[0],
                'detail': {'discharge_location': enc[5]},
            })

    # ICU stays
    for stay in conn.execute("""
        SELECT s.stay_id, s.first_careunit, s.intime, e.hadm_id
        FROM icu_stay s
        LEFT JOIN encounter e ON s.encounter_id = e.id
        WHERE s.patient_id = ?
    """, [pid]).fetchall():
        events.append({
            'event_type': 'icu_admission',
            'timestamp': _ts(stay[2]),
            'description': f'ICU admission to {stay[1]}',
            'encounter_id': stay[3],
            'detail': {'careunit': stay[1], 'stay_id': stay[0]},
        })

    # Diagnoses
    for dx in conn.execute("""
        SELECT d.icd_code, d.icd_version, d.long_title, e.hadm_id, e.admittime
        FROM diagnosis d
        JOIN encounter e ON d.encounter_id = e.id
        WHERE d.patient_id = ?
    """, [pid]).fetchall():
        events.append({
            'event_type': 'diagnosis',
            'timestamp': _ts(dx[4]),
            'description': f'{dx[0]}: {dx[2]}',
            'encounter_id': dx[3],
            'detail': {'icd_code': dx[0], 'icd_version': dx[1]},
        })

    events.sort(key=lambda e: e['timestamp'] if e['timestamp'] else '0')
    return events


# ---------------------------------------------------------------------------
# Encounter queries
# ---------------------------------------------------------------------------

def get_encounter_list(patient=None, admission_type=None, date_from=None,
                       date_to=None, page=1, page_size=PAGE_SIZE):
    """Return paginated encounter list."""
    conn = _conn()
    conditions = []
    params = []

    if patient:
        conditions.append("p.subject_id = ?")
        params.append(int(patient))
    if admission_type:
        conditions.append("e.admission_type = ?")
        params.append(admission_type)
    if date_from:
        conditions.append("e.admittime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("e.admittime <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT e.id, e.hadm_id, e.patient_id, p.subject_id,
               e.admittime, e.dischtime, e.deathtime, e.admission_type,
               e.admission_location, e.discharge_location, e.insurance,
               e.language, e.marital_status, e.race, e.hospital_expire_flag,
               COUNT(*) OVER() AS _total
        FROM encounter e
        JOIN patient p ON e.patient_id = p.id
        {where}
        ORDER BY e.admittime DESC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    results = []
    for r in rows:
        results.append({
            'id': r[0], 'hadm_id': r[1], 'patient_id': r[2],
            'subject_id': r[3], 'admittime': _ts(r[4]),
            'dischtime': _ts(r[5]), 'deathtime': _ts(r[6]),
            'admission_type': r[7], 'admission_location': r[8],
            'discharge_location': r[9], 'insurance': r[10],
            'language': r[11], 'marital_status': r[12], 'race': r[13],
            'hospital_expire_flag': bool(r[14]),
        })
    return {'count': total, 'results': results}


def get_encounter_detail(hadm_id):
    """Return single encounter or None."""
    conn = _conn()
    r = conn.execute("""
        SELECT e.id, e.hadm_id, e.patient_id, p.subject_id,
               e.admittime, e.dischtime, e.deathtime, e.admission_type,
               e.admit_provider_id, e.admission_location, e.discharge_location,
               e.insurance, e.language, e.marital_status, e.race,
               e.edregtime, e.edouttime, e.hospital_expire_flag
        FROM encounter e
        JOIN patient p ON e.patient_id = p.id
        WHERE e.hadm_id = ?
    """, [hadm_id]).fetchone()
    if not r:
        return None
    return {
        'id': r[0], 'hadm_id': r[1], 'patient_id': r[2], 'subject_id': r[3],
        'admittime': _ts(r[4]), 'dischtime': _ts(r[5]), 'deathtime': _ts(r[6]),
        'admission_type': r[7], 'admit_provider_id': r[8],
        'admission_location': r[9], 'discharge_location': r[10],
        'insurance': r[11], 'language': r[12], 'marital_status': r[13],
        'race': r[14], 'edregtime': _ts(r[15]), 'edouttime': _ts(r[16]),
        'hospital_expire_flag': bool(r[17]),
    }


def _get_encounter_id(hadm_id):
    """Resolve hadm_id to internal id."""
    conn = _conn()
    row = conn.execute("SELECT id FROM encounter WHERE hadm_id = ?", [hadm_id]).fetchone()
    return row[0] if row else None


def get_encounter_labs(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_lab_events(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_vitals(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_vital_signs(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_diagnoses(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_diagnoses(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_procedures(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_procedures(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_medications(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_medications(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_notes(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}
    return _get_notes(encounter_id=enc_id, page=page, page_size=page_size)


def get_encounter_icu_stays(hadm_id, page=1, page_size=PAGE_SIZE):
    enc_id = _get_encounter_id(hadm_id)
    if enc_id is None:
        return {'count': 0, 'results': []}

    conn = _conn()
    offset = (page - 1) * page_size
    rows = conn.execute("""
        SELECT id, stay_id, first_careunit, last_careunit, intime, outtime, los,
               COUNT(*) OVER() AS _total
        FROM icu_stay WHERE encounter_id = ?
        ORDER BY intime DESC
        LIMIT ? OFFSET ?
    """, [enc_id, page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'stay_id': r[1], 'first_careunit': r[2],
            'last_careunit': r[3], 'intime': _ts(r[4]),
            'outtime': _ts(r[5]), 'los': r[6],
        } for r in rows],
    }


# ---------------------------------------------------------------------------
# Clinical list queries (labs, vitals, diagnoses, etc.)
# ---------------------------------------------------------------------------

def _resolve_subject_to_patient_id(subject_id):
    conn = _conn()
    row = conn.execute("SELECT id FROM patient WHERE subject_id = ?", [int(subject_id)]).fetchone()
    return row[0] if row else None


def _resolve_hadm_to_encounter_id(hadm_id):
    conn = _conn()
    row = conn.execute("SELECT id FROM encounter WHERE hadm_id = ?", [int(hadm_id)]).fetchone()
    return row[0] if row else None


def _get_lab_events(patient_subject_id=None, encounter_id=None, label=None,
                    itemid=None, date_from=None, date_to=None,
                    abnormal_only=False, page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("l.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("l.encounter_id = ?")
        params.append(encounter_id)
    if label:
        conditions.append("l.label ILIKE ?")
        params.append(f"%{label}%")
    if itemid:
        conditions.append("l.itemid = ?")
        params.append(int(itemid))
    if date_from:
        conditions.append("l.charttime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("l.charttime <= ?")
        params.append(date_to)
    if abnormal_only:
        conditions.append("l.flag != '' AND l.flag IS NOT NULL")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT l.id, l.patient_id, l.encounter_id, l.labevent_id, l.itemid,
               l.label, l.fluid, l.category, l.charttime, l.value, l.valuenum,
               l.valueuom, l.ref_range_lower, l.ref_range_upper, l.flag, l.priority,
               COUNT(*) OVER() AS _total
        FROM lab_event l
        {where}
        ORDER BY l.charttime DESC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'labevent_id': r[3], 'itemid': r[4], 'label': r[5],
            'fluid': r[6], 'category': r[7], 'charttime': _ts(r[8]),
            'value': r[9], 'valuenum': r[10], 'valueuom': r[11],
            'ref_range_lower': r[12], 'ref_range_upper': r[13],
            'flag': r[14], 'priority': r[15],
        } for r in rows],
    }


def get_labs_list(**kwargs):
    return _get_lab_events(**kwargs)


def _get_vital_signs(patient_subject_id=None, encounter_id=None, label=None,
                     itemid=None, date_from=None, date_to=None,
                     page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("v.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("v.encounter_id = ?")
        params.append(encounter_id)
    if label:
        conditions.append("v.label ILIKE ?")
        params.append(f"%{label}%")
    if itemid:
        conditions.append("v.itemid = ?")
        params.append(int(itemid))
    if date_from:
        conditions.append("v.charttime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("v.charttime <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT v.id, v.patient_id, v.encounter_id, v.stay_id, v.charttime,
               v.itemid, v.label, v.value, v.valuenum, v.valueuom,
               COUNT(*) OVER() AS _total
        FROM vital_sign v
        {where}
        ORDER BY v.charttime DESC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'stay_id': r[3], 'charttime': _ts(r[4]), 'itemid': r[5],
            'label': r[6], 'value': r[7], 'valuenum': r[8], 'valueuom': r[9],
        } for r in rows],
    }


def get_vitals_list(**kwargs):
    return _get_vital_signs(**kwargs)


def _get_diagnoses(patient_subject_id=None, encounter_id=None, icd_code=None,
                   search=None, page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("d.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("d.encounter_id = ?")
        params.append(encounter_id)
    if icd_code:
        conditions.append("d.icd_code ILIKE ?")
        params.append(f"{icd_code}%")
    if search:
        conditions.append("d.long_title ILIKE ?")
        params.append(f"%{search}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT d.id, d.patient_id, d.encounter_id, d.seq_num,
               d.icd_code, d.icd_version, d.long_title,
               COUNT(*) OVER() AS _total
        FROM diagnosis d
        {where}
        ORDER BY d.encounter_id, d.seq_num
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'seq_num': r[3], 'icd_code': r[4], 'icd_version': r[5],
            'long_title': r[6],
        } for r in rows],
    }


def get_diagnoses_list(**kwargs):
    return _get_diagnoses(**kwargs)


def _get_procedures(patient_subject_id=None, encounter_id=None, icd_code=None,
                    search=None, page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("pr.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("pr.encounter_id = ?")
        params.append(encounter_id)
    if icd_code:
        conditions.append("pr.icd_code ILIKE ?")
        params.append(f"{icd_code}%")
    if search:
        conditions.append("pr.long_title ILIKE ?")
        params.append(f"%{search}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT pr.id, pr.patient_id, pr.encounter_id, pr.seq_num,
               pr.icd_code, pr.icd_version, pr.long_title,
               COUNT(*) OVER() AS _total
        FROM procedure pr
        {where}
        ORDER BY pr.encounter_id, pr.seq_num
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'seq_num': r[3], 'icd_code': r[4], 'icd_version': r[5],
            'long_title': r[6],
        } for r in rows],
    }


def get_procedures_list(**kwargs):
    return _get_procedures(**kwargs)


def _get_medications(patient_subject_id=None, encounter_id=None, drug=None,
                     date_from=None, date_to=None, page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("m.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("m.encounter_id = ?")
        params.append(encounter_id)
    if drug:
        conditions.append("m.drug ILIKE ?")
        params.append(f"%{drug}%")
    if date_from:
        conditions.append("m.starttime >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("m.starttime <= ?")
        params.append(date_to)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT m.id, m.patient_id, m.encounter_id, m.drug, m.drug_type,
               m.starttime, m.stoptime, m.dose_val_rx, m.dose_unit_rx,
               m.route, m.prod_strength,
               COUNT(*) OVER() AS _total
        FROM medication m
        {where}
        ORDER BY m.starttime DESC NULLS LAST
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'drug': r[3], 'drug_type': r[4],
            'starttime': _ts(r[5]), 'stoptime': _ts(r[6]),
            'dose_val_rx': r[7], 'dose_unit_rx': r[8],
            'route': r[9], 'prod_strength': r[10],
        } for r in rows],
    }


def get_medications_list(**kwargs):
    return _get_medications(**kwargs)


def _get_notes(patient_subject_id=None, encounter_id=None, note_type=None,
               page=1, page_size=PAGE_SIZE):
    conn = _conn()
    conditions = []
    params = []

    if patient_subject_id:
        pid = _resolve_subject_to_patient_id(patient_subject_id)
        if pid is None:
            return {'count': 0, 'results': []}
        conditions.append("n.patient_id = ?")
        params.append(pid)
    if encounter_id:
        conditions.append("n.encounter_id = ?")
        params.append(encounter_id)
    if note_type:
        conditions.append("n.note_type = ?")
        params.append(note_type)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    rows = conn.execute(f"""
        SELECT n.id, n.patient_id, n.encounter_id, n.note_id, n.note_type,
               n.charttime, n.text,
               COUNT(*) OVER() AS _total
        FROM note n
        {where}
        ORDER BY n.charttime DESC NULLS LAST
        LIMIT ? OFFSET ?
    """, params + [page_size, offset]).fetchall()

    total = rows[0][-1] if rows else 0
    return {
        'count': total,
        'results': [{
            'id': r[0], 'patient_id': r[1], 'encounter_id': r[2],
            'note_id': r[3], 'note_type': r[4],
            'charttime': _ts(r[5]), 'text': r[6],
        } for r in rows],
    }


def get_notes_list(**kwargs):
    return _get_notes(**kwargs)


def get_lab_items():
    """Return distinct lab item references."""
    conn = _conn()
    rows = conn.execute("""
        SELECT DISTINCT itemid, label FROM lab_event
        ORDER BY label
    """).fetchall()
    return [{'itemid': r[0], 'label': r[1]} for r in rows]


def get_vital_items():
    """Return the vital sign item reference list."""
    from clinical.models import VITAL_SIGN_ITEMIDS
    return [
        {'itemid': k, 'label': v}
        for k, v in sorted(VITAL_SIGN_ITEMIDS.items(), key=lambda x: x[1])
    ]


# ---------------------------------------------------------------------------
# Dashboard queries
# ---------------------------------------------------------------------------

def get_demographics():
    conn = _conn()

    age_dist = conn.execute("""
        SELECT anchor_age AS age, COUNT(*) AS count
        FROM patient GROUP BY anchor_age ORDER BY anchor_age
    """).fetchall()

    gender_dist = conn.execute("""
        SELECT gender, COUNT(*) AS count
        FROM patient GROUP BY gender ORDER BY gender
    """).fetchall()

    race_dist = conn.execute("""
        SELECT race, COUNT(*) AS count FROM (
            SELECT DISTINCT ON (patient_id) patient_id, race
            FROM encounter ORDER BY patient_id, admittime
        ) sub
        GROUP BY race ORDER BY count DESC
    """).fetchall()

    alive = conn.execute("SELECT COUNT(*) FROM patient WHERE dod IS NULL").fetchone()[0]
    deceased = conn.execute("SELECT COUNT(*) FROM patient WHERE dod IS NOT NULL").fetchone()[0]

    return {
        'age_distribution': [{'age': r[0], 'count': r[1]} for r in age_dist],
        'gender_distribution': [{'gender': r[0], 'count': r[1]} for r in gender_dist],
        'race_distribution': [{'race': r[0], 'count': r[1]} for r in race_dist],
        'mortality': {'alive': alive, 'deceased': deceased},
    }


def get_utilization():
    conn = _conn()

    by_month = conn.execute("""
        SELECT strftime(admittime, '%Y-%m') AS month, COUNT(*) AS count
        FROM encounter
        GROUP BY month ORDER BY month
    """).fetchall()

    los_by_type = conn.execute("""
        SELECT admission_type,
               AVG(EXTRACT(EPOCH FROM (dischtime - admittime)) / 86400.0) AS avg_los
        FROM encounter
        WHERE dischtime IS NOT NULL
        GROUP BY admission_type ORDER BY admission_type
    """).fetchall()

    total_patients = conn.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    total_icu = conn.execute("SELECT COUNT(*) FROM icu_stay").fetchone()[0]
    avg_icu_los = conn.execute(
        "SELECT AVG(los) FROM icu_stay WHERE los IS NOT NULL"
    ).fetchone()[0]
    patients_icu = conn.execute(
        "SELECT COUNT(DISTINCT patient_id) FROM icu_stay"
    ).fetchone()[0]

    return {
        'admissions_by_month': [{'month': r[0], 'count': r[1]} for r in by_month],
        'los_by_admission_type': [
            {'admission_type': r[0], 'avg_los': round(r[1], 2) if r[1] else 0}
            for r in los_by_type
        ],
        'icu_stats': {
            'total_icu_stays': total_icu,
            'avg_icu_los': round(avg_icu_los, 2) if avg_icu_los else 0,
            'patients_with_icu': patients_icu,
            'total_patients': total_patients,
        },
    }


def get_clinical():
    conn = _conn()

    top_dx = conn.execute("""
        SELECT icd_code, long_title, COUNT(*) AS count
        FROM diagnosis GROUP BY icd_code, long_title
        ORDER BY count DESC LIMIT 20
    """).fetchall()

    top_labs = conn.execute("""
        SELECT label, COUNT(*) AS count
        FROM lab_event GROUP BY label
        ORDER BY count DESC LIMIT 20
    """).fetchall()

    top_meds = conn.execute("""
        SELECT drug, COUNT(*) AS count
        FROM medication GROUP BY drug
        ORDER BY count DESC LIMIT 20
    """).fetchall()

    return {
        'top_diagnoses': [{'icd_code': r[0], 'long_title': r[1], 'count': r[2]} for r in top_dx],
        'top_labs': [{'label': r[0], 'count': r[1]} for r in top_labs],
        'top_medications': [{'drug': r[0], 'count': r[1]} for r in top_meds],
    }


def get_missingness():
    conn = _conn()
    completeness = []

    def _pct(total, non_null):
        return round(non_null / total * 100, 1) if total else 0

    # Labs valuenum
    lab_total = conn.execute("SELECT COUNT(*) FROM lab_event").fetchone()[0]
    lab_nn = conn.execute("SELECT COUNT(*) FROM lab_event WHERE valuenum IS NOT NULL").fetchone()[0]
    completeness.append({'data_type': 'Lab values (valuenum)', 'total': lab_total,
                         'non_null': lab_nn, 'pct': _pct(lab_total, lab_nn)})

    # Vitals valuenum
    vt = conn.execute("SELECT COUNT(*) FROM vital_sign").fetchone()[0]
    vnn = conn.execute("SELECT COUNT(*) FROM vital_sign WHERE valuenum IS NOT NULL").fetchone()[0]
    completeness.append({'data_type': 'Vital signs (valuenum)', 'total': vt,
                         'non_null': vnn, 'pct': _pct(vt, vnn)})

    # Encounters
    et = conn.execute("SELECT COUNT(*) FROM encounter").fetchone()[0]
    for col, lbl in [('dischtime', 'Encounter discharge time'),
                     ('deathtime', 'Encounter death time')]:
        nn = conn.execute(f"SELECT COUNT(*) FROM encounter WHERE {col} IS NOT NULL").fetchone()[0]
        completeness.append({'data_type': lbl, 'total': et, 'non_null': nn, 'pct': _pct(et, nn)})

    nn = conn.execute("SELECT COUNT(*) FROM encounter WHERE discharge_location != ''").fetchone()[0]
    completeness.append({'data_type': 'Encounter discharge location', 'total': et,
                         'non_null': nn, 'pct': _pct(et, nn)})

    # Notes text
    nt = conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]
    nnn = conn.execute("SELECT COUNT(*) FROM note WHERE text != ''").fetchone()[0]
    completeness.append({'data_type': 'Note text', 'total': nt,
                         'non_null': nnn, 'pct': _pct(nt, nnn)})

    # Medications
    mt = conn.execute("SELECT COUNT(*) FROM medication").fetchone()[0]
    for col, lbl in [('starttime', 'Medication start time'),
                     ('stoptime', 'Medication stop time')]:
        nn = conn.execute(f"SELECT COUNT(*) FROM medication WHERE {col} IS NOT NULL").fetchone()[0]
        completeness.append({'data_type': lbl, 'total': mt, 'non_null': nn, 'pct': _pct(mt, nn)})

    return {'completeness': completeness}


# ---------------------------------------------------------------------------
# Research queries
# ---------------------------------------------------------------------------

def get_patients_for_criterion(criterion):
    """Return set of patient IDs matching a single criterion."""
    conn = _conn()
    ctype = criterion.get('type')

    if ctype == 'diagnosis':
        code = criterion.get('icd_code', '').strip().upper()
        conditions = []
        params = []
        if code:
            conditions.append("icd_code LIKE ?")
            params.append(f"{code}%")
        version = criterion.get('icd_version')
        if version is not None:
            conditions.append("icd_version = ?")
            params.append(version)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(f"SELECT DISTINCT patient_id FROM diagnosis {where}", params).fetchall()
        return {r[0] for r in rows}

    elif ctype == 'lab':
        conditions = []
        params = []
        label = criterion.get('label', '')
        if label:
            conditions.append("l.label ILIKE ?")
            params.append(f"%{label}%")
        op = criterion.get('operator')
        val = criterion.get('value')
        if op and val is not None:
            op_map = {'>': '>', '>=': '>=', '<': '<', '<=': '<=', '=': '=', '!=': '!='}
            sql_op = op_map.get(op, '=')
            conditions.append(f"l.valuenum {sql_op} ?")
            params.append(float(val))
        temporal = criterion.get('temporal', {})
        within_hours = temporal.get('within_hours')
        join_enc = ""
        if within_hours:
            conditions.append("l.encounter_id IS NOT NULL")
            join_enc = "JOIN encounter enc ON l.encounter_id = enc.id"
            conditions.append(f"l.charttime <= enc.admittime + INTERVAL '{int(within_hours)} hours'")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT DISTINCT l.patient_id FROM lab_event l {join_enc} {where}", params
        ).fetchall()
        return {r[0] for r in rows}

    elif ctype == 'vital':
        conditions = []
        params = []
        label = criterion.get('label', '')
        if label:
            conditions.append("v.label ILIKE ?")
            params.append(f"%{label}%")
        op = criterion.get('operator')
        val = criterion.get('value')
        if op and val is not None:
            op_map = {'>': '>', '>=': '>=', '<': '<', '<=': '<=', '=': '=', '!=': '!='}
            sql_op = op_map.get(op, '=')
            conditions.append(f"v.valuenum {sql_op} ?")
            params.append(float(val))
        temporal = criterion.get('temporal', {})
        within_hours = temporal.get('within_hours')
        join_enc = ""
        if within_hours:
            conditions.append("v.encounter_id IS NOT NULL")
            join_enc = "JOIN encounter enc ON v.encounter_id = enc.id"
            conditions.append(f"v.charttime <= enc.admittime + INTERVAL '{int(within_hours)} hours'")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(
            f"SELECT DISTINCT v.patient_id FROM vital_sign v {join_enc} {where}", params
        ).fetchall()
        return {r[0] for r in rows}

    elif ctype == 'medication':
        drug = criterion.get('drug', '')
        conditions = []
        params = []
        if drug:
            conditions.append("drug ILIKE ?")
            params.append(f"%{drug}%")
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = conn.execute(f"SELECT DISTINCT patient_id FROM medication {where}", params).fetchall()
        return {r[0] for r in rows}

    elif ctype == 'age':
        op = criterion.get('operator', '>=')
        val = criterion.get('value', 0)
        op_map = {'>': '>', '>=': '>=', '<': '<', '<=': '<=', '=': '=', '!=': '!='}
        sql_op = op_map.get(op, '>=')
        rows = conn.execute(f"SELECT id FROM patient WHERE anchor_age {sql_op} ?", [int(val)]).fetchall()
        return {r[0] for r in rows}

    elif ctype == 'gender':
        val = criterion.get('value', '')
        rows = conn.execute("SELECT id FROM patient WHERE gender = ?", [val]).fetchall()
        return {r[0] for r in rows}

    return set()


def execute_criteria(criteria_json):
    """Execute criteria and return list of {patient_id, encounter_id, group_label} dicts."""
    conn = _conn()
    inclusion = criteria_json.get('inclusion', [])
    exclusion = criteria_json.get('exclusion', [])
    group_by = criteria_json.get('group_by')

    if not inclusion:
        rows = conn.execute("SELECT id FROM patient").fetchall()
        patient_ids = {r[0] for r in rows}
    else:
        patient_ids = None
        for criterion in inclusion:
            matches = get_patients_for_criterion(criterion)
            if patient_ids is None:
                patient_ids = matches
            else:
                patient_ids &= matches
        if patient_ids is None:
            patient_ids = set()

    for criterion in exclusion:
        excluded = get_patients_for_criterion(criterion)
        patient_ids -= excluded

    if not patient_ids:
        return []

    id_list = ', '.join(str(i) for i in patient_ids)
    encounters = conn.execute(f"""
        SELECT e.patient_id, e.id, p.anchor_age
        FROM encounter e
        JOIN patient p ON e.patient_id = p.id
        WHERE e.patient_id IN ({id_list})
    """).fetchall()

    results = []
    for patient_id, encounter_id, anchor_age in encounters:
        group_label = ''
        if group_by:
            gb_type = group_by.get('type')
            threshold = group_by.get('threshold')
            labels = group_by.get('labels', ['A', 'B'])
            if gb_type == 'age' and threshold is not None:
                group_label = labels[0] if anchor_age < threshold else labels[1]
        results.append({
            'patient_id': patient_id,
            'encounter_id': encounter_id,
            'group_label': group_label,
        })

    return results


def get_cohort_patient_data(patient_ids, encounter_ids=None):
    """Get patient data for cohort stats (from DuckDB patient IDs)."""
    conn = _conn()
    if not patient_ids:
        return {'patients': [], 'encounters': []}

    id_list = ', '.join(str(i) for i in patient_ids)
    patients = conn.execute(f"""
        SELECT id, subject_id, gender, anchor_age FROM patient WHERE id IN ({id_list})
    """).fetchall()

    encounters = []
    if encounter_ids:
        eid_list = ', '.join(str(i) for i in encounter_ids)
        encounters = conn.execute(f"""
            SELECT id, hadm_id, admittime, dischtime, admission_type,
                   hospital_expire_flag
            FROM encounter WHERE id IN ({eid_list})
        """).fetchall()

    return {'patients': patients, 'encounters': encounters}


def get_export_data(patient_pks, data_types):
    """Export data for given patient PKs (DuckDB internal IDs)."""
    conn = _conn()
    if not patient_pks:
        return {}

    id_list = ', '.join(str(i) for i in patient_pks)
    export = {}

    if 'demographics' in data_types:
        rows = conn.execute(f"""
            SELECT subject_id, gender, anchor_age, anchor_year, anchor_year_group,
                   CAST(dod AS VARCHAR) FROM patient WHERE id IN ({id_list})
        """).fetchall()
        export['demographics'] = [
            {'subject_id': r[0], 'gender': r[1], 'anchor_age': r[2],
             'anchor_year': r[3], 'anchor_year_group': r[4], 'dod': r[5]}
            for r in rows
        ]

    if 'encounters' in data_types:
        rows = conn.execute(f"""
            SELECT e.hadm_id, p.subject_id, e.admittime, e.dischtime,
                   e.admission_type, e.admission_location, e.discharge_location,
                   e.insurance, e.race, e.hospital_expire_flag
            FROM encounter e JOIN patient p ON e.patient_id = p.id
            WHERE e.patient_id IN ({id_list})
        """).fetchall()
        export['encounters'] = [
            {'hadm_id': r[0], 'patient__subject_id': r[1],
             'admittime': _ts(r[2]), 'dischtime': _ts(r[3]),
             'admission_type': r[4], 'admission_location': r[5],
             'discharge_location': r[6], 'insurance': r[7],
             'race': r[8], 'hospital_expire_flag': bool(r[9])}
            for r in rows
        ]

    if 'labs' in data_types:
        rows = conn.execute(f"""
            SELECT p.subject_id, enc.hadm_id, l.label, l.charttime,
                   l.value, l.valuenum, l.valueuom, l.flag
            FROM lab_event l
            JOIN patient p ON l.patient_id = p.id
            LEFT JOIN encounter enc ON l.encounter_id = enc.id
            WHERE l.patient_id IN ({id_list})
            LIMIT 10000
        """).fetchall()
        export['labs'] = [
            {'patient__subject_id': r[0], 'encounter__hadm_id': r[1],
             'label': r[2], 'charttime': _ts(r[3]), 'value': r[4],
             'valuenum': r[5], 'valueuom': r[6], 'flag': r[7]}
            for r in rows
        ]

    if 'vitals' in data_types:
        rows = conn.execute(f"""
            SELECT p.subject_id, enc.hadm_id, v.label, v.charttime,
                   v.valuenum, v.valueuom
            FROM vital_sign v
            JOIN patient p ON v.patient_id = p.id
            LEFT JOIN encounter enc ON v.encounter_id = enc.id
            WHERE v.patient_id IN ({id_list})
            LIMIT 10000
        """).fetchall()
        export['vitals'] = [
            {'patient__subject_id': r[0], 'encounter__hadm_id': r[1],
             'label': r[2], 'charttime': _ts(r[3]),
             'valuenum': r[4], 'valueuom': r[5]}
            for r in rows
        ]

    if 'diagnoses' in data_types:
        rows = conn.execute(f"""
            SELECT p.subject_id, enc.hadm_id, d.icd_code, d.icd_version,
                   d.long_title, d.seq_num
            FROM diagnosis d
            JOIN patient p ON d.patient_id = p.id
            JOIN encounter enc ON d.encounter_id = enc.id
            WHERE d.patient_id IN ({id_list})
        """).fetchall()
        export['diagnoses'] = [
            {'patient__subject_id': r[0], 'encounter__hadm_id': r[1],
             'icd_code': r[2], 'icd_version': r[3],
             'long_title': r[4], 'seq_num': r[5]}
            for r in rows
        ]

    if 'medications' in data_types:
        rows = conn.execute(f"""
            SELECT p.subject_id, enc.hadm_id, m.drug, m.starttime,
                   m.stoptime, m.route, m.dose_val_rx, m.dose_unit_rx
            FROM medication m
            JOIN patient p ON m.patient_id = p.id
            JOIN encounter enc ON m.encounter_id = enc.id
            WHERE m.patient_id IN ({id_list})
        """).fetchall()
        export['medications'] = [
            {'patient__subject_id': r[0], 'encounter__hadm_id': r[1],
             'drug': r[2], 'starttime': _ts(r[3]), 'stoptime': _ts(r[4]),
             'route': r[5], 'dose_val_rx': r[6], 'dose_unit_rx': r[7]}
            for r in rows
        ]

    if 'notes' in data_types:
        rows = conn.execute(f"""
            SELECT p.subject_id, enc.hadm_id, n.note_type, n.charttime, n.text
            FROM note n
            JOIN patient p ON n.patient_id = p.id
            LEFT JOIN encounter enc ON n.encounter_id = enc.id
            WHERE n.patient_id IN ({id_list})
            LIMIT 5000
        """).fetchall()
        export['notes'] = [
            {'patient__subject_id': r[0], 'encounter__hadm_id': r[1],
             'note_type': r[2], 'charttime': _ts(r[3]), 'text': r[4]}
            for r in rows
        ]

    return export


def get_patient_ids_for_subject_ids(subject_ids):
    """Resolve subject_ids to DuckDB internal patient IDs."""
    conn = _conn()
    if not subject_ids:
        return []
    placeholders = ', '.join(['?'] * len(subject_ids))
    rows = conn.execute(
        f"SELECT id FROM patient WHERE subject_id IN ({placeholders})",
        list(subject_ids)
    ).fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# FHIR queries
# ---------------------------------------------------------------------------

class DuckRow:
    """Lightweight wrapper giving attribute access to dict/tuple data for FHIR transformers."""
    def __init__(self, data):
        if isinstance(data, dict):
            self.__dict__.update(data)
        else:
            self.__dict__.update(data)

    def __getattr__(self, name):
        return None


def _patient_row_to_obj(row):
    """Convert patient tuple to DuckRow."""
    return DuckRow({
        'id': row[0], 'pk': row[0], 'subject_id': row[1], 'gender': row[2],
        'anchor_age': row[3], 'anchor_year': row[4],
        'anchor_year_group': row[5], 'dod': row[6],
    })


def _encounter_row_to_obj(row):
    """Convert encounter tuple (with patient subject_id) to DuckRow."""
    patient = DuckRow({'subject_id': row[3]})
    return DuckRow({
        'id': row[0], 'pk': row[0], 'hadm_id': row[1], 'patient_id': row[2],
        'patient': patient,
        'admittime': row[4], 'dischtime': row[5], 'deathtime': row[6],
        'admission_type': row[7], 'admission_location': row[8],
        'discharge_location': row[9], 'hospital_expire_flag': bool(row[10]),
    })


def get_fhir_patient(subject_id):
    conn = _conn()
    row = conn.execute("""
        SELECT id, subject_id, gender, anchor_age, anchor_year,
               anchor_year_group, dod
        FROM patient WHERE subject_id = ?
    """, [subject_id]).fetchone()
    return _patient_row_to_obj(row) if row else None


def get_fhir_patients(gender=None, subject_id=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if subject_id:
        conditions.append("subject_id = ?")
        params.append(subject_id)
    if gender:
        conditions.append("gender = ?")
        params.append(gender)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"SELECT COUNT(*) FROM patient {where}", params).fetchone()[0]
    rows = conn.execute(f"""
        SELECT id, subject_id, gender, anchor_age, anchor_year,
               anchor_year_group, dod
        FROM patient {where} ORDER BY subject_id
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_patient_row_to_obj(r) for r in rows]


def get_fhir_encounter(hadm_id):
    conn = _conn()
    row = conn.execute("""
        SELECT e.id, e.hadm_id, e.patient_id, p.subject_id,
               e.admittime, e.dischtime, e.deathtime, e.admission_type,
               e.admission_location, e.discharge_location, e.hospital_expire_flag
        FROM encounter e JOIN patient p ON e.patient_id = p.id
        WHERE e.hadm_id = ?
    """, [hadm_id]).fetchone()
    return _encounter_row_to_obj(row) if row else None


def get_fhir_encounters(patient_subject_id=None, date_filter=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if date_filter:
        if date_filter.startswith('ge'):
            conditions.append("e.admittime >= ?")
            params.append(date_filter[2:])
        elif date_filter.startswith('le'):
            conditions.append("e.admittime <= ?")
            params.append(date_filter[2:])
        else:
            conditions.append("CAST(e.admittime AS DATE) = ?")
            params.append(date_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM encounter e JOIN patient p ON e.patient_id = p.id {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        SELECT e.id, e.hadm_id, e.patient_id, p.subject_id,
               e.admittime, e.dischtime, e.deathtime, e.admission_type,
               e.admission_location, e.discharge_location, e.hospital_expire_flag
        FROM encounter e JOIN patient p ON e.patient_id = p.id
        {where}
        ORDER BY e.hadm_id
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_encounter_row_to_obj(r) for r in rows]


def _lab_row_to_obj(row):
    patient = DuckRow({'subject_id': row[15]})
    encounter = DuckRow({'hadm_id': row[16]}) if row[16] else None
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'labevent_id': row[3], 'itemid': row[4], 'label': row[5],
        'fluid': row[6], 'category': row[7], 'charttime': row[8],
        'value': row[9], 'valuenum': row[10], 'valueuom': row[11],
        'ref_range_lower': row[12], 'ref_range_upper': row[13], 'flag': row[14],
    })


def _vital_row_to_obj(row):
    patient = DuckRow({'subject_id': row[10]})
    encounter = DuckRow({'hadm_id': row[11]}) if row[11] else None
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'stay_id': row[3], 'charttime': row[4], 'itemid': row[5],
        'label': row[6], 'value': row[7], 'valuenum': row[8], 'valueuom': row[9],
    })


def _dx_row_to_obj(row):
    patient = DuckRow({'subject_id': row[7]})
    encounter = DuckRow({'hadm_id': row[8]})
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'seq_num': row[3], 'icd_code': row[4], 'icd_version': row[5],
        'long_title': row[6],
    })


def _proc_row_to_obj(row):
    patient = DuckRow({'subject_id': row[7]})
    encounter = DuckRow({'hadm_id': row[8]})
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'seq_num': row[3], 'icd_code': row[4], 'icd_version': row[5],
        'long_title': row[6],
    })


def _med_row_to_obj(row):
    patient = DuckRow({'subject_id': row[11]})
    encounter = DuckRow({'hadm_id': row[12]})
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'drug': row[3], 'ndc': row[4], 'dose_val_rx': row[5],
        'dose_unit_rx': row[6], 'route': row[7],
        'starttime': row[8], 'stoptime': row[9], 'drug_type': row[10],
    })


def _note_row_to_obj(row):
    patient = DuckRow({'subject_id': row[7]})
    encounter = DuckRow({'hadm_id': row[8]}) if row[8] else None
    return DuckRow({
        'id': row[0], 'pk': row[0], 'patient_id': row[1], 'encounter_id': row[2],
        'patient': patient, 'encounter': encounter,
        'note_id': row[3], 'note_type': row[4], 'charttime': row[5], 'text': row[6],
    })


_FHIR_LAB_SQL = """
    SELECT l.id, l.patient_id, l.encounter_id, l.labevent_id, l.itemid,
           l.label, l.fluid, l.category, l.charttime, l.value, l.valuenum,
           l.valueuom, l.ref_range_lower, l.ref_range_upper, l.flag,
           p.subject_id, enc.hadm_id
    FROM lab_event l
    JOIN patient p ON l.patient_id = p.id
    LEFT JOIN encounter enc ON l.encounter_id = enc.id
"""

_FHIR_VITAL_SQL = """
    SELECT v.id, v.patient_id, v.encounter_id, v.stay_id, v.charttime,
           v.itemid, v.label, v.value, v.valuenum, v.valueuom,
           p.subject_id, enc.hadm_id
    FROM vital_sign v
    JOIN patient p ON v.patient_id = p.id
    LEFT JOIN encounter enc ON v.encounter_id = enc.id
"""

_FHIR_DX_SQL = """
    SELECT d.id, d.patient_id, d.encounter_id, d.seq_num, d.icd_code,
           d.icd_version, d.long_title, p.subject_id, enc.hadm_id
    FROM diagnosis d
    JOIN patient p ON d.patient_id = p.id
    JOIN encounter enc ON d.encounter_id = enc.id
"""

_FHIR_PROC_SQL = """
    SELECT pr.id, pr.patient_id, pr.encounter_id, pr.seq_num, pr.icd_code,
           pr.icd_version, pr.long_title, p.subject_id, enc.hadm_id
    FROM procedure pr
    JOIN patient p ON pr.patient_id = p.id
    JOIN encounter enc ON pr.encounter_id = enc.id
"""

_FHIR_MED_SQL = """
    SELECT m.id, m.patient_id, m.encounter_id, m.drug, m.ndc,
           m.dose_val_rx, m.dose_unit_rx, m.route,
           m.starttime, m.stoptime, m.drug_type,
           p.subject_id, enc.hadm_id
    FROM medication m
    JOIN patient p ON m.patient_id = p.id
    JOIN encounter enc ON m.encounter_id = enc.id
"""

_FHIR_NOTE_SQL = """
    SELECT n.id, n.patient_id, n.encounter_id, n.note_id, n.note_type,
           n.charttime, n.text, p.subject_id, enc.hadm_id
    FROM note n
    JOIN patient p ON n.patient_id = p.id
    LEFT JOIN encounter enc ON n.encounter_id = enc.id
"""


def get_fhir_lab(labevent_id):
    conn = _conn()
    row = conn.execute(f"{_FHIR_LAB_SQL} WHERE l.labevent_id = ?", [labevent_id]).fetchone()
    return _lab_row_to_obj(row) if row else None


def get_fhir_vital(vital_pk):
    conn = _conn()
    row = conn.execute(f"{_FHIR_VITAL_SQL} WHERE v.id = ?", [vital_pk]).fetchone()
    return _vital_row_to_obj(row) if row else None


def get_fhir_labs(patient_subject_id=None, encounter_hadm_id=None,
                  code=None, date_filter=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    if code:
        conditions.append("l.label ILIKE ?")
        params.append(f"%{code}%")
    if date_filter:
        if date_filter.startswith('ge'):
            conditions.append("l.charttime >= ?")
            params.append(date_filter[2:])
        elif date_filter.startswith('le'):
            conditions.append("l.charttime <= ?")
            params.append(date_filter[2:])
        else:
            conditions.append("CAST(l.charttime AS DATE) = ?")
            params.append(date_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM lab_event l
        JOIN patient p ON l.patient_id = p.id
        LEFT JOIN encounter enc ON l.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_LAB_SQL} {where} ORDER BY l.charttime
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_lab_row_to_obj(r) for r in rows]


def get_fhir_vitals(patient_subject_id=None, encounter_hadm_id=None,
                    code=None, date_filter=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    if code:
        conditions.append("v.label ILIKE ?")
        params.append(f"%{code}%")
    if date_filter:
        if date_filter.startswith('ge'):
            conditions.append("v.charttime >= ?")
            params.append(date_filter[2:])
        elif date_filter.startswith('le'):
            conditions.append("v.charttime <= ?")
            params.append(date_filter[2:])
        else:
            conditions.append("CAST(v.charttime AS DATE) = ?")
            params.append(date_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM vital_sign v
        JOIN patient p ON v.patient_id = p.id
        LEFT JOIN encounter enc ON v.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_VITAL_SQL} {where} ORDER BY v.charttime
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_vital_row_to_obj(r) for r in rows]


def get_fhir_condition(hadm_id, seq_num):
    conn = _conn()
    row = conn.execute(
        f"{_FHIR_DX_SQL} WHERE enc.hadm_id = ? AND d.seq_num = ?",
        [hadm_id, seq_num]
    ).fetchone()
    return _dx_row_to_obj(row) if row else None


def get_fhir_conditions(patient_subject_id=None, encounter_hadm_id=None,
                        code=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    if code:
        conditions.append("d.icd_code = ?")
        params.append(code)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM diagnosis d
        JOIN patient p ON d.patient_id = p.id
        JOIN encounter enc ON d.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_DX_SQL} {where} ORDER BY enc.hadm_id, d.seq_num
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_dx_row_to_obj(r) for r in rows]


def get_fhir_procedure(hadm_id, seq_num):
    conn = _conn()
    row = conn.execute(
        f"{_FHIR_PROC_SQL} WHERE enc.hadm_id = ? AND pr.seq_num = ?",
        [hadm_id, seq_num]
    ).fetchone()
    return _proc_row_to_obj(row) if row else None


def get_fhir_procedures(patient_subject_id=None, encounter_hadm_id=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM procedure pr
        JOIN patient p ON pr.patient_id = p.id
        JOIN encounter enc ON pr.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_PROC_SQL} {where} ORDER BY enc.hadm_id, pr.seq_num
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_proc_row_to_obj(r) for r in rows]


def get_fhir_medication(med_pk):
    conn = _conn()
    row = conn.execute(f"{_FHIR_MED_SQL} WHERE m.id = ?", [med_pk]).fetchone()
    return _med_row_to_obj(row) if row else None


def get_fhir_medications(patient_subject_id=None, encounter_hadm_id=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM medication m
        JOIN patient p ON m.patient_id = p.id
        JOIN encounter enc ON m.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_MED_SQL} {where} ORDER BY m.id
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_med_row_to_obj(r) for r in rows]


def get_fhir_note(note_id):
    conn = _conn()
    row = conn.execute(f"{_FHIR_NOTE_SQL} WHERE n.note_id = ?", [note_id]).fetchone()
    return _note_row_to_obj(row) if row else None


def get_fhir_notes(patient_subject_id=None, encounter_hadm_id=None,
                   note_type=None, page=1):
    conn = _conn()
    conditions = []
    params = []
    if patient_subject_id:
        conditions.append("p.subject_id = ?")
        params.append(patient_subject_id)
    if encounter_hadm_id:
        conditions.append("enc.hadm_id = ?")
        params.append(encounter_hadm_id)
    if note_type:
        conditions.append("LOWER(n.note_type) = LOWER(?)")
        params.append(note_type)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * PAGE_SIZE

    total = conn.execute(f"""
        SELECT COUNT(*) FROM note n
        JOIN patient p ON n.patient_id = p.id
        LEFT JOIN encounter enc ON n.encounter_id = enc.id
        {where}
    """, params).fetchone()[0]

    rows = conn.execute(f"""
        {_FHIR_NOTE_SQL} {where} ORDER BY n.id
        LIMIT ? OFFSET ?
    """, params + [PAGE_SIZE, offset]).fetchall()

    return total, [_note_row_to_obj(r) for r in rows]


def get_fhir_patient_everything(subject_id):
    """Get all resources for a patient ($everything)."""
    conn = _conn()
    p_row = conn.execute("""
        SELECT id, subject_id, gender, anchor_age, anchor_year,
               anchor_year_group, dod
        FROM patient WHERE subject_id = ?
    """, [subject_id]).fetchone()
    if not p_row:
        return None

    pid = p_row[0]
    patient = _patient_row_to_obj(p_row)

    encounters = conn.execute(f"""
        SELECT e.id, e.hadm_id, e.patient_id, p.subject_id,
               e.admittime, e.dischtime, e.deathtime, e.admission_type,
               e.admission_location, e.discharge_location, e.hospital_expire_flag
        FROM encounter e JOIN patient p ON e.patient_id = p.id
        WHERE e.patient_id = ?
    """, [pid]).fetchall()

    labs = conn.execute(
        f"{_FHIR_LAB_SQL} WHERE l.patient_id = ? LIMIT 500", [pid]
    ).fetchall()

    vitals = conn.execute(
        f"{_FHIR_VITAL_SQL} WHERE v.patient_id = ? LIMIT 500", [pid]
    ).fetchall()

    diagnoses = conn.execute(
        f"{_FHIR_DX_SQL} WHERE d.patient_id = ?", [pid]
    ).fetchall()

    procedures = conn.execute(
        f"{_FHIR_PROC_SQL} WHERE pr.patient_id = ?", [pid]
    ).fetchall()

    meds = conn.execute(
        f"{_FHIR_MED_SQL} WHERE m.patient_id = ?", [pid]
    ).fetchall()

    notes = conn.execute(
        f"{_FHIR_NOTE_SQL} WHERE n.patient_id = ?", [pid]
    ).fetchall()

    return {
        'patient': patient,
        'encounters': [_encounter_row_to_obj(r) for r in encounters],
        'labs': [_lab_row_to_obj(r) for r in labs],
        'vitals': [_vital_row_to_obj(r) for r in vitals],
        'diagnoses': [_dx_row_to_obj(r) for r in diagnoses],
        'procedures': [_proc_row_to_obj(r) for r in procedures],
        'medications': [_med_row_to_obj(r) for r in meds],
        'notes': [_note_row_to_obj(r) for r in notes],
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_table_counts():
    """Return dict of table_name -> row_count."""
    conn = _conn()
    counts = {}
    for table in ['patient', 'encounter', 'icu_stay', 'transfer', 'lab_event',
                  'vital_sign', 'diagnosis', 'procedure', 'medication',
                  'medication_administration', 'note']:
        try:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            counts[table] = 0
    return counts


def reset_all_tables():
    """Drop and recreate all clinical tables."""
    from core.duckdb_schema import drop_all_tables, ensure_schema
    conn = _conn()
    drop_all_tables(conn)
    ensure_schema(conn)


def _ts(val):
    """Format a timestamp value for JSON output."""
    if val is None:
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)
