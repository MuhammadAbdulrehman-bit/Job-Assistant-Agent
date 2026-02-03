import streamlit as st
import os
import shutil
from rag_engine import get_agent
from ingest import ingest_documents

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Job Assistant Agent",
    page_icon="🤖",
    layout="wide"
)

# --- HEADER ---
st.title("🤖 Job Assistant Agent")
st.markdown("*Your AI-powered executive assistant for checking policies and drafting documents.*")

# --- SIDEBAR: KNOWLEDGE BASE ---
with st.sidebar:
    st.header("📂 Knowledge Base")
    st.write("Upload new policy documents here to update the agent's brain.")
    
    # File Uploader
    uploaded_files = st.file_uploader(
        "Upload PDF, Docx, or Txt", 
        accept_multiple_files=True, 
        type=["pdf"] # Currently backend only supports PDF
    )
    
    if uploaded_files:
        # Define path to data folder (go up one level from src)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        if st.button("💾 Save & Process Documents"):
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    # Save file to data/ directory
                    file_path = os.path.join(data_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                # Trigger the ingestion script
                # Note: Currently ingest.py is hardcoded to look for "Confidential.pdf"
                # We might need to update ingest.py later to scan the whole folder.
                try:
                    ingest_documents()
                    st.success("✅ Knowledge base updated successfully!")
                    # Clear agent cache so it picks up new data
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Error during ingestion: {e}")

    st.divider()
    st.info("ℹ️ **Note:** The agent uses Google Gemini Pro & ChromaDB.")

# --- CHAT INTERFACE ---

# 1. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am Mark's Executive Assistant. How can I help you with the internship policies or drafting memos today?"}
    ]

# 2. Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Handle User Input
if prompt := st.chat_input("Ask about the dress code, wifi, or ask me to write a memo..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Consulting the policies..."):
            try:
                # Initialize agent (Cached to prevent reloading on every input)
                @st.cache_resource
                def load_agent():
                    return get_agent()
                
                agent_executor = load_agent()
                
                # Invoke the agent
                response = agent_executor.invoke({"input": prompt})
                result = response["output"]
                
                st.markdown(result)
                
                # Append assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": result})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")