"""Generate and execute read-only DuckDB SQL queries."""

import os
import re
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openrouter import ChatOpenRouter
from langchain_ollama import ChatOllama



# Load environment variables.
load_dotenv()


# Find the database file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "insurance.duckdb"


# Create the LLM.
# model = ChatOpenRouter(
#     model="z-ai/glm-5.2:free",
#     openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
#     temperature=0,
# )


model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=512,
    timeout=120
)



# Define the database schema.
SCHEMA = """
TABLE insured
- insured_id
- age
- gender
- occupation
- insured_zip
- hobbies
- relationship
- education_level
- capital_gains
- capital_loss
- monthly_income

TABLE policy
- policy_number
- insured_id
- months_as_customer
- policy_bind_date
- policy_state
- policy_csl
- policy_deductible
- policy_annual_premium
- umbrella_limit
- auto_year

TABLE vehicle
- vehicle_id
- policy_number
- auto_make
- auto_model
- auto_year

TABLE incident
- incident_id
- policy_number
- incident_date
- incident_type
- collision_type
- incident_severity
- authorities_contacted
- incident_state
- incident_city
- incident_location
- incident_hour_of_day
- vehicles_involved
- property_damage
- bodily_injuries
- witnesses
- police_report_available

TABLE claim
- claim_id
- incident_id
- total_claim_amount
- injury_claim
- property_claim
- vehicle_claim
- fraud_reported


RELATIONSHIPS

insured.insured_id = policy.insured_id
policy.policy_number = vehicle.policy_number
policy.policy_number = incident.policy_number
incident.incident_id = claim.incident_id


VALID JOIN PATHS

claim -> incident -> policy -> insured
claim -> incident -> policy -> vehicle

Never join claim directly to vehicle.
"""


