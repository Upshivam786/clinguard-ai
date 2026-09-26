CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.mimic_transcript_raw (
    subject_id TEXT,
    hadm_id TEXT,
    admission_type TEXT,
    admission_location TEXT,
    discharge_location TEXT,
    insurance TEXT,
    marital_status TEXT,
    race TEXT,
    gender TEXT,
    anchor_age TEXT,

    drug TEXT,
    formulary_drug_cd TEXT,
    prod_strength TEXT,
    dose_val_rx TEXT,
    dose_unit_rx TEXT,
    form_unit_disp TEXT,
    route TEXT,

    eventtype TEXT,
    careunit TEXT,

    order_type TEXT,
    order_subtype TEXT,
    transaction_type TEXT,

    spec_type_desc TEXT,
    test_name TEXT,
    org_name TEXT,
    ab_name TEXT,
    comments TEXT,

    drg_type TEXT,
    description TEXT,
    drg_severity TEXT,
    drg_mortality TEXT
);
