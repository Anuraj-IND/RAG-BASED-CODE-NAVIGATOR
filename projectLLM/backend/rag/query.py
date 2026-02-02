from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from .scaledown import scaledown_compress




def ask_question(index_path: str, query: str):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    docs = db.similarity_search(query, k=3)

    raw_context = "\n\n".join(
        f"[{d.metadata['path']}]\n{d.page_content}" for d in docs
    )

    context = scaledown_compress(raw_context, query)

    llm = OllamaLLM(
        model="qwen2.5:3b-instruct",
        num_ctx=4096,
        num_predict=2048
    )

    prompt = f"""
You are a codebase expert.

Context:
{context}

Question:
{query}

Explain clearly and mention file paths.
"""

    return llm.invoke(prompt)
