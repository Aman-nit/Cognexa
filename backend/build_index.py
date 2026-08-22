"""Clean the insurance workbook and load its relational model into DuckDB.

Run from the repository root:
    python backend/build_index.py
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd


TABLE_CONFIG = {
    "insured": {
        "columns": [
            "insured_id", "insured_zip", "age", "gender", "education_level",
            "occupation", "hobbies", "relationship", "capital_gains", "capital_loss",
        ],
        "id": "insured_id",
        "integer_columns": ["insured_id", "age", "capital_gains", "capital_loss"],
        "string_columns": ["gender", "education_level", "occupation", "hobbies", "relationship"],
    },
    "policy": {
        "columns": [
            "policy_number", "insured_id", "months_as_customer", "policy_bind_date",
            "policy_state", "policy_csl", "policy_deductible", "policy_annual_premium", "umbrella_limit",
        ],
        "id": "policy_number",
        "integer_columns": ["policy_number", "insured_id", "months_as_customer", "policy_deductible", "umbrella_limit"],
        "decimal_columns": ["policy_annual_premium"],
        "date_columns": ["policy_bind_date"],
        "string_columns": ["policy_state", "policy_csl"],
    },
    "vehicle": {
        "columns": ["vehicle_id", "policy_number", "auto_make", "auto_model", "auto_year"],
        "id": "vehicle_id",
        "integer_columns": ["vehicle_id", "policy_number", "auto_year"],
        "string_columns": ["auto_make", "auto_model"],
    },
    "incident": {
        "columns": [
            "incident_id", "policy_number", "incident_date", "incident_type", "collision_type",
            "incident_severity", "authorities_contacted", "incident_state", "incident_city",
            "incident_location", "incident_hour_of_day", "vehicles_involved", "property_damage",
            "bodily_injuries", "witnesses", "police_report_available",
        ],
        "id": "incident_id",
        "integer_columns": ["incident_id", "policy_number", "incident_hour_of_day", "vehicles_involved", "bodily_injuries", "witnesses"],
        "date_columns": ["incident_date"],
        "string_columns": [
            "incident_type", "collision_type", "incident_severity", "authorities_contacted",
            "incident_state", "incident_city", "incident_location",
        ],
        "yes_no_columns": ["property_damage", "police_report_available"],
    },
    "claim": {
        "columns": ["claim_id", "incident_id", "total_claim_amount", "injury_claim", "property_claim", "vehicle_claim", "fraud_reported"],
        "id": "claim_id",
        "integer_columns": ["claim_id", "incident_id", "total_claim_amount", "injury_claim", "property_claim", "vehicle_claim"],
        "yes_no_columns": ["fraud_reported"],
    },
}


def fail(message: str) -> None:
    raise ValueError(message)


def clean_table(name: str, frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    config = TABLE_CONFIG[name]
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    if list(frame.columns) != config["columns"]:
        fail(f"{name}: unexpected columns. Expected {config['columns']}; received {list(frame.columns)}")

    input_rows = len(frame)
    frame = frame.dropna(how="all").copy()
    blank_rows_removed = input_rows - len(frame)
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].map(lambda value: value.strip() if isinstance(value, str) else value)
        frame[column] = frame[column].replace({"": pd.NA, "?": pd.NA, "N/A": pd.NA, "NA": pd.NA})

    duplicate_rows_removed = int(frame.duplicated().sum())
    frame = frame.drop_duplicates().copy()

    for column in config.get("integer_columns", []):
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.isna().any() or (converted % 1 != 0).any():
            fail(f"{name}.{column}: contains missing or non-integer values")
        frame[column] = converted.astype("int64")

    for column in config.get("decimal_columns", []):
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.isna().any():
            fail(f"{name}.{column}: contains missing or invalid numeric values")
        frame[column] = converted.round(2)

    for column in config.get("date_columns", []):
        converted = pd.to_datetime(frame[column], errors="coerce")
        if converted.isna().any():
            fail(f"{name}.{column}: contains missing or invalid dates")
        frame[column] = converted.dt.date

    for column in config.get("string_columns", []):
        frame[column] = frame[column].astype("string")

    for column in config.get("yes_no_columns", []):
        frame[column] = frame[column].astype("string").str.upper()
        invalid = frame[column].dropna()[~frame[column].dropna().isin(["Y", "N", "YES", "NO"])]
        if not invalid.empty:
            fail(f"{name}.{column}: invalid yes/no values: {invalid.unique().tolist()}")
        frame[column] = frame[column].replace({"Y": "YES", "N": "NO"})

    if name == "insured":
        zip_values = pd.to_numeric(frame["insured_zip"], errors="coerce")
        if zip_values.isna().any() or (zip_values % 1 != 0).any():
            fail("insured.insured_zip: contains invalid postal codes")
        frame["insured_zip"] = zip_values.astype("int64").astype(str).str.zfill(6)

    identifier = config["id"]
    if frame[identifier].duplicated().any():
        fail(f"{name}.{identifier}: duplicate primary-key values found")
    if (frame[identifier] <= 0).any():
        fail(f"{name}.{identifier}: identifiers must be positive")

    # DuckDB receives ordinary Python strings; this also preserves SQL NULLs.
    for column in frame.columns:
        if pd.api.types.is_string_dtype(frame[column]):
            frame[column] = frame[column].astype(object).where(frame[column].notna(), None)

    return frame[config["columns"]], {
        "input_rows": input_rows,
        "blank_rows_removed": blank_rows_removed,
        "duplicate_rows_removed": duplicate_rows_removed,
        "clean_rows": len(frame),
        "null_counts": {column: int(count) for column, count in frame.isna().sum().items() if count},
    }


DDL = """
CREATE TABLE insured (
    insured_id BIGINT PRIMARY KEY,
    insured_zip VARCHAR NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR NOT NULL,
    education_level VARCHAR NOT NULL,
    occupation VARCHAR NOT NULL,
    hobbies VARCHAR NOT NULL,
    relationship VARCHAR NOT NULL,
    capital_gains BIGINT NOT NULL,
    capital_loss BIGINT NOT NULL
);
CREATE TABLE policy (
    policy_number BIGINT PRIMARY KEY,
    insured_id BIGINT NOT NULL REFERENCES insured(insured_id),
    months_as_customer INTEGER NOT NULL,
    policy_bind_date DATE NOT NULL,
    policy_state VARCHAR NOT NULL,
    policy_csl VARCHAR NOT NULL,
    policy_deductible BIGINT NOT NULL,
    policy_annual_premium DECIMAL(12,2) NOT NULL,
    umbrella_limit BIGINT NOT NULL
);
CREATE TABLE vehicle (
    vehicle_id BIGINT PRIMARY KEY,
    policy_number BIGINT NOT NULL REFERENCES policy(policy_number),
    auto_make VARCHAR NOT NULL,
    auto_model VARCHAR NOT NULL,
    auto_year INTEGER NOT NULL
);
CREATE TABLE incident (
    incident_id BIGINT PRIMARY KEY,
    policy_number BIGINT NOT NULL REFERENCES policy(policy_number),
    incident_date DATE NOT NULL,
    incident_type VARCHAR NOT NULL,
    collision_type VARCHAR,
    incident_severity VARCHAR NOT NULL,
    authorities_contacted VARCHAR,
    incident_state VARCHAR NOT NULL,
    incident_city VARCHAR NOT NULL,
    incident_location VARCHAR NOT NULL,
    incident_hour_of_day INTEGER NOT NULL CHECK (incident_hour_of_day BETWEEN 0 AND 23),
    vehicles_involved INTEGER NOT NULL CHECK (vehicles_involved >= 1),
    property_damage VARCHAR CHECK (property_damage IN ('YES', 'NO') OR property_damage IS NULL),
    bodily_injuries INTEGER NOT NULL CHECK (bodily_injuries >= 0),
    witnesses INTEGER NOT NULL CHECK (witnesses >= 0),
    police_report_available VARCHAR CHECK (police_report_available IN ('YES', 'NO') OR police_report_available IS NULL)
);
CREATE TABLE claim (
    claim_id BIGINT PRIMARY KEY,
    incident_id BIGINT NOT NULL REFERENCES incident(incident_id),
    total_claim_amount BIGINT NOT NULL CHECK (total_claim_amount >= 0),
    injury_claim BIGINT NOT NULL CHECK (injury_claim >= 0),
    property_claim BIGINT NOT NULL CHECK (property_claim >= 0),
    vehicle_claim BIGINT NOT NULL CHECK (vehicle_claim >= 0),
    fraud_reported VARCHAR NOT NULL CHECK (fraud_reported IN ('YES', 'NO')),
    CHECK (total_claim_amount = injury_claim + property_claim + vehicle_claim)
);
CREATE TABLE data_quality_audit (
    table_name VARCHAR PRIMARY KEY,
    input_rows INTEGER NOT NULL,
    blank_rows_removed INTEGER NOT NULL,
    duplicate_rows_removed INTEGER NOT NULL,
    clean_rows INTEGER NOT NULL,
    nullable_field_null_counts JSON NOT NULL,
    loaded_at_utc TIMESTAMP NOT NULL
);
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root / "data" / "1db65133-d9c2-4d71-9d4a-8963a16e255d.xlsx",
        help="Path to the source .xlsx workbook (default: repository data workbook)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "data",
        help="Directory for the database and cleaned CSV files (default: data/)",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    clean_dir = args.output_dir / "cleaned_csv"
    clean_dir.mkdir(exist_ok=True)

    excel = pd.ExcelFile(args.input)
    unexpected_sheets = set(excel.sheet_names) - set(TABLE_CONFIG)
    missing_sheets = set(TABLE_CONFIG) - set(excel.sheet_names)
    if unexpected_sheets or missing_sheets:
        fail(f"Workbook sheets do not match expected schema. Missing={sorted(missing_sheets)}, unexpected={sorted(unexpected_sheets)}")

    cleaned, audit = {}, {}
    for name in TABLE_CONFIG:
        cleaned[name], audit[name] = clean_table(name, pd.read_excel(args.input, sheet_name=name))

    relationships = [("policy", "insured_id", "insured", "insured_id"), ("vehicle", "policy_number", "policy", "policy_number"), ("incident", "policy_number", "policy", "policy_number"), ("claim", "incident_id", "incident", "incident_id")]
    for child, child_key, parent, parent_key in relationships:
        unmatched = sorted(set(cleaned[child][child_key]) - set(cleaned[parent][parent_key]))
        if unmatched:
            fail(f"Foreign-key violation: {child}.{child_key} has {len(unmatched)} unmatched values")

    claim = cleaned["claim"]
    if not (claim["total_claim_amount"] == claim["injury_claim"] + claim["property_claim"] + claim["vehicle_claim"]).all():
        fail("claim: total_claim_amount does not equal injury + property + vehicle claims")

    for name, frame in cleaned.items():
        frame.to_csv(clean_dir / f"{name}.csv", index=False)

    database_path = args.output_dir / "claimshield.duckdb"
    if database_path.exists():
        database_path.unlink()
    connection = duckdb.connect(str(database_path))
    try:
        connection.execute(DDL)
        for name, frame in cleaned.items():
            connection.register("load_frame", frame)
            connection.execute(f"INSERT INTO {name} SELECT * FROM load_frame")
            connection.unregister("load_frame")
        loaded_at = datetime.now(timezone.utc).replace(tzinfo=None)
        for name, result in audit.items():
            connection.execute(
                "INSERT INTO data_quality_audit VALUES (?, ?, ?, ?, ?, ?, ?)",
                [name, result["input_rows"], result["blank_rows_removed"], result["duplicate_rows_removed"], result["clean_rows"], json.dumps(result["null_counts"]), loaded_at],
            )
        verification = {}
        for name in TABLE_CONFIG:
            verification[name] = connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    manifest = {
        "source_workbook": str(args.input.resolve()),
        "database": str(database_path.resolve()),
        "table_row_counts": verification,
        "cleaning_audit": audit,
        "validated_relationships": ["policy.insured_id -> insured.insured_id", "vehicle.policy_number -> policy.policy_number", "incident.policy_number -> policy.policy_number", "claim.incident_id -> incident.incident_id"],
    }
    (args.output_dir / "load_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
