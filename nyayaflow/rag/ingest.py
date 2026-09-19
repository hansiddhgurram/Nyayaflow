"""Ingest legal documents into ChromaDB."""
import os
from typing import List, Dict, Any
from rag.retriever import LegalRetriever


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


def ingest_legal_document(
    file_path: str,
    act_name: str,
    source_url: str = "",
    chunk_size: int = 1000,
) -> None:
    """Ingest a single legal document file into ChromaDB."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text, chunk_size)
    retriever = LegalRetriever()

    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            "id": f"{act_name.replace(' ', '_')}_chunk_{i}",
            "content": chunk,
            "act_name": act_name,
            "section": f"Chunk {i+1}/{len(chunks)}",
            "title": f"{act_name} - Part {i+1}",
            "source_url": source_url,
        })

    retriever.add_documents(documents)
    print(f"Ingested {len(documents)} chunks from {act_name}")


def ingest_all_legal_docs(legal_docs_dir: str = "./legal_docs") -> None:
    """Ingest all legal documents in the directory."""
    mapping = {
        "mediation_act_2023.txt": ("Mediation Act, 2023", "https://www.indiacode.nic.in/handle/123456789/17124"),
        "it_act_2000.txt": ("Information Technology Act, 2000", "https://www.indiacode.nic.in/handle/123456789/1999"),
        "contract_act_1872.txt": ("Indian Contract Act, 1872", "https://www.indiacode.nic.in/handle/123456789/2187"),
        "consumer_protection_act_2019.txt": ("Consumer Protection Act, 2019", "https://www.indiacode.nic.in/handle/123456789/15141"),
        "msmde_act_2006.txt": ("MSMED Act, 2006", "https://www.indiacode.nic.in/handle/123456789/2989"),
    }

    for filename, (act_name, url) in mapping.items():
        filepath = os.path.join(legal_docs_dir, filename)
        if os.path.exists(filepath):
            ingest_legal_document(filepath, act_name, url)
        else:
            print(f"Warning: {filepath} not found, skipping.")


if __name__ == "__main__":
    ingest_all_legal_docs()
