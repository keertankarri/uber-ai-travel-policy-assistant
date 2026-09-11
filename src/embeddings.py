import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Import your Day 1 ingestion script
from ingestion import process_documents

# Define where to save the database
DB_DIR = Path(__file__).parent.parent / "data" / "vectorstore"

def build_vector_store():
    """Generates embeddings for chunks and saves them in a FAISS database."""
    # 1. Fetch the chunks from Day 1
    chunks = process_documents()
    
    if not chunks:
        print("❌ No chunks found. Please check your data folders.")
        return
        
    print("\n🧠 Initializing Embedding Model (Downloading 'all-MiniLM-L6-v2'...)")
    # 2. Load the open-source embedding model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # 3. Convert your dictionaries into standard LangChain Document objects
    print(f"🔄 Converting {len(chunks)} text chunks into LangChain Documents...")
    documents = [
        Document(page_content=chunk["text"], metadata=chunk["metadata"]) 
        for chunk in chunks
    ]
    
    # 4. Generate vectors and build the database
    print("⚙️ Generating vectors and building FAISS database. Please wait...")
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # 5. Save the database locally so we don't have to rebuild it every time
    os.makedirs(DB_DIR, exist_ok=True)
    vectorstore.save_local(str(DB_DIR))
    print(f"\n✅ Vector database successfully created and saved to: {DB_DIR}")

if __name__ == "__main__":
    build_vector_store()