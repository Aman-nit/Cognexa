from dotenv import load_dotenv
import streamlit as st

from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_ollama import ChatOllama

load_dotenv()

st.title("Claim Policy Chatbot")
st.header("Ask any question related to claim policy and get instant answers!")

input_text = st.text_input("Enter your question here:")


# Primary Model: Ollama
ollama_llm = ChatOllama(
    model="phi3",
    base_url="http://localhost:11434",
    max_tokens=512,
    timeout=30,
)



# Fallback Model: Hugging Face
hf_llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen3.8-2.4T-A95B",
    task="text-generation",
    temperature=0.1,
    max_new_tokens=512,
   
)

hf_model = ChatHuggingFace(llm=hf_llm)



# Create fallback chain
model = ollama_llm.with_fallbacks([hf_model])



# Ask question
if st.button("Ask"):

    if input_text.strip():

        try:
            response = model.invoke(input_text)

            st.write(response.content)

        except Exception as e:
            st.error(f"Both models failed: {e}")

    else:
        st.warning("Please enter a question.")