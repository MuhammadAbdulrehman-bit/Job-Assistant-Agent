import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.chains.retrieval_qa.base import RetrievalQA 
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# IMPORT ALL TOOLS FROM ONE PLACE
from agent_tools import create_word_document, get_search_tool, create_policy_tool

load_dotenv()

def get_agent():
    print("🧠 Initializing the Office Agent with Standard Operating Procedures...")

    # 1. THE BRAIN (Using 1.5-flash for reliability/free tier)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    # 2. THE MEMORY (RAG Pipeline)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 2})
    )

    # 3. THE TOOLKIT
    policy_tool = create_policy_tool(qa_chain)
    search_tool = get_search_tool()
    tools = [policy_tool, search_tool, create_word_document]

    # 4. THE AGENT MANAGER (With "Mark" & Date Logic Baked In)
    
    # We define the "Personality" and "Rules" here.
    # This acts as the default context for every single interaction.
    system_instructions = (
        "You are the Executive Assistant for Supervisor Mark in the AI Department. "
        "You have access to tools. Use them to answer the user request."
        "\n\n"
        "### STANDARD OPERATING PROCEDURES (FOLLOW STRICTLY):"
        "\n1 If you need to find the current date use the tool"
        "\n2. SIGNATURE: All memos and letters must be addressed 'From: Mark, AI Department'."
        "\n3. FORMATTING: When writing the document body, be professional and concise."
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
    
    # THE ULTIMATE TEST (Clean Query)
    # Notice: We don't mention Mark or the Date here anymore!
    query = (
        "Read the internship policy to find the dress code and the wifi password. "
        "Then, write a formal memo addressed to 'New Interns' explaining these two rules."
    )
    
    agent_executor.invoke({"input": query})