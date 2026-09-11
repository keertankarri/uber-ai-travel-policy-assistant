import os
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Define the path to your newly created vector database
DB_DIR = Path(__file__).parent.parent / "data" / "vectorstore"

def get_retriever():
    """Loads the FAISS database and returns a LangChain retriever."""
    if not os.path.exists(DB_DIR):
        raise FileNotFoundError(f"Vector database not found at {DB_DIR}. Please run embeddings.py first.")

    # We must use the EXACT same embedding model used during ingestion
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Load the local FAISS index
    vectorstore = FAISS.load_local(
        str(DB_DIR), 
        embeddings, 
        allow_dangerous_deserialization=True # Required for local FAISS loading
    )
    
    # Configure it to return the top 3 most relevant chunks
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def retrieve_policy_context(query: str) -> str:
    """Searches the database and formats the results into a single text block."""
    retriever = get_retriever()
    results = retriever.invoke(query)
    
    if not results:
        return "No relevant policy documents found."
    
    # Combine the retrieved chunks into a single readable context block
    context = "\n\n".join([f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" for doc in results])
    return context

if __name__ == "__main__":
    # Let's test the retrieval engine!
    print("🤖 Booting up the RAG Retrieval Engine...\n")
    
    test_query = "What is the travel budget limit for a trip to India?"
    print(f"👤 User Query: '{test_query}'\n")
    
    context = retrieve_policy_context(test_query)
    
    print("🔍 Retrieved Context:")
    print("-" * 50)
    print(context)
    print("-" * 50)