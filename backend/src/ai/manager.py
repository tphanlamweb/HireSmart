import os
import threading
import logging
from typing import List

_embedding_model = None
_embeddings_cache = {}
_emb_model_lock = threading.Lock()

def get_embedding_model():
    """Lazily load and return the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        with _emb_model_lock:
            if _embedding_model is None:
                model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/LaBSE')
                logging.info(f"Loading embedding model: {model_name}")
                _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def get_embeddings(texts: List[str], batch_size: int = 32):
    """Get embeddings for a list of texts; caches results per-text."""
    key = (tuple(texts), batch_size)
    if key in _embeddings_cache:
        return _embeddings_cache[key]
    model = get_embedding_model()
    embs = model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    _embeddings_cache[key] = embs
    return embs

# ---- Ollama helpers ----
_OLLAMA_BASE = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
_OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')

def ollama_available(timeout: float = 1.0) -> bool:
    try:
        import requests
        r = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

def call_ollama(prompt: str, model: str | None = None, timeout: float = 10.0) -> str:
    """Call local Ollama generate API and return raw text output (may include JSON)."""
    import httpx
    m = model or _OLLAMA_MODEL
    url = f"{_OLLAMA_BASE}/api/generate"
    payload = {"model": m, "prompt": prompt, "max_tokens": 512}
    resp = httpx.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def setup_models():
    """Eagerly initialize heavy models at app startup if desired."""
    try:
        get_embedding_model()
    except Exception as e:
        logging.warning("Failed to load embedding model at startup: %s", e)
