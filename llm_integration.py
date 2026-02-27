import os
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def query_ollama(model, prompt, system_prompt=None):
    """
    Query Ollama API running in a separate container or locally.
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    url = f"{ollama_host}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API Connection Error: {e}")
        return None

def generate_rag_response(query, context, provider="local"):
    """
    Generate a response using the specified LLM provider.
    
    Args:
        query (str): The user's question.
        context (str): The retrieved context from the knowledge base.
        provider (str): 'ollama', 'openai', or 'local'.
    
    Returns:
        str: The generated response or None if failed.
    """
    
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3")
        system_prompt = (
            "You are a helpful AI assistant for Oudience, an e-commerce platform. "
            "Answer the user's question based strictly on the provided context. "
            "If the answer is not in the context, politely say you don't know. "
            "Keep answers professional, concise, and friendly."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        return query_ollama(model, prompt, system_prompt)
        
    elif provider == "openai":
        # Placeholder for OpenAI integration
        # intended for use if user supplies OPENAI_API_KEY
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, falling back to local.")
            return None
            
        try:
            # Simple manual request to avoid adding openai dependency if not needed
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful customer support assistant."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ]
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            return None

    return None
