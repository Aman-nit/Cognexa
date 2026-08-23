import streamlit as st

from sql_query import generate_sql_and_execute
from classifier import classify_query
from retrieval import retrieve_documents
from rag_sql import generate_investigation_report

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


# Page setup
st.set_page_config(
    page_title="Cognexa Insurance Assistant",
    page_icon="🛡️",
    layout="centered"
)


# Custom UI
st.markdown(
    """
    <style>

    .stApp {
        background-color: #0e1117;
        color: #f5f5f5;
    }

    .main-title {
        text-align: center;
        font-size: 38px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #9aa4b2;
        font-size: 16px;
        margin-bottom: 35px;
    }

    .answer-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        line-height: 1.7;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 45px;
        font-size: 16px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# Header
st.markdown(
    '<div class="main-title">🛡️ Cognexa</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI-Powered Insurance Claims Assistant</div>',
    unsafe_allow_html=True
)


# Load LLM
model = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=512,
    timeout=120
)


# Answer prompt
ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an insurance claims assistant.

USER QUESTION:
{query}

EXACT DATA RETURNED FOR THIS QUESTION:
{context}

Your job is to explain the provided information to the user.

STRICT RULES:

1. Use ONLY the provided information.
2. Never invent values.
3. Never change values.
4. Never estimate values.
5. Never assume missing information.
6. Never generate SQL.
7. Never mention SQL.
8. Never mention database systems.
9. Never mention RAG, Pinecone, retrieval, chunks, context, or internal processing.
10. Start with a short meaningful heading.
11. Understand the user's question first.
12. Answer exactly what the user asked.
13. If multiple records are provided, use a clean Markdown table.
14. Preserve ALL columns from the provided data.
15. Use readable column names.
16. Display NULL values as "Not available".
17. Do not remove columns.
18. Do not change numeric values.
19. If aggregate values are provided, clearly explain them.
20. Do not calculate statistics from partial data.
21. If information is insufficient, say so.
22. Keep the answer concise.
23. Do not discuss unrelated topics.

For multiple records:

### Claims Overview

| Claim ID | Claim Amount | Policy State |
|---:|---:|---|
| 1 | 71610 | OH |
| 2 | 34650 | IL |

### Summary

The query returned the matching claims shown above.

For aggregate results:

### Claims Summary

| Policy State | Claim Count |
|---|---:|
| OH | 352 |
| IL | 338 |
| IN | 310 |

### Summary

Explain the result using only the provided values.

Now answer the user's question.
"""
)

answer_chain = (
    ANSWER_PROMPT
    | model
    | StrOutputParser()
)


# Query input
query = st.text_input(
    "Ask your question",
    placeholder=(
        "e.g. Show claims above 10000 "
        "with policy state and incident severity"
    )
)


# Ask button
if st.button("🔍 Ask Cognexa"):

    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()


    # Classify question
    with st.spinner("Understanding your question..."):

        try:
            label = classify_query(query)

        except Exception as e:

            st.error("Unable to classify the query.")
            st.caption(str(e))
            st.stop()


    # Show query type
    type_name = {
        "rag_query": "📚 Policy / Document Query",
        "sql_query": "🗄️ Database Query",
        "rag_sql_query": "🔎 Investigation Query"
    }

    st.caption(
        type_name.get(label, label)
    )


    # Handle RAG query
    if label == "rag_query":

        with st.spinner(
            "Searching policy information..."
        ):

            try:

                context = retrieve_documents(query)

            except Exception as e:

                st.error(
                    "Unable to retrieve information."
                )

                st.caption(str(e))
                st.stop()


        if not context:

            st.warning(
                "No relevant information was found."
            )

            st.stop()


        # Generate RAG answer
        with st.spinner(
            "Generating answer..."
        ):

            try:

                answer = answer_chain.invoke({
                    "context": context,
                    "query": query
                })

            except Exception as e:

                st.error(
                    "Unable to generate the answer."
                )

                st.caption(str(e))
                st.stop()


        st.markdown("### 💡 Answer")

        st.markdown(answer)


    # Handle SQL query
    elif label == "sql_query":

        with st.spinner(
            "Querying claims database..."
        ):

            try:

                response = generate_sql_and_execute(
                    query
                )

            except Exception as e:

                st.error(
                    "Unable to process the database query."
                )

                st.caption(str(e))
                st.stop()


        sql = response["sql"]
        result = response["results"]


        # Show generated SQL
        with st.expander(
            "🧾 Generated SQL"
        ):

            st.code(
                sql,
                language="sql"
            )


        # Check result
        if result.empty:

            st.info(
                "No matching records were found."
            )

            st.stop()


        # Show database result
        st.markdown(
            "### 📊 Query Results"
        )

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )


        # Convert data for LLM
        database_context = result.to_json(
            orient="records"
        )


        # Generate answer
        with st.spinner(
            "Preparing answer..."
        ):

            try:

                answer = answer_chain.invoke({
                    "context": database_context,
                    "query": query
                })

            except Exception as e:

                st.error(
                    "Unable to generate the answer."
                )

                st.caption(str(e))
                st.stop()


        # Show final answer
        st.markdown(
            "### 💡 Answer"
        )

        st.markdown(
            '<div class="answer-box">'
            + answer +
            '</div>',
            unsafe_allow_html=True
        )


     # Handle RAG plus SQL query
    elif label == "rag_sql_query":

        with st.spinner(
            "Investigating claim and policy information..."
        ):
            try:
                response = generate_investigation_report(query)

            except Exception as e:
                st.error(
                    "Unable to generate investigation report."
                )
                st.caption(str(e))
                st.stop()

        # Show investigation report
        st.markdown("### 🔎 Investigation Report")

        st.markdown(
            '<div class="answer-box">'
            + response["report"]
            + '</div>',
            unsafe_allow_html=True
        )

        # Show generated SQL
        with st.expander("🧾 View Generated SQL"):

            st.code(
                response["sql"],
                language="sql"
            )

        # Show database results
        with st.expander("📊 View Claim Data"):

            sql_result = response.get("sql_result")

            if sql_result is None:

                st.info(
                    "No database data available."
                )

            elif sql_result.empty:

                st.info(
                    "No matching claim records found."
                )

            else:

                st.dataframe(
                    sql_result,
                    use_container_width=True,
                    hide_index=True
                )

        # Show retrieved chunks
        with st.expander(
            "📚 View Retrieved Policy Information"
        ):

            chunks = response.get(
                "retrieved_chunks",
                []
            )

            # Handle a single string
            if isinstance(chunks, str):
                chunks = [chunks]

            if not chunks:

                st.info(
                    "No policy information was retrieved."
                )

            else:

                st.caption(
                    f"{len(chunks)} relevant chunks retrieved."
                )

                for i, chunk in enumerate(
                    chunks,
                    start=1
                ):

                    st.markdown(
                        f"#### 📄 Retrieved Chunk {i}"
                    )

                    if hasattr(
                        chunk,
                        "page_content"
                    ):

                        st.markdown(
                            chunk.page_content
                        )

                        if getattr(
                            chunk,
                            "metadata",
                            None
                        ):

                            with st.expander(
                                f"Metadata - Chunk {i}"
                            ):

                                st.json(
                                    chunk.metadata
                                )

                    else:

                        st.markdown(
                            str(chunk)
                        )

                    st.divider()