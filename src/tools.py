import os
import sys
from dotenv import load_dotenv

# Load API key from .env file immediately
load_dotenv()

from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Ensure app directory is in path to import database models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
from models import db, User, Expense

# --- FAISS VECTOR DB INITIALIZATION ---
VECTORSTORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vectorstore'))

vectorstore = None
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    if os.path.exists(VECTORSTORE_DIR):
        vectorstore = FAISS.load_local(
            VECTORSTORE_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
except Exception as e:
    print(f"Warning: Could not initialize FAISS vector store: {e}")

# --- TOOL 1: FAISS Policy Search Tool (RAG) ---
@tool
def policy_search_tool(query: str) -> str:
    """Searches corporate travel policy documents for rules, limits, and guidelines."""
    if not vectorstore:
        return "Travel policy database is currently offline. Please run src/ingestion.py to generate the index and verify your GOOGLE_API_KEY."
    
    # Retrieve top 3 matching policy chunks from vectorstore
    docs = vectorstore.similarity_search(query, k=3)
    if not docs:
        return "No specific corporate policy guidelines found for this query."
        
    results = [f"- {doc.page_content}" for doc in docs]
    return "Relevant Corporate Policy Rules:\n" + "\n".join(results)

# --- TOOL 2: SQL Database Expense History Tool ---
@tool
def get_user_expense_history_tool(username: str) -> str:
    """Looks up past travel expense history for a given employee username from the database."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return f"No user found with username '{username}'."
    
    expenses = Expense.query.filter_by(user_id=user.id).order_by(Expense.date_submitted.desc()).all()
    if not expenses:
        return f"No expense history found for {username}."
    
    history = [
        f"- {e.category}: ${e.amount:.2f} (Status: {e.status}) on {e.date_submitted.strftime('%Y-%m-%d')}" 
        for e in expenses
    ]
    return f"Expense history for {user.name} ({username} - {user.department}):\n" + "\n".join(history)