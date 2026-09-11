import os
import sys
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Ensure tools module can be imported cleanly when called from Flask
sys.path.append(os.path.dirname(__file__))
from tools import policy_search_tool, get_user_expense_history_tool

# Initialize Gemini 3.6 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash", 
    temperature=0.2
)

# Define tools available to the AI agent
tools = [policy_search_tool, get_user_expense_history_tool]

# Travel-only system prompt (LangGraph state modifier)
system_prompt = """You are the Uber Corporate Travel Policy Assistant. 
Your primary job is to help employees navigate travel rules, expense limits, and their own expense history.

STRICT SCOPE LIMITATIONS:
1. You must ONLY answer questions related to corporate travel, expenses, and policy guidelines.
2. If a user asks about anything unrelated (e.g., coding, general knowledge, personal advice, weather), politely decline and state your specific purpose.
3. Use the `policy_search_tool` to look up general corporate travel rules.
4. Use the `get_user_expense_history_tool` to look up the user's specific expense history.

If the user asks about "my expenses", "what I spent", or similar, automatically use the provided active employee ID when calling the expense history tool.
"""

# Construct the LangGraph ReAct Agent
agent_executor = create_react_agent(
    model=llm, 
    tools=tools, 
    prompt=system_prompt
)

def ask_travel_agent(user_message: str, username: str = "Unknown") -> str:
    """Invokes the LangGraph travel agent with the user's message and session username."""
    try:
        contextual_message = f"[Active Employee ID: {username}]\nUser Question: {user_message}"
        
        response = agent_executor.invoke({"messages": [("user", contextual_message)]})
        raw_content = response["messages"][-1].content
        
        if isinstance(raw_content, list):
            text_parts = []
            for block in raw_content:
                if isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
                else:
                    text_parts.append(str(block))
            return "\n".join(text_parts)
            
        return str(raw_content)
        
    except Exception as e:
        print(f"Agent Error: {e}")
        return "I apologize, but I encountered a network or processing error. Please try again."

# Alias run_agent to ask_travel_agent for app.py compatibility
run_agent = ask_travel_agent