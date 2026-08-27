"""Cognexa main application for SQL, semantic, and hybrid search."""

import os

import streamlit as st

from dotenv import load_dotenv

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter

from classifier import classify_query
from sql_query import generate_sql_and_execute
from semantic_search import semantic_search


load_dotenv()


# Configure Streamlit page
st.set_page_config(
    page_title="Cognexa Insurance Assistant",
    page_icon="🛡️",
    layout="centered",
)


# Create LLM
model = ChatOpenRouter(
    model="openai/gpt-oss-20b",
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)

# model = ChatOllama(
#     model="phi3",
#     base_url="http://localhost:11434",
#     max_tokens=512,
#     timeout=120
# )



# Create final answer prompt
ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an insurance business assistant.

USER QUESTION:
{question}

DATABASE INFORMATION:
{sql_data}

BUSINESS RULES:
{semantic_data}

Answer the user's question using only the information provided.

Rules:
- Use database information when it is available.
- Use business rules when they are available.
- If both are available, combine them.
- Do not invent information.
- Do not change database values.
- Do not change business-rule values.
- Do not assume missing information.
- If the required information is not available, say so.
- Keep the answer clear and concise.
- ALWAYS cite specific rule IDs (e.g., BR007, BR008) if you use them.
- ALWAYS format currency amounts in INR (₹) and NEVER in Dollars ($).
"""
)


answer_chain = ANSWER_PROMPT | model | StrOutputParser()


# Display application
st.title("🛡️ Cognexa")
st.caption("AI-Powered Insurance Claims Assistant")


# Get user question
query = st.text_input(
    "Ask your question",
    placeholder="Example: What claims should be investigated?",
)


if st.button("🔍 Ask Cognexa"):

    # Check user question
    if not query.strip():
        st.warning("Please enter a question.")
        st.stop()

    question = query.strip()


    # Classify the question
    with st.spinner("Understanding your question..."):
        try:
            route = classify_query(question)

        except Exception as error:
            st.error("Unable to classify the question.")
            st.caption(str(error))
            st.stop()


    st.caption(f"Search type: {route}")


    # Prepare empty data
    sql_data = "No database information was retrieved."
    semantic_data = "No business knowledge was retrieved."

    sql = None
    sql_result = None
    passages = []


    # Run SQL search
    if route in {"sql_query", "hybrid_search"}:

        with st.spinner("Querying insurance database..."):
            try:
                response = generate_sql_and_execute(question)

                sql = response["sql"]
                sql_result = response["results"]

            except Exception as error:
                st.error("Unable to process the database query.")
                st.caption(str(error))
                st.stop()


        if sql_result.empty:
            sql_data = "No matching database records were found."

        else:
            limited_result = sql_result.head(15)
            sql_data = limited_result.to_json(
                orient="records"
            )
            if len(sql_result) > 15:
                sql_data += f"\n\n(Note: Showing 15 out of {len(sql_result)} records. The full list is displayed below.)"


    # Run semantic search
    if route in {"semantic_search", "hybrid_search"}:

        with st.spinner("Searching business rules..."):
            try:
                passages = semantic_search(
                    question,
                    top_k=5,
                )

            except Exception as error:
                st.error(
                    "Unable to search the semantic knowledge base."
                )
                st.caption(str(error))
                st.stop()


        if passages:
            semantic_data = "\n\n".join(passages)


    # Generate final answer
    with st.spinner("Preparing answer..."):

        try:
            answer = answer_chain.invoke(
                {
                    "question": question,
                    "sql_data": sql_data,
                    "semantic_data": semantic_data,
                }
            )

        except Exception as error:
            st.error("Unable to generate the answer.")
            st.caption(str(error))
            st.stop()


    # Show final answer
    st.markdown("### 💡 Answer")
    st.markdown(answer)


    # Show generated SQL
    if sql is not None:

        with st.expander("🧾 Generated SQL"):
            st.code(
                sql,
                language="sql",
            )


    # Show database results
    if sql_result is not None:

        with st.expander("📊 View Database Results"):

            if sql_result.empty:
                st.info("No matching records were found.")

            else:
                st.dataframe(
                    sql_result,
                    use_container_width=True,
                    hide_index=True,
                )


    # Show semantic results
    if passages:

        with st.expander("📚 View Retrieved Business Rules"):

            for index, passage in enumerate(
                passages,
                1,
            ):
                st.markdown(
                    f"**[{index}]** {passage}"
                )