"""Classify insurance questions into SQL, semantic, or hybrid search."""
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv()


# Load local Phi-3.
# model = ChatOllama(
#     model="phi3",
#     temperature=0,
# )
model = ChatOpenRouter(
    model="openai/gpt-oss-20b",
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)


# Define the classifier prompt.
CLASSIFIER_PROMPT = ChatPromptTemplate.from_template(
    """
Classify the user question into exactly one label:

sql_query
semantic_search
hybrid_search

sql_query:
Use when the answer can be obtained from the DuckDB database.

Examples:
- Show claims above 50000
- What is the total claim amount?
- Find the highest capital gain
- Show fraudulent claims
- Which vehicle has the highest year?

semantic_search:
Use when the question only requires business rules,
policies, procedures, or definitions from the YAML knowledge base.

Examples:
- What claims require manual investigation?
- What is the high-value claim rule?
- What happens when a claim is filed within 30 days?
- What does BR006 mean?

hybrid_search:
Use when BOTH database information and YAML business rules
are required.

Examples:
- Should claim 5 be investigated according to the business rules?
- Does claim 5 trigger the high-value claim rule?
- Does claim 5 violate the investigation rules?

IMPORTANT:
Do not choose hybrid_search just because the question contains
words like claim, policy, fraud, insured, or vehicle.

Return ONLY one label.

USER QUESTION:
{query}
"""
)


# Create the classifier chain.
classifier_chain = CLASSIFIER_PROMPT | model | StrOutputParser()


# Allowed labels.
VALID_LABELS = {
    "sql_query",
    "semantic_search",
    "hybrid_search",
}


# Classify the user question.
def classify_query(user_query: str) -> str:
    response = classifier_chain.invoke(
        {"query": user_query}
    )

    label = response.strip().lower()

    for valid_label in VALID_LABELS:
        if valid_label in label:
            return valid_label

    raise ValueError(
        f"Invalid classifier response: {response}"
    )


# Test the classifier.
if __name__ == "__main__":
    while True:
        question = input("\nAsk your question: ")

        if question.lower() in {"exit", "quit"}:
            break

        try:
            print(classify_query(question))
        except Exception as error:
            print(f"Error: {error}")