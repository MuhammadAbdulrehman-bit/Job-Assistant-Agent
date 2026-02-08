import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
# SWITCH TO LOCAL EMBEDDINGS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

# IMPORT TOOLS
from agent_tools import create_word_document, get_search_tool, get_todays_date

load_dotenv()

def get_agent():
    print("🧠 Initializing the Office Agent (Hybrid Mode)...")

    # 1. BRAIN: Use Google Flash (Cloud)
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    # 2. MEMORY: Use HuggingFace (Local)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # --- PATH FIX: Ensure we look in the EXACT same folder as ingest.py ---
    # Go up one level from 'src' to find the root, then 'chroma_db'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "chroma_db")
    
    vector_db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    retriever = vector_db.as_retriever(search_kwargs={"k": 10})
    
    def fetch_internal_docs(query: str):
        docs = retriever.invoke(query)
        return "\n\n".join([d.page_content for d in docs])

    # --- CRITICAL FIX: RENAME THE TOOL ---
    # Old Name: "lookup_internship_policy" (Too narrow!)
    # New Name: "internal_knowledge_base" (Broad!)
    knowledge_base_tool = Tool(
        name="internal_knowledge_base",
        func=fetch_internal_docs,
        description="Searches through ALL uploaded internal documents, including reports, policies, project details, and memos. USE THIS FIRST for any question about company files."
    )

    search_tool = get_search_tool()
    tools = [knowledge_base_tool, search_tool, create_word_document, get_todays_date]

    # --- PROMPT UPDATE ---
    system_instructions = (
        "You are the Executive Assistant for Supervisor Mark in the AI Department. "
        "You have access to tools to answer questions or create documents."
        "\n\n"
        "### DECISION PROTOCOL:"
        "\n1. **SIMPLE QUESTIONS:** If the user asks for information (e.g., 'What is Biryani?', 'What is the wifi password?'), just answer directly. **DO NOT** use a formal signature."
        "\n2. **DOCUMENT CREATION:** If the user explicitly asks you to 'Write a letter', 'Draft a memo', or 'Create a document':"
        "\n   - Generate the body text."
        "\n   - **DO NOT** write the Date (the tool does it)."
        "\n   - **DO** include the signature: 'Sincerely, Mark, AI Department'."
        "\n   - Pass the text to the 'create_word_document' tool."
        "\n\n"
        "### TOOLS:"
        "\n- **internal_knowledge_base**: Use this for ANY question about files, reports, policies, or specific company info."
        "\n- **web_search**: Use this ONLY for general world knowledge (like news, recipes, public facts)."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor

if __name__ == "__main__":
    agent_executor = get_agent()
    
    # Test Query
    query = "What is the Future Intellica report about?"
    agent_executor.invoke({"input": query})