# Create the SQL generation prompt.
SQL_PROMPT = ChatPromptTemplate.from_template(
    """
You are a DuckDB SQL generator.

Convert the user's question into exactly ONE read-only SELECT query.

SCHEMA:
{schema}

ALIASES:
insured AS ins
policy AS p
vehicle AS v
incident AS i
claim AS c

RULES:

1. Return SQL only.
2. Return exactly one SELECT statement.
3. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE,
   COPY, EXPORT, ATTACH, DETACH, INSTALL, LOAD, CALL or PRAGMA.
4. Use only the tables and columns in the schema.
5. Never invent tables or columns.
6. Always use the correct aliases.
7. Always qualify columns with aliases.
8. Use explicit JOIN ... ON conditions.
9. Never join claim directly to vehicle.
10. Use only required joins.
11. Normal record queries must use LIMIT 100.
12. Aggregate queries do not need LIMIT.
13. "how many" means COUNT(*).
14. "total" means SUM().
15. "average" means AVG().
16. "highest" means MAX().
17. "lowest" means MIN().
18. "top N" means ORDER BY value DESC LIMIT N.
19. "bottom N" means ORDER BY value ASC LIMIT N.
20. Use WHERE for normal filters.
21. Use HAVING only for aggregate filters.
22. Do not use aggregate functions inside WHERE.
23. For claims above an amount use c.total_claim_amount directly.
24. For claims below an amount use c.total_claim_amount directly.
25. GROUP BY must contain every selected non-aggregate column.
26. Do not use aggregate functions when individual records are requested.
27. Do not return comments or explanations.

COMMON MEANINGS:

"fraudulent claims" -> c.fraud_reported = 'Y'

"fraud was reported" -> c.fraud_reported = 'Y'

"claims above 50000" -> c.total_claim_amount > 50000

"claims below 20000" -> c.total_claim_amount < 20000

"highest claim" -> ORDER BY c.total_claim_amount DESC LIMIT 1

"lowest claim" -> ORDER BY c.total_claim_amount ASC LIMIT 1

"highest capital gain" -> ORDER BY ins.capital_gains DESC

"average premium" -> AVG(p.policy_annual_premium)

"claims by severity" -> GROUP BY i.incident_severity


EXAMPLES:

Question:
Show all claims where fraud was reported

SQL:
SELECT
    c.claim_id,
    c.incident_id,
    c.total_claim_amount,
    c.fraud_reported
FROM claim AS c
WHERE c.fraud_reported = 'Y'
LIMIT 100


Question:
Find the total claim amount per incident

SQL:
SELECT
    c.incident_id,
    SUM(c.total_claim_amount) AS total_claim
FROM claim AS c
GROUP BY c.incident_id


Question:
List vehicles involved in fraudulent claims

SQL:
SELECT
    v.vehicle_id,
    v.auto_make,
    v.auto_model,
    c.claim_id
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
JOIN policy AS p
    ON i.policy_number = p.policy_number
JOIN vehicle AS v
    ON p.policy_number = v.policy_number
WHERE c.fraud_reported = 'Y'
LIMIT 100


Question:
Find average annual premium by state

SQL:
SELECT
    p.policy_state,
    AVG(p.policy_annual_premium) AS avg_premium
FROM policy AS p
GROUP BY p.policy_state
ORDER BY avg_premium DESC


Question:
Show insured individuals with the highest capital gain

SQL:
SELECT
    ins.insured_id,
    ins.age,
    ins.occupation,
    ins.capital_gains
FROM insured AS ins
ORDER BY ins.capital_gains DESC
LIMIT 5


Question:
Count incidents by severity

SQL:
SELECT
    i.incident_severity,
    COUNT(*) AS total_incidents
FROM incident AS i
GROUP BY i.incident_severity
ORDER BY total_incidents DESC


Question:
Detect suspicious claims above 50000

SQL:
SELECT
    c.claim_id,
    c.incident_id,
    c.total_claim_amount
FROM claim AS c
WHERE c.total_claim_amount > 50000
LIMIT 100


Question:
Join insured with their policies

SQL:
SELECT
    ins.insured_id,
    ins.age,
    ins.gender,
    p.policy_number,
    p.policy_annual_premium
FROM insured AS ins
JOIN policy AS p
    ON ins.insured_id = p.insured_id
LIMIT 100


Question:
Find the maximum claim amount

SQL:
SELECT
    MAX(c.total_claim_amount) AS max_claim
FROM claim AS c


Question:
Find the minimum claim amount

SQL:
SELECT
    MIN(c.total_claim_amount) AS min_claim
FROM claim AS c


Question:
Show the claim with the highest amount

SQL:
SELECT
    c.claim_id,
    c.incident_id,
    c.total_claim_amount
FROM claim AS c
ORDER BY c.total_claim_amount DESC
LIMIT 1


Question:
Show the claim with the lowest amount

SQL:
SELECT
    c.claim_id,
    c.incident_id,
    c.total_claim_amount
FROM claim AS c
ORDER BY c.total_claim_amount ASC
LIMIT 1


Question:
Maximum annual premium by state

SQL:
SELECT
    p.policy_state,
    MAX(p.policy_annual_premium) AS highest_premium
FROM policy AS p
GROUP BY p.policy_state


Question:
Minimum annual premium by state

SQL:
SELECT
    p.policy_state,
    MIN(p.policy_annual_premium) AS lowest_premium
FROM policy AS p
GROUP BY p.policy_state


Question:
Find the newest and oldest vehicles

SQL:
SELECT
    MAX(v.auto_year) AS newest_vehicle,
    MIN(v.auto_year) AS oldest_vehicle
FROM vehicle AS v


Question:
Highest and lowest capital gain among insured

SQL:
SELECT
    MAX(ins.capital_gains) AS max_gain,
    MIN(ins.capital_gains) AS min_gain
FROM insured AS ins


Question:
How many fraudulent claims are there?

SQL:
SELECT
    COUNT(*) AS fraud_claim_count
FROM claim AS c
WHERE c.fraud_reported = 'Y'


Question:
What is the average claim amount by incident severity?

SQL:
SELECT
    i.incident_severity,
    AVG(c.total_claim_amount) AS average_claim_amount
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
GROUP BY i.incident_severity
ORDER BY average_claim_amount DESC


USER QUESTION:
{question}

RETURN ONLY THE SQL QUERY.
"""
)


