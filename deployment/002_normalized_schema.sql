CREATE SCHEMA IF NOT EXISTS clinical;

-- ============================================================
-- Patients
-- ============================================================

CREATE TABLE IF NOT EXISTS clinical.patients (
    patient_id BIGSERIAL PRIMARY KEY,
    subject_id TEXT NOT NULL UNIQUE,

    gender TEXT,
    anchor_age INTEGER,
    race TEXT,
    marital_status TEXT,
    insurance TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- Admissions
-- ============================================================

CREATE TABLE IF NOT EXISTS clinical.admissions (
    admission_id BIGSERIAL PRIMARY KEY,
    hadm_id TEXT NOT NULL UNIQUE,

    patient_id BIGINT NOT NULL
        REFERENCES clinical.patients(patient_id),

    admission_type TEXT,
    admission_location TEXT,
    discharge_location TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- Clinical events
-- ============================================================

CREATE TABLE IF NOT EXISTS clinical.clinical_events (
    event_id BIGSERIAL PRIMARY KEY,

    patient_id BIGINT NOT NULL
        REFERENCES clinical.patients(patient_id),

    admission_id BIGINT
        REFERENCES clinical.admissions(admission_id),

    event_type TEXT,

    order_type TEXT,
    order_subtype TEXT,
    transaction_type TEXT,

    drug TEXT,
    formulary_drug_cd TEXT,
    prod_strength TEXT,

    dose_val_rx TEXT,
    dose_unit_rx TEXT,
    form_unit_disp TEXT,
    route TEXT,

    careunit TEXT,

    spec_type_desc TEXT,
    test_name TEXT,
    org_name TEXT,
    ab_name TEXT,

    comments TEXT,

    drg_type TEXT,
    description TEXT,
    drg_severity TEXT,
    drg_mortality TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_patients_subject_id
    ON clinical.patients(subject_id);

CREATE INDEX IF NOT EXISTS idx_admissions_patient_id
    ON clinical.admissions(patient_id);

CREATE INDEX IF NOT EXISTS idx_admissions_hadm_id
    ON clinical.admissions(hadm_id);

CREATE INDEX IF NOT EXISTS idx_events_patient_id
    ON clinical.clinical_events(patient_id);

CREATE INDEX IF NOT EXISTS idx_events_admission_id
    ON clinical.clinical_events(admission_id);

CREATE INDEX IF NOT EXISTS idx_events_order_type
    ON clinical.clinical_events(order_type);

CREATE INDEX IF NOT EXISTS idx_events_event_type
    ON clinical.clinical_events(event_type);
