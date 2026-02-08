import streamlit as st
import os
import ast
from rag_engine import get_agent
from ingest import ingest_documents

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Job Assistant Agent",
    page_icon="🤖",
    layout="wide"
)

# --- HELPER FUNCTION: CLEAN ROBOT OUTPUT ---
# --- HELPER FUNCTION: CLEAN ROBOT OUTPUT ---
def clean_response(text):
    """
    Robust cleaner that handles Gemini's mixed output format.
    It extracts text from both dictionaries and raw strings inside the list.
    """
    text = str(text).strip()
    
    # Check if it looks like the raw list format: "[{'type': 'text'..."
    if text.startswith("[") and ("'type': 'text'" in text or "extras" in text):
        try:
            # Safely parse the string as a Python list
            parsed_data = ast.literal_eval(text)
            clean_text = ""
            
            # Loop through ALL items in the list
            for item in parsed_data:
                # Case 1: It's a dictionary (Standard Gemini response)
                if isinstance(item, dict):
                    if 'text' in item:
                        clean_text += item['text']
                
                # Case 2: It's just a string (The part getting cut off!)
                elif isinstance(item, str):
                    clean_text += item
            
            return clean_text
        except:
            # If parsing fails, just return original to be safe
            return text
            
    # If it's normal text, return it as is
    return text
# --- HEADER ---
st.title("🤖 Job Assistant Agent")
st.markdown("*Your AI-powered executive assistant for checking policies and drafting documents.*")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am Mark's Executive Assistant. How can I help you today?"}
    ]
if "latest_file_path" not in st.session_state:
    st.session_state.latest_file_path = None

# --- SIDEBAR: KNOWLEDGE BASE ---
with st.sidebar:
    st.header("📂 Knowledge Base")
    st.write("Upload new policy documents here.")
    
    uploaded_files = st.file_uploader(
        "Upload PDF, Docx, or Txt", 
        accept_multiple_files=True, 
        type=["pdf"] 
    )
    
    if uploaded_files:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        if st.button("💾 Save & Process Documents"):
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(data_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                try:
                    ingest_documents()
                    st.success("✅ Knowledge base updated!")
                    st.cache_resource.clear()
                except Exception as e:
                    st.error(f"Error during ingestion: {e}")

    st.divider()
    
    # --- PERSISTENT DOWNLOAD BUTTON ---
    if st.session_state.latest_file_path and os.path.exists(st.session_state.latest_file_path):
        st.success("📄 Document Ready!")
        with open(st.session_state.latest_file_path, "rb") as file:
            st.download_button(
                label="📥 Download Generated Word Doc",
                data=file,
                file_name="Internship_Memo.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# --- CHAT INTERFACE ---

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Ask about the dress code, wifi, or ask me to write a memo..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Working on it..."):
            try:
                @st.cache_resource
                def load_agent():
                    return get_agent()
                
                agent_executor = load_agent()
                
                # Invoke agent
                response = agent_executor.invoke({"input": prompt})
                raw_result = response["output"]

                # --- APPLY THE CLEANER ---
                final_result = clean_response(raw_result)

                st.markdown(final_result)
                st.session_state.messages.append({"role": "assistant", "content": final_result})

                # CHECK IF FILE WAS CREATED
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                target_file = os.path.join(base_dir, "data", "agent_output_final.docx")
                
                if os.path.exists(target_file):
                    st.session_state.latest_file_path = target_file
                    st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {e}")