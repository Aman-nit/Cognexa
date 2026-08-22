-- Insurance Project: DuckDB Relational Schema

CREATE TABLE insured (
    insured_id BIGINT PRIMARY KEY,
    age BIGINT,
    gender VARCHAR,
    occupation VARCHAR,
    hobbies VARCHAR,
    relationship VARCHAR,
    education_level VARCHAR,
    capital_gains DOUBLE,
    capital_loss DOUBLE,
    monthly_income DOUBLE
);

CREATE TABLE policy (
    policy_number BIGINT PRIMARY KEY,
    insured_id BIGINT REFERENCES insured(insured_id),
    policy_bind_date DATE,
    policy_state VARCHAR,
    policy_csl VARCHAR,
    policy_deductable DOUBLE,
    policy_annual_premium DOUBLE,
    umbrella_limit DOUBLE,
    auto_year BIGINT
);

CREATE TABLE vehicle (
    vehicle_id BIGINT PRIMARY KEY,
    policy_number BIGINT REFERENCES policy(policy_number),
    auto_make VARCHAR,
    auto_model VARCHAR,
    auto_year BIGINT
);

CREATE TABLE incident (
    incident_id BIGINT PRIMARY KEY,
    policy_number BIGINT REFERENCES policy(policy_number),
    incident_date DATE,
    incident_type VARCHAR,
    collision_type VARCHAR,
    incident_severity VARCHAR,
    authorities_contacted VARCHAR,
    incident_state VARCHAR,
    incident_city VARCHAR,
    incident_location VARCHAR,
    incident_hour_of_the_day BIGINT,
    number_of_vehicles_involved BIGINT,
    property_damage VARCHAR,
    bodily_injuries BIGINT,
    witnesses BIGINT,
    police_report_available VARCHAR
);

CREATE TABLE claim (
    claim_id BIGINT PRIMARY KEY,
    incident_id BIGINT REFERENCES incident(incident_id),
    total_claim_amount DOUBLE,
    injury_claim DOUBLE,
    property_claim DOUBLE,
    vehicle_claim DOUBLE,
    fraud_reported VARCHAR
);
