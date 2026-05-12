from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.tools.retriever import create_retriever_tool
from langchain.agents import create_agent
from dotenv import load_dotenv

# Load API keys (Tavily) from .env
load_dotenv()

# ==========================================
# 1. EphiUIP TOOL A: INTERNAL LENOVO DATABASE
# ==========================================
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory="vector_db", embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 3})

internal_search_tool = create_retriever_tool(
    retriever,
    name="lenovo_internal_search",
    description="Use this tool to search for internal Lenovo server specs, AI strategy, and Dell comparisons. ALWAYS use this first for Lenovo hardware questions."
)

# ==========================================
# 2. EQUIP TOOL B: EXTERNAL WEB SEARCH
# ==========================================
# Updated to the new TavilySearch class
web_search_tool = TavilySearch(max_results=3)
web_search_tool.name = "web_search"
web_search_tool.description = "Use this tool to search the live internet for recent news, stock prices, or general data not found in Lenovo's internal documents."

tools = [internal_search_tool, web_search_tool]

# ==========================================
# 3. SETUP THE BRAIN & THE STATE MACHINE
# ==========================================
llm = ChatOllama(model="qwen 2.5:3b", temperature=0)

# The new V1.0 standard: Just a clean, raw string!
system_instruction = """
You are a highly professional AI Solution Architect at Lenovo.
Your job is to answer questions accurately and CONCISELY. 
- If you use the web search tool, extract ONLY the exact fact requested and write a 1-2 sentence summary. Do not output massive raw JSON data.
- If you use the internal search tool, you MUST cite the filename like this: (Source: filename.txt).
"""

# The Agent is now built using the new 'system_prompt' parameter
agent = create_agent(
    model=llm, 
    tools=tools, 
    system_prompt=system_instruction
)

# ==========================================
# 4. EXECUTE THE CLEAN LOOP
# ==========================================
print("🤖 Enterprise LangChain V1.0 Agent Initialized.")
query = input("\nEnter your complex research query: ")

print("\nThinking... (Agent is querying tools in the background)\n")

# .invoke() runs the whole loop silently and only returns the final state
final_state = agent.invoke({"messages": [("user", query)]})

# We extract ONLY the very last message (the AI's final human-readable answer)
final_answer = final_state["messages"][-1].content

print("==================================================")
print("FINAL CONCISE REPORT:")
print("==================================================")
print(final_answer)