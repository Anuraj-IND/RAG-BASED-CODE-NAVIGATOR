import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

CODE_EXT = (".py", ".js", ".ts", ".java", ".go", ".rs",".md")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
    return chunks

def index_repo(repo_path: str, index_path: str):
    docs = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(CODE_EXT):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for chunk in chunk_text(content):
                            if chunk.strip():
                                docs.append(
                                    Document(
                                        page_content=chunk,
                                        metadata={"path": path}
                                    )
                                )
                except:
                    pass

    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local(index_path)

    return len(docs)
