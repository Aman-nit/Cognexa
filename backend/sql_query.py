"""Generate and execute read-only DuckDB queries from natural-language questions."""

import re
from pathlib import Path

import duckdb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


# Database path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "insurance.duckdb"


# Initialize the language model used for SQL generation and correction.
model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=1000,
    timeout=120
)


# Schema and relationship context supplied to the language model.
SCHEMA = """
TABLE insured:
insured_id
age
gender
occupation
hobbies
relationship
education_level
capital_gains
capital_loss
monthly_income

TABLE policy:
policy_number
insured_id
policy_bind_date
policy_state
policy_csl
policy_deductable
policy_annual_premium
umbrella_limit
auto_year

TABLE vehicle:
vehicle_id
policy_number
auto_make
auto_model
auto_year

TABLE incident:
incident_id
policy_number
incident_date
incident_type
collision_type
incident_severity
authorities_contacted
incident_state
incident_city
incident_location
incident_hour_of_the_day
number_of_vehicles_involved
property_damage
bodily_injuries
witnesses
police_report_available

TABLE claim:
claim_id
incident_id
total_claim_amount
injury_claim
property_claim
vehicle_claim
fraud_reported

VALID RELATIONSHIPS:

claim.incident_id = incident.incident_id

incident.policy_number = policy.policy_number

policy.insured_id = insured.insured_id

policy.policy_number = vehicle.policy_number
"""


