import pandas as pd
import duckdb

excel_file = "cleaned_insurance_dataset.xlsx"
database_file = "insurance_project.duckdb"


tables = pd.read_excel(
    excel_file,
    sheet_name=["insured", "policy", "vehicle", "incident", "claim"]
)

con = duckdb.connect(database_file)


con.execute("""
CREATE OR REPLACE TABLE insured (
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
)
""")

con.execute("""
CREATE OR REPLACE TABLE policy (
    policy_number BIGINT PRIMARY KEY,
    insured_id BIGINT REFERENCES insured(insured_id),
    policy_bind_date DATE,
    policy_state VARCHAR,
    policy_csl VARCHAR,
    policy_deductable DOUBLE,
    policy_annual_premium DOUBLE,
    umbrella_limit DOUBLE,
    auto_year BIGINT
)
""")

con.execute("""
CREATE OR REPLACE TABLE vehicle (
    vehicle_id BIGINT PRIMARY KEY,
    policy_number BIGINT REFERENCES policy(policy_number),
    auto_make VARCHAR,
    auto_model VARCHAR,
    auto_year BIGINT
)
""")

con.execute("""
CREATE OR REPLACE TABLE incident (
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
)
""")

con.execute("""
CREATE OR REPLACE TABLE claim (
    claim_id BIGINT PRIMARY KEY,
    incident_id BIGINT REFERENCES incident(incident_id),
    total_claim_amount DOUBLE,
    injury_claim DOUBLE,
    property_claim DOUBLE,
    vehicle_claim DOUBLE,
    fraud_reported VARCHAR
)
""")


for table_name in ["insured", "policy", "vehicle", "incident", "claim"]:
    con.register("temp_data", tables[table_name])
    con.execute(f"INSERT INTO {table_name} SELECT * FROM temp_data")
    con.unregister("temp_data")


con.execute("""
CREATE OR REPLACE VIEW insurance_claim_analysis AS
SELECT
    i.insured_id,
    i.age,
    i.gender,
    p.policy_number,
    p.policy_state,
    inc.incident_id,
    inc.incident_type,
    inc.incident_severity,
    c.claim_id,
    c.total_claim_amount,
    c.injury_claim,
    c.property_claim,
    c.vehicle_claim,
    c.fraud_reported
FROM insured i
JOIN policy p ON i.insured_id = p.insured_id
JOIN incident inc ON p.policy_number = inc.policy_number
JOIN claim c ON inc.incident_id = c.incident_id
""")


print("DuckDB database created successfully!\n")
for table_name in ["insured", "policy", "vehicle", "incident", "claim"]:
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"{table_name}: {count} rows")

con.close()
