import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.tools.retriever import create_retriever_tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# 1. Initialize Environment
load_dotenv()
print("🤖 Booting up Lenovo Smart Research Buddy (Terminal Mode)...")

# 2. Setup Database & Embeddings (matching your app.py)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory="vector_db", embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 3})

# 3. Setup Tools
internal_tool = create_retriever_tool(retriever, name="lenovo_internal", description="Search internal docs for Lenovo specs.")
web_tool = TavilySearch(max_results=3)

# 4. Setup LLM (This explicitly passes the model, preventing the 400 error)
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# 5. Setup Agent
system_instruction = """You are an autonomous enterprise "Smart Research Buddy" Agent.
Use your tools to find accurate information. Do not hallucinate. 
Format your output cleanly with bullet points, and append your sources at the end.
"""
agent = create_react_agent(model=llm, tools=[internal_tool, web_tool], prompt=system_instruction)

print("✅ System Ready.\n" + "="*50)

# 6. Terminal Chat Loop
while True:
    try:
        query = input("\n👤 Enter your enterprise research query (or type 'exit'):\n> ")
        if query.lower() in ['exit', 'quit']:
            print("Shutting down...")
            break
            
        print("\n🔴 Searching database and generating cited report...\n")
        
        # Run the agent
        final_state = agent.invoke({"messages": [HumanMessage(content=query)]})
        
        # Print the final response
        print("="*50)
        print(final_state["messages"][-1].content)
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")