# File: gurbani-insight/app/utils/embedding.py

"""
Embedding utilities for the Gurbani Insight application.

Provides functions for generating text embeddings using Ollama API.
"""

import logging
import random
import requests
from typing import List
from app.config import EMBEDDING_MODEL, OLLAMA_API_URL

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """
    Get embeddings from Ollama API with error handling.
    
    Args:
        text (str): Text to generate embedding for
        
    Returns:
        List[float]: Vector embedding
    
    Notes:
        If the embedding generation fails, a random embedding is returned
        as a fallback to allow the application to continue functioning.
    """
    try:
        # Log the attempt to connect to Ollama
        logger.info(f"Requesting embedding for text: {text[:50]}...")
        
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=5  # Add a timeout to avoid hanging
        )
        
        if response.status_code == 200:
            embedding = response.json().get('embedding')
            if embedding:
                logger.info(f"Successfully received embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error(f"Embedding response missing 'embedding' field: {response.json()}")
                return _get_fallback_embedding()
        else:
            logger.error(f"Embedding API error: {response.text}")
            return _get_fallback_embedding()
            
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to Ollama API at {OLLAMA_API_URL}. Is Ollama running?")
        return _get_fallback_embedding()
        
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        return _get_fallback_embedding()


def _get_fallback_embedding() -> List[float]:
    """
    Generate a fallback random embedding.
    
    Returns:
        List[float]: A random embedding vector
    """
    logger.warning("Using fallback random embedding")
    return [random.uniform(-1, 1) for _ in range(768)]  # 768 dimensions for compatibility


def get_best_available_model() -> str:
    """
    Find the best available model for text generation.
    
    Returns:
        str: Name of the best available model, or None if no models are available
    """
    available_models = get_available_models()
    logger.info(f"Available models: {available_models}")
    
    # Models in order of preference
    preferred_models = ["phi3", "mistral", "llama3", "phi", "gemma:2b", "gemma", "llama2", "neural-chat"]
    
    # Try to find any preferred model
    for model in preferred_models:
        for available in available_models:
            if model in available.lower():
                logger.info(f"Selected model: {available}")
                return available
    
    # If no preferred model is found but there are models, return the first one
    if available_models:
        logger.info(f"Using fallback model: {available_models[0]}")
        return available_models[0]
    
    # No models available
    logger.warning("No models available")
    return None


def get_available_models() -> List[str]:
    """
    Get list of available Ollama models.
    
    Returns:
        List[str]: List of available model names
    """
    try:
        response = requests.get(
            OLLAMA_API_URL.replace("/embeddings", "/tags"),
            timeout=2
        )
        if response.status_code == 200:
            return [model['name'] for model in response.json().get('models', [])]
        return []
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return []