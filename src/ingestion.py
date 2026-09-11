import os
import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

# Configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def clean_text(text: str) -> str:
    """Removes excessive line breaks and standardizes spacing."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_metadata(filename: str) -> dict:
    """Generates source, policy type, and country metadata based on filename."""
    name_lower = filename.lower()
    
    country = "Global"
    if "india" in name_lower:
        country = "India"
    elif "us" in name_lower:
        country = "US"

    policy_type = "general"
    for category in ["travel", "airport", "expense", "cancellation", "approval", "eligibility"]:
        if category in name_lower:
            policy_type = category
            break

    return {
        "source": filename,
        "policy_type": policy_type,
        "country": country
    }

def process_documents():
    """Loads, cleans, enriches with metadata, and chunks all policy documents."""
    script_dir = Path(__file__).parent.resolve()
    target_dir = script_dir.parent / "data" / "company_policy"

    if not target_dir.exists():
        print(f"❌ Error: Directory '{target_dir}' does not exist. Create it and place your .txt policy files inside.")
        return []

    txt_files = list(target_dir.glob("*.txt"))
    if not txt_files:
        print(f"⚠️ Warning: No .txt files found in '{target_dir}'.")
        return []

    print(f"\n{'Document Name':<32} | {'Character Count':<16} | {'Chunks Created':<15}")
    print("-" * 70)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    all_chunks = []

    for file_path in txt_files:
        filename = file_path.name
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                print(f"{filename:<32} | EMPTY (Skipped)   | 0")
                continue

            cleaned = clean_text(content)
            metadata = extract_metadata(filename)
            chunks = splitter.split_text(cleaned)

            for idx, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk,
                    "metadata": metadata,
                    "chunk_id": f"{filename}_chunk_{idx}"
                })

            print(f"{filename:<32} | {len(cleaned):<16,} | {len(chunks):<15}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("-" * 70)
    print(f"✅ Total Chunk Count: {len(all_chunks)}\n")

    return all_chunks

def create_faiss_vectorstore(chunks):
    """Converts chunks to embeddings and saves a local FAISS index."""
    if not chunks:
        print("❌ No chunks available to index.")
        return

    print("🧠 Initializing Google Gemini Embeddings...")
    # FIX: Added 'text-' to the model string
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # Convert dictionaries to LangChain Document objects
    documents = [
        Document(page_content=chunk["text"], metadata=chunk["metadata"]) 
        for chunk in chunks
    ]

    print("⚡ Generating FAISS vector store...")
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save to the root vectorstore directory (matches tools.py path)
    script_dir = Path(__file__).parent.resolve()
    vectorstore_dir = script_dir.parent / "vectorstore"
    vectorstore_dir.mkdir(parents=True, exist_ok=True)
    
    vectorstore.save_local(str(vectorstore_dir))
    print(f"🎉 FAISS vector store successfully saved to: {vectorstore_dir}\n")

if __name__ == "__main__":
    chunks = process_documents()
    if chunks:
        create_faiss_vectorstore(chunks)