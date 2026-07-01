import os
import numpy as np
from typing import List, Union
from loguru import logger
import google.generativeai as genai

# Globals for caching models
_local_model = None

def get_embedding_provider() -> str:
    """Returns the configured embedding provider ('local' or 'gemini')."""
    return os.getenv("EMBEDDING_PROVIDER", "local").lower()

def get_gemini_embedding_model() -> str:
    """Returns the configured Gemini embedding model."""
    return os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

def get_local_embedding_model_name() -> str:
    """Returns the configured local sentence-transformers model name."""
    return os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

def _init_local_model():
    """Initializes and caches the local SentenceTransformer model."""
    global _local_model
    if _local_model is not None:
        return _local_model
        
    model_name = get_local_embedding_model_name()
    logger.info(f"Initializing local sentence-transformers model: {model_name}")
    try:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(model_name)
        return _local_model
    except ImportError:
        logger.warning("sentence-transformers not installed. Falling back to simple vectorizer.")
        raise
    except Exception as e:
        logger.error(f"Failed to load sentence-transformers model {model_name}: {str(e)}")
        raise

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Computes vector embeddings for a list of texts using the configured provider.
    """
    if not texts:
        return []
        
    provider = get_embedding_provider()
    
    if provider == "gemini":
        try:
            logger.info("Generating embeddings via Gemini Embeddings API")
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key:
                genai.configure(api_key=api_key)
            model = get_gemini_embedding_model()
            if not model.startswith("models/"):
                model_name = f"models/{model}"
            else:
                model_name = model
                
            # Clean texts to avoid API errors
            cleaned_texts = [t.replace("\n", " ") for t in texts]
            response = genai.embed_content(
                model=model_name,
                content=cleaned_texts,
                task_type="retrieval_document"
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding generation failed: {str(e)}. Falling back to local/simple.")
            # Fall through to local
            
    # Local sentence-transformers (default)
    try:
        model = _init_local_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Local sentence-transformers failed: {str(e)}. Using TF-IDF mock embeddings.")
        return _mock_embeddings_tfidf(texts)

def get_embedding(text: str) -> List[float]:
    """Computes a vector embedding for a single text."""
    res = get_embeddings([text])
    return res[0] if res else []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes the cosine similarity between two vectors."""
    if not v1 or not v2:
        return 0.0
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(arr1, arr2) / (norm1 * norm2))

def compute_similarity_matrix(source_embeddings: List[List[float]], target_embeddings: List[List[float]]) -> np.ndarray:
    """Computes a matrix of cosine similarities between two lists of embeddings."""
    if not source_embeddings or not target_embeddings:
        return np.zeros((len(source_embeddings), len(target_embeddings)))
        
    s_arr = np.array(source_embeddings)
    t_arr = np.array(target_embeddings)
    
    # Normalize vectors
    s_norms = np.linalg.norm(s_arr, axis=1, keepdims=True)
    t_norms = np.linalg.norm(t_arr, axis=1, keepdims=True)
    
    s_norms[s_norms == 0] = 1.0
    t_norms[t_norms == 0] = 1.0
    
    s_normed = s_arr / s_norms
    t_normed = t_arr / t_norms
    
    return np.dot(s_normed, t_normed.T)

def _mock_embeddings_tfidf(texts: List[str]) -> List[List[float]]:
    """
    Fallback mock vectorizer using scikit-learn's TfidfVectorizer.
    Useful for testing or when deep learning models fail to load.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(max_features=128, stop_words="english")
    try:
        # Fit vectorizer on current texts
        # If texts list is too small or single word, add dummy context
        corpus = texts + ["python react java cloud database experience developer"]
        matrix = vectorizer.fit_transform(corpus)
        # Return only the parts corresponding to original texts
        dense = matrix.toarray()[:len(texts)]
        return dense.tolist()
    except Exception as e:
        logger.error(f"Fallback vectorizer failed: {e}")
        # Return random/identity vector
        return [[1.0] + [0.0] * 127 for _ in texts]