# Prompt used to convert a user question into one SELECT statement.
SQL_PROMPT = ChatPromptTemplate.from_template("""
You are a DuckDB SQL generator.

Convert the user's question into ONE valid SELECT query.

SCHEMA:

{schema}


ALIASES:

claim AS c
incident AS i
policy AS p
insured AS ins
vehicle AS v


VALID JOINS:

c.incident_id = i.incident_id

i.policy_number = p.policy_number

p.insured_id = ins.insured_id

p.policy_number = v.policy_number


IMPORTANT:

Never join claim directly to vehicle.

Correct path:

claim -> incident -> policy -> vehicle


STRICT RULES:

1. Return ONLY SQL.

2. The first word must be SELECT.

3. Generate exactly ONE SELECT statement.

4. Never generate INSERT.

5. Never generate UPDATE.

6. Never generate DELETE.

7. Never generate DROP.

8. Never generate ALTER.

9. Never generate CREATE.

10. Never generate TRUNCATE.

11. Never generate COPY.

12. Never generate EXPORT.

13. Never generate ATTACH.

14. Never generate DETACH.

15. Never generate INSTALL.

16. Never generate LOAD.

17. Never generate CALL.

18. Never generate PRAGMA.

19. Use ONLY tables from the schema.

20. Use ONLY columns from the schema.

21. Never invent columns.

22. Never invent tables.

23. Use only aliases c, i, p, ins and v.

24. Always qualify columns with aliases.

25. Only use JOINs required by the question.

26. Always use explicit JOIN conditions.

27. Do not create unnecessary CTEs.

28. Do not create unnecessary subqueries.

29. Do not use WITH unless absolutely necessary.

30. Normal record queries MUST use LIMIT 100.

31. COUNT, SUM, AVG, MIN and MAX queries do not require LIMIT.

32. If using GROUP BY, every selected non-aggregate column MUST appear in GROUP BY.

33. Never select claim_id in a GROUP BY query unless claim-level results are requested.

34. Never select total_claim_amount directly when calculating a count by category.

35. Never select unrelated columns in an aggregate query.

36. Never use aggregate functions in WHERE.

37. Use WHERE for filtering individual records.

38. Use HAVING only for filtering aggregated GROUP BY results.

39. Do NOT use SUM when the user asks to show individual claims above an amount.

40. Do NOT use AVG when the user asks to show individual claims above an amount.

41. Do NOT use COUNT when the user asks to show individual claims.

42. Do NOT use MIN or MAX when the user asks to show individual claims.

43. Do not generate comments.

44. Do not explain the query.

45. Do not use Markdown.

46. Do not use ```sql.

47. Do not apologize.

48. Do not say "Here is the query".

49. Never generate multiple SQL statements.


FILTERING RULES:

If the user says:

"claims above 50000"

use:

WHERE c.total_claim_amount > 50000


If the user says:

"claims below 20000"

use:

WHERE c.total_claim_amount < 20000


If the user says:

"claims above 50000"

DO NOT use:

SUM(c.total_claim_amount)

COUNT(*)

AVG(c.total_claim_amount)

MAX(c.total_claim_amount)


If the user asks for individual records, use the actual column
directly in WHERE.


AGGREGATE RULES:

"how many" means COUNT(*).

"total" means SUM().

"average" means AVG().

"highest" means MAX().

"lowest" means MIN().


EXAMPLE 1:

Question:

Show claims above 50000

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount
FROM claim AS c
WHERE c.total_claim_amount > 50000
LIMIT 100


EXAMPLE 2:

Question:

Show claims below 20000

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount
FROM claim AS c
WHERE c.total_claim_amount < 20000
LIMIT 100


EXAMPLE 3:

Question:

Show claims where fraud was reported as Y

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount,
    c.fraud_reported
FROM claim AS c
WHERE c.fraud_reported = 'Y'
LIMIT 100


EXAMPLE 4:

Question:

Show claims with major incident severity

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount,
    i.incident_severity
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
WHERE i.incident_severity = 'Major Damage'
LIMIT 100


EXAMPLE 5:

Question:

Show claims above 10000 with policy state and incident severity

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount,
    p.policy_state,
    i.incident_severity
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
JOIN policy AS p
    ON i.policy_number = p.policy_number
WHERE c.total_claim_amount > 10000
LIMIT 100


EXAMPLE 6:

Question:

How many claims are there?

Correct SQL:

SELECT
    COUNT(*) AS claim_count
FROM claim AS c


EXAMPLE 7:

Question:

What is the total claim amount?

Correct SQL:

SELECT
    SUM(c.total_claim_amount) AS total_claim_amount
FROM claim AS c


EXAMPLE 8:

Question:

What is the average claim amount?

Correct SQL:

SELECT
    AVG(c.total_claim_amount) AS average_claim_amount
FROM claim AS c


EXAMPLE 9:

Question:

How many claims are there in each policy state?

Correct SQL:

SELECT
    p.policy_state,
    COUNT(*) AS claim_count
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
JOIN policy AS p
    ON i.policy_number = p.policy_number
GROUP BY p.policy_state
ORDER BY claim_count DESC


EXAMPLE 10:

Question:

What is the total claim amount for each policy state?

Correct SQL:

SELECT
    p.policy_state,
    SUM(c.total_claim_amount) AS total_claim_amount
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
JOIN policy AS p
    ON i.policy_number = p.policy_number
GROUP BY p.policy_state
ORDER BY total_claim_amount DESC


EXAMPLE 11:

Question:

Show claims with vehicle make and model

Correct SQL:

SELECT
    c.claim_id,
    c.total_claim_amount,
    v.auto_make,
    v.auto_model
FROM claim AS c
JOIN incident AS i
    ON c.incident_id = i.incident_id
JOIN vehicle AS v
    ON i.policy_number = v.policy_number
LIMIT 100


USER QUESTION:

{question}

RETURN ONLY THE SQL QUERY.
""")


sql_chain = SQL_PROMPT | model | StrOutputParser()


# Remove response formatting and isolate the generated SQL statement.
def extract_sql(raw_sql):
    sql = raw_sql.strip()

    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace("```", "")

    match = re.search(
        r"\bSELECT\b",
        sql,
        flags=re.IGNORECASE
    )

    if not match:
        raise ValueError(
            "The model did not generate a SELECT query."
        )

    sql = sql[match.start():].strip()

    if ";" in sql:
        sql = sql.split(";")[0].strip()

    return sql