# Create the SQL chain.
sql_chain = SQL_PROMPT | model | StrOutputParser()


# Extract the SQL from the model response.
def extract_sql(raw_sql: str) -> str:

    sql = raw_sql.strip()

    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = sql.replace("```", "").strip()

    match = re.search(
        r"\bSELECT\b",
        sql,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Model did not generate a SELECT query."
        )

    sql = sql[match.start():].strip()

    # Reject multiple statements.
    if ";" in sql:
        parts = [
            part.strip()
            for part in sql.split(";")
            if part.strip()
        ]

        if len(parts) > 1:
            raise ValueError(
                "Multiple SQL statements are not allowed."
            )

        sql = parts[0]

    return sql


# Check that the SQL is read-only.
def validate_sql(sql: str) -> str:

    sql = sql.strip()

    if not re.match(
        r"^SELECT\b",
        sql,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    forbidden = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|"
        r"TRUNCATE|COPY|EXPORT|ATTACH|DETACH|"
        r"INSTALL|LOAD|CALL|PRAGMA|VACUUM|"
        r"SET|RESET"
        r")\b",
        flags=re.IGNORECASE,
    )

    if forbidden.search(sql):
        raise ValueError(
            "Unsafe SQL operation detected."
        )

    return sql


# Generate a safe SQL query.
def generate_sql(question: str) -> str:

    raw_sql = sql_chain.invoke(
        {
            "schema": SCHEMA,
            "question": question,
        }
    )

    sql = extract_sql(raw_sql)

    return validate_sql(sql)


# Correct SQL when DuckDB reports an error.
def fix_sql(
    question: str,
    sql: str,
    error: Exception,
) -> str:

    prompt = ChatPromptTemplate.from_template(
        """
Fix the following DuckDB SQL query.

QUESTION:
{question}

SQL:
{sql}

ERROR:
{error}

SCHEMA:
{schema}

Return exactly one SELECT statement.

Rules:
- Use only valid tables and columns.
- Use aliases c, i, p, ins and v.
- Never join claim directly to vehicle.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
  TRUNCATE, COPY, EXPORT, ATTACH, DETACH, INSTALL,
  LOAD, CALL or PRAGMA.
- Return SQL only.

Correct query:
"""
    )

    chain = prompt | model | StrOutputParser()

    raw_sql = chain.invoke(
        {
            "question": question,
            "sql": sql,
            "error": str(error),
            "schema": SCHEMA,
        }
    )

    fixed_sql = extract_sql(raw_sql)

    return validate_sql(fixed_sql)


# Generate, validate and execute the query.
def generate_sql_and_execute(question: str):

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    sql = generate_sql(question)

    with duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    ) as connection:

        # Check the query before execution.
        try:
            connection.execute(
                "EXPLAIN " + sql
            )

        except Exception as error:

            sql = fix_sql(
                question,
                sql,
                error,
            )

            connection.execute(
                "EXPLAIN " + sql
            )

        # Execute the final query.
        results = connection.execute(
            sql
        ).fetchdf()

    return {
        "question": question,
        "sql": sql,
        "results": results,
    }


# Test the SQL pipeline.
if __name__ == "__main__":

    question = input(
        "Ask your question: "
    )

    try:

        response = generate_sql_and_execute(
            question
        )

        print("\nGenerated SQL:")
        print(response["sql"])

        print("\nQuery Results:")
        print(response["results"])

    except Exception as error:

        print("\nError:")
        print(error)