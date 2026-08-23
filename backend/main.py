import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from classifier import classify_query
from retrieval import retrieve_documents


# Load LLM
model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=512,
    timeout=30
)


# Create answer prompt
ANSWER_PROMPT = ChatPromptTemplate.from_template("""
You are an insurance claims assistant.

Answer the user's question using the provided context.

Rules:
- Give a clear and concise answer.
- Use only information available in the context.
- Do not mention the context, chunks, Pinecone, retrieval, or RAG.
- Do not copy the context word-for-word.
- If the context does not contain enough information, say that the available information is insufficient.
- Format the answer in a clean and easy-to-read way.

Context:
{context}

Question:
{query}

Answer:
""")


answer_chain = ANSWER_PROMPT | model | StrOutputParser()


# Streamlit UI
st.title("Cognexa Insurance Assistant")

query = st.text_input("Ask your question:")


if st.button("Ask") or query:

    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()

    # Classify query
    with st.spinner("Understanding your question..."):

        try:
            label = classify_query(query)

        except Exception as e:
            st.error("Unable to classify the query.")
            st.caption(f"Details: {e}")
            st.stop()

    # Handle RAG queries
    if label == "rag_query":

        with st.spinner("Searching relevant information..."):

            try:
                context = retrieve_documents(query)

            except Exception as e:
                st.error("Unable to retrieve information.")
                st.caption(f"Details: {e}")
                st.stop()

        if not context.strip():
            st.warning("I couldn't find relevant information for your question.")
            st.stop()

        # Generate final answer
        with st.spinner("Generating answer..."):

            try:
                answer = answer_chain.invoke({
                    "context": context,
                    "query": query
                })

            except Exception as e:
                st.error("Unable to generate the answer.")
                st.caption(f"Details: {e}")
                st.stop()

        # Show only final answer
        st.subheader("Answer")
        st.write(answer)

    elif label == "sql_query":

        st.info("This is a SQL query. SQL processing will be handled here.")

    elif label == "rag_sql_query":

        st.info("This query requires both SQL and document retrieval.")