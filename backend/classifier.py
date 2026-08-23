from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

# Load model
model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=512,
    timeout=30
)

# Classifier prompt
CLASSIFIER_PROMPT = ChatPromptTemplate.from_template("""
You are a query router for an insurance claims chatbot.

Classify the user's question into exactly ONE of these three labels:

- sql_query: questions asking for counts, sums, averages, filters, or lookups over structured claim data

- rag_query: questions about policy documents, SOPs, rules, definitions, or general "how does X work" questions

- rag_sql_query: questions that reference a SPECIFIC claim/policy ID AND ask for judgment/explanation combining data + rules

Respond with ONLY the label.

Examples:

Q: How many claims have claim amount greater than 100000?
A: sql_query

Q: What is our policy on pre-existing condition exclusions?
A: rag_query

Q: For claim ID CLM4521, is this a fraud case and why?
A: rag_sql_query

Q: List all claims filed in the last 30 days.
A: sql_query

Q: What documents are required to file a claim?
A: rag_query

Q: Should we flag claim CLM9981 for investigation based on its details?
A: rag_sql_query

Now classify this:

Q: {query}

A:
""")

classifier_chain = CLASSIFIER_PROMPT | model | StrOutputParser()

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

    label = raw.strip().lower().split()[0] if raw.strip() else ""

    label = label.strip(".,:;\"'")

    final = label if label in VALID_LABELS else "rag_query"

    return final