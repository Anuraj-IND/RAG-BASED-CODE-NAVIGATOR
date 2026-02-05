from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from .scaledown import scaledown_compress

def get_response_from_rag(history: list, index_path: str) -> str:
    """
    Generates response using FULL conversation history (not just last query)
    Args:
        history: List of dicts [{"query": str, "response": str}]
        index_path: Path to the FAISS index
    Returns:
        str: Response based on entire conversation history
    """
    # Get the current query (last one in history)
    current_query = history[-1]['query']
    
    # Build conversation context from history
    conversation_context = ""
    for i, msg in enumerate(history[:-1]):  # All except the last one
        if msg.get('response'):
            conversation_context += f"Previous Q: {msg['query']}\nPrevious A: {msg['response']}\n\n"
    
    # Use the actual RAG system with the current query
    # The conversation context can be included in the prompt
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    docs = db.similarity_search(current_query, k=2)
    
    raw_context = "\n\n".join(
        f"[{d.metadata['path']}]\n{d.page_content}" for d in docs
    )
    
    context = scaledown_compress(raw_context, current_query)
    
    llm = OllamaLLM(
        model="qwen3:4b",
        num_ctx=4096,
        num_predict=15068,
    )
    
    # Build prompt with conversation history
    history_prompt = ""
    if conversation_context:
        history_prompt = f"\n\nPrevious Conversation:\n{conversation_context}"
    
    prompt = f"""
You are a codebase expert.

Context from codebase:
{context}
{history_prompt}
Current Question:
{current_query}

Explain clearly and mention file paths. Consider the conversation history when answering.
"""
    
    return llm.invoke(prompt)


def ask_question(index_path: str, query: str):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    docs = db.similarity_search(query, k=2)

    raw_context = "\n\n".join(
        f"[{d.metadata['path']}]\n{d.page_content}" for d in docs
    )

    context = scaledown_compress(raw_context, query)

    llm = OllamaLLM(
    model="qwen3:4b",
    num_ctx=4096,
    num_predict=15068,   # BIG speed win
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
