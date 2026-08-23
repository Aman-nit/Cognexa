from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from sql_query import generate_sql_and_execute
from retrieval import retrieve_documents


model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=1200,
    timeout=120
)


INVESTIGATION_PROMPT = ChatPromptTemplate.from_template("""
You are an insurance claims investigation assistant.

USER QUESTION:
{question}

STRUCTURED CLAIM DATA:
{sql_data}

RELEVANT POLICY AND SOP INFORMATION:
{document_context}

Analyze both sources and prepare a clear investigation report.

Rules:

1. Use only the information provided.
2. Never invent facts.
3. Never guess missing values.
4. Never change database values.
5. If information is missing, say "Information not available."
6. Do not mention SQL.
7. Do not mention database systems.
8. Do not mention RAG.
9. Do not mention chunks.
10. Do not mention retrieval.
11. Do not mention embeddings.
12. Clearly separate facts from conclusions.
13. Do not automatically call a claim fraudulent.
14. fraud_reported is only an indicator from the provided data.
15. Use the policy and SOP information when making findings.
16. Do not make a final legal decision.
17. If evidence is insufficient, clearly say so.
18. Keep the report professional and concise.

Use this structure:

### 🔎 Investigation Report

**Claim / Policy Information**

Present the important claim information.

### 📋 Relevant Policy / Rules

Summarize the relevant policy or SOP information.

### 🔍 Findings

Compare the claim information with the relevant rules.

### ⚠️ Risk / Concern

Mention supported concerns, inconsistencies, missing information,
or suspicious indicators.

If no concern is supported, say:

"No specific concern was identified from the available information."

### ✅ Conclusion

Give a short conclusion based only on the provided information.

If insufficient:

"The available information is insufficient to reach a definitive conclusion."

USER QUESTION:
{question}

Generate the investigation report.
""")


investigation_chain = (
    INVESTIGATION_PROMPT
    | model
    | StrOutputParser()
)


def dataframe_to_context(dataframe):
    if dataframe.empty:
        return "No claim records were found."

    return dataframe.to_string(index=False)


def normalize_chunks(retrieved):
    if retrieved is None:
        return []

    if isinstance(retrieved, list):
        return retrieved

    if isinstance(retrieved, tuple):
        return list(retrieved)

    if isinstance(retrieved, str):
        return [retrieved]

    return [str(retrieved)]


def generate_investigation_report(question):

    # Get claim data
    sql_response = generate_sql_and_execute(question)

    sql = sql_response["sql"]
    sql_result = sql_response["results"]

    sql_data = dataframe_to_context(sql_result)

    # Get policy documents
    retrieved = retrieve_documents(question)

    retrieved_chunks = normalize_chunks(retrieved)

    if not retrieved_chunks:
        document_context = "No relevant policy or SOP information was found."
    else:
        document_context = "\n\n".join(
            str(chunk)
            for chunk in retrieved_chunks
        )

    # Generate report
    report = investigation_chain.invoke({
        "question": question,
        "sql_data": sql_data,
        "document_context": document_context
    })

    return {
        "report": report,
        "sql": sql,
        "sql_result": sql_result,
        "retrieved_chunks": retrieved_chunks
    }


if __name__ == "__main__":

    question = input(
        "Ask investigation question: "
    )

    try:

        response = generate_investigation_report(
            question
        )

        print("\n")
        print("=" * 60)
        print("INVESTIGATION REPORT")
        print("=" * 60)
        print(response["report"])

        print("\n")
        print("=" * 60)
        print("GENERATED SQL")
        print("=" * 60)
        print(response["sql"])

        print("\n")
        print("=" * 60)
        print("RETRIEVED CHUNKS")
        print("=" * 60)

        for i, chunk in enumerate(
            response["retrieved_chunks"],
            1
        ):
            print(f"\n--- Chunk {i} ---")
            print(chunk)

    except Exception as e:

        print(
            "\nUnable to generate investigation report."
        )

        print(
            f"Error: {e}"
        )