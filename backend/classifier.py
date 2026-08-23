from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


# LLM
model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=100,
    timeout=120
)


# Classifier prompt
CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""

You are a query router for an insurance claims assistant.

Classify the user's question into EXACTLY ONE of these labels:

sql_query
rag_query
rag_sql_query


==================================================
IMPORTANT CLASSIFICATION RULE
==================================================

First ask:

Can this question be answered using ONLY the
structured insurance database?

If YES:
Return sql_query.

Do NOT classify a question as rag_sql_query just because
it contains words such as:

claim
policy
incident
fraud
insurance
policy state
insured
vehicle

If the required information exists in the database,
the answer is sql_query.

Use rag_sql_query ONLY when a specific record must be
evaluated using policy documents, SOPs, rules, or
guidelines.


==================================================
SQL_QUERY
==================================================

Use sql_query when the question can be answered using
structured data from the insurance database.

This includes:

- filtering
- sorting
- searching
- COUNT
- SUM
- AVG
- MIN
- MAX
- GROUP BY
- comparisons
- joins
- claim information
- policy information
- incident information
- insured information
- vehicle information


==================================================
SQL_QUERY EXAMPLES
==================================================

Q: Show all claims above 50000.
A: sql_query

Q: Show claims below 20000 with their claim amount and fraud reported status.
A: sql_query

Q: Show claims with major incident severity.
A: sql_query

Q: Show claims where fraud was reported as Y.
A: sql_query

Q: Show claims from Ohio policy state.
A: sql_query


Q: Show claims above 50000 with policy state and incident severity.
A: sql_query

Q: Show claim ID, claim amount, policy state, incident city, and incident severity.
A: sql_query

Q: Show all claims with their policy number and incident date.
A: sql_query

Q: Show claims along with vehicle make and model.
A: sql_query

Q: Show claims with insured person's age and occupation.
A: sql_query


Q: How many claims are there in total?
A: sql_query

Q: What is the total claim amount?
A: sql_query

Q: What is the average claim amount?
A: sql_query

Q: What is the highest claim amount?
A: sql_query

Q: What is the lowest claim amount?
A: sql_query


Q: How many claims are there in each policy state?
A: sql_query

Q: What is the total claim amount for each policy state?
A: sql_query

Q: What is the average claim amount for each policy state?
A: sql_query

Q: How many claims are there for each incident severity?
A: sql_query

Q: What is the total claim amount for each incident severity?
A: sql_query

Q: How many claims are reported as fraud for each policy state?
A: sql_query

Q: What is the average claim amount for each incident type?
A: sql_query


Q: Which policy state has the highest total claim amount?
A: sql_query

Q: Which incident severity has the highest average claim amount?
A: sql_query

Q: Show the top 10 claims by total claim amount.
A: sql_query

Q: Show the 10 claims with the highest vehicle claim amount.
A: sql_query

Q: How many claims are there for each combination of policy state and incident severity?
A: sql_query

Q: What is the average age of insured people who have claims?
A: sql_query

Q: Show claims where the insured person's monthly income is greater than 5000.
A: sql_query

Q: Show the total claim amount by policy state and incident severity.
A: sql_query


==================================================
RAG_QUERY
==================================================

Use rag_query when the question is about information
contained in insurance documents.

This includes:

- insurance policies
- SOPs
- rules
- procedures
- definitions
- coverage rules
- documentation requirements
- claim procedures
- fraud investigation guidelines


==================================================
RAG_QUERY EXAMPLES
==================================================

Q: What documents are required to file a claim?
A: rag_query

Q: What is the policy regarding pre-existing conditions?
A: rag_query

Q: What is the procedure for investigating a claim?
A: rag_query

Q: What does the fraud investigation policy say?
A: rag_query

Q: What are the rules for approving a claim?
A: rag_query

Q: What documents are needed for claim verification?
A: rag_query


==================================================
RAG_SQL_QUERY
==================================================

Use rag_sql_query ONLY when BOTH conditions are true:

1. The question refers to a SPECIFIC claim, policy,
   insured person, or incident.

AND

2. The question requires combining database information
   with policy documents, SOPs, rules, or guidelines.

If the question only asks for database information,
use sql_query.


==================================================
RAG_SQL_QUERY EXAMPLES
==================================================

Q: Is claim 4521 fraudulent according to our fraud policy?
A: rag_sql_query

Q: Should claim 9981 be flagged according to the fraud investigation rules?
A: rag_sql_query

Q: Based on the details of claim 4521, does it violate the insurance policy?
A: rag_sql_query

Q: For policy 12345, does the claim satisfy the coverage rules?
A: rag_sql_query

Q: Should claim 4521 be approved according to the claim approval SOP?
A: rag_sql_query


==================================================
IMPORTANT DIFFERENCES
==================================================

Q: Show claim 4521.
A: sql_query

Q: Show the amount of claim 4521.
A: sql_query

Q: Show claims where fraud was reported as Y.
A: sql_query

Q: How many claims are in Ohio?
A: sql_query

Q: What is the total claim amount by policy state?
A: sql_query

Q: Show claims above 50000 with policy information.
A: sql_query


BUT:


Q: Is claim 4521 fraudulent according to the fraud policy?
A: rag_sql_query

Q: Should claim 4521 be approved according to the SOP?
A: rag_sql_query

Q: Does claim 4521 violate the coverage rules?
A: rag_sql_query


==================================================
USER QUESTION
==================================================

{query}


==================================================
FINAL INSTRUCTION
==================================================

Return ONLY ONE label:

sql_query
rag_query
rag_sql_query

Do not explain your answer.
Do not return anything else.

""")


# Classifier chain
classifier_chain = (
    CLASSIFIER_PROMPT
    | model
    | StrOutputParser()
)


# Valid labels
VALID_LABELS = {
    "sql_query",
    "rag_query",
    "rag_sql_query"
}


# Classify query
def classify_query(user_query):

    raw = classifier_chain.invoke({
        "query": user_query
    })

    label = raw.strip().lower()

    # Check for valid label
    for valid_label in VALID_LABELS:
        if valid_label in label:
            return valid_label

    # Default label
    return "sql_query"


# Test
if __name__ == "__main__":

    while True:

        question = input("\nAsk your question: ")

        if question.lower() in {"exit", "quit"}:
            break

        try:

            result = classify_query(question)

            print("\nClassification:")
            print(result)

        except Exception as e:

            print("\nUnable to classify query.")
            print(f"Error: {e}")