# Reject generated SQL that is not intended to be read-only.
def validate_sql(sql):
    sql = sql.strip()

    if not re.match(
        r"^SELECT\b",
        sql,
        flags=re.IGNORECASE
    ):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    forbidden = re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|"
        r"TRUNCATE|COPY|EXPORT|ATTACH|DETACH|"
        r"INSTALL|LOAD|CALL|PRAGMA"
        r")\b",
        flags=re.IGNORECASE
    )

    if forbidden.search(sql):
        raise ValueError(
            "Unsafe SQL operation detected."
        )

    bad_patterns = [
        r"\bI'm sorry\b",
        r"\bI am sorry\b",
        r"\bHere is\b",
        r"\bExplanation\b",
        r"\bSQL Query\b",
        r"\bAnswer:\b"
    ]

    for pattern in bad_patterns:
        if re.search(
            pattern,
            sql,
            flags=re.IGNORECASE
        ):
            raise ValueError(
                "The model generated invalid SQL."
            )

    return sql


# Generate, extract, and validate a query for the user's question.
def generate_sql(question):
    raw_sql = sql_chain.invoke({
        "schema": SCHEMA,
        "question": question
    })

    sql = extract_sql(raw_sql)

    sql = validate_sql(sql)

    return sql


# Ask the language model to correct a query rejected by DuckDB.
def fix_sql(question, sql, error):

    FIX_PROMPT = ChatPromptTemplate.from_template("""
You are a DuckDB SQL correction assistant.

Fix the invalid SQL query.

USER QUESTION:

{question}


INVALID SQL:

{sql}


DUCKDB ERROR:

{error}


SCHEMA:

{schema}


ALIASES:

claim AS c
incident AS i
policy AS p
insured AS ins
vehicle AS v


VALID JOINS:

c.incident_id = i.incident_id

i.policy_number = p.policy_number

p.insured_id = ins.insured_id

p.policy_number = v.policy_number


IMPORTANT:

The DuckDB error is authoritative.

If the error says:

WHERE clause cannot contain aggregates

then remove SUM, AVG, COUNT, MIN and MAX
from the WHERE clause.

For example:

WRONG:

WHERE SUM(c.total_claim_amount) > 50000

CORRECT:

WHERE c.total_claim_amount > 50000


If the user asks to SHOW claims,
return individual claim records.

If the user asks "claims above 50000",
use:

WHERE c.total_claim_amount > 50000

Do NOT use SUM.

Do NOT use COUNT.

Do NOT use AVG.

Do NOT use MAX.

Do NOT use MIN.


GROUP BY RULE:

Every selected non-aggregate column must appear
in GROUP BY.


STRICT RULES:

1. Return ONLY one SELECT query.

2. Do not explain anything.

3. Do not use Markdown.

4. Do not use ```sql.

5. Do not invent columns.

6. Do not invent tables.

7. Do not invent relationships.

8. Use only aliases c, i, p, ins and v.

9. Use valid DuckDB syntax.

10. Generate exactly one SELECT query.

11. Do not use INSERT.

12. Do not use UPDATE.

13. Do not use DELETE.

14. Do not use DROP.

15. Do not use ALTER.

16. Do not use CREATE.

RETURN ONLY THE CORRECTED SQL.
""")

    fix_chain = (
        FIX_PROMPT
        | model
        | StrOutputParser()
    )

    fixed_raw = fix_chain.invoke({
        "question": question,
        "sql": sql,
        "error": str(error),
        "schema": SCHEMA
    })

    fixed_sql = extract_sql(fixed_raw)

    fixed_sql = validate_sql(fixed_sql)

    return fixed_sql


# Generate a query, validate it with EXPLAIN, then execute it safely.
def generate_sql_and_execute(question):

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    sql = generate_sql(question)

    with duckdb.connect(
        str(DATABASE_PATH),
        read_only=True
    ) as connection:

        try:

            connection.execute(
                "EXPLAIN " + sql
            )

        except Exception as first_error:

            sql = fix_sql(
                question,
                sql,
                first_error
            )

            try:

                connection.execute(
                    "EXPLAIN " + sql
                )

            except Exception as second_error:

                raise ValueError(
                    "Unable to generate a valid SQL query: "
                    + str(second_error)
                )

        results = connection.execute(
            sql
        ).fetchdf()

    return {
        "question": question,
        "sql": sql,
        "results": results
    }


# Optional command-line entry point for manually testing the module.
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

    except Exception as e:

        print(
            "\nUnable to process the database query."
        )

        print(
            f"Error: {e}"
        )