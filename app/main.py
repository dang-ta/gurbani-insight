# File: gurbani-insight/app/main.py

"""
Main FastAPI application for the Gurbani Insight service.

This module implements the API endpoints for searching and retrieving
information from the Guru Granth Sahib using semantic search.
"""

import logging
import os
import traceback
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.config import CHROMA_DB_PATH, COLLECTION_NAME, PORT, HOST
from app.models import SearchRequest, ChatRequest, ChatMessage, GenerateRequest
from app.utils.search import search_similar_texts, expand_query
from app.utils.response import format_results, format_results_with_llm
from app.utils.embedding import get_best_available_model, get_available_models

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Gurbani Insight API",
    description="API for searching and retrieving wisdom from the Guru Granth Sahib",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve the HTML interface
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main HTML interface."""
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running properly.
    
    Returns:
        dict: Service status information
    """
    try:
        # Check ChromaDB
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
            collection_count = collection.count()
            collection_status = f"Exists with {collection_count} documents"
        except Exception as e:
            collection_status = f"Error: {str(e)}"
            collection_count = 0
            
        # Check Ollama
        try:
            import requests
            ollama_response = requests.get(
                "http://localhost:11434/api/version",
                timeout=2
            )
            ollama_status = "Connected" if ollama_response.status_code == 200 else "Error"
            
            # Get available models
            models = get_available_models()
            ollama_models = ", ".join(models) if models else "None available"
        except Exception as e:
            ollama_status = f"Error: {str(e)}"
            ollama_models = "Not available"
        
        return {
            "status": "ok",
            "name": "Gurbani Insight API",
            "version": "1.0.0",
            "chromadb_collection": collection_status,
            "documents": collection_count,
            "ollama": ollama_status,
            "models": ollama_models
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Search endpoint for finding relevant passages in the Guru Granth Sahib.
    
    Args:
        request (SearchRequest): Search request with query and parameters
        
    Returns:
        dict: Search results and formatted response
    """
    try:
        logger.info(f"Search request: {request.query} (top_k={request.top_k}, format={request.format})")
        results = search_similar_texts(request.query, request.top_k)
        return {"results": results, "formatted_response": format_results(results, request.format)}
    except Exception as e:
        logger.error(f"Search API error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """
    Legacy endpoint for compatibility with older clients.
    
    Args:
        request (GenerateRequest): Generate request with prompt and parameters
        
    Returns:
        dict: Generated response
    """
    try:
        logger.info(f"Generate request: {request.prompt} (top_k={request.top_k})")
        results = search_similar_texts(request.prompt, request.top_k)
        return {"response": format_results(results)}
    except Exception as e:
        logger.error(f"Generate API error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    """
    OpenAI-compatible chat completion API for better integration.
    
    Args:
        request (ChatRequest): Chat request with messages and parameters
        
    Returns:
        dict: Chat completion response
    """
    logger.info(f"Chat completion request with model: {request.model}")
    try:
        # Extract the last user message as the query
        user_messages = [msg for msg in request.messages if msg.role.lower() == "user"]
        if not user_messages:
            logger.error("No user message found in request")
            raise HTTPException(status_code=400, detail="No user message found")
        
        # Get the original query
        original_query = user_messages[-1].content
        logger.info(f"Original query: {original_query}")
        
        # Look for conversation context in previous messages
        conversation_history = ""
        if len(request.messages) > 1:
            previous_messages = request.messages[:-1]
            conversation_history = "\n".join([f"{msg.role}: {msg.content}" for msg in previous_messages[-3:]])
        
        # Expand the query to improve semantic understanding
        expanded_query = expand_query(original_query)
        logger.info(f"Expanded query: {expanded_query}")
        
        # Determine optimal number of chunks to retrieve based on query complexity
        # Longer, more complex queries may need more sources
        words_in_query = len(original_query.split())
        base_k = request.top_k if request.top_k else 10
        
        # Adjust retrieval count based on query length and complexity
        if words_in_query > 15:
            num_chunks = min(base_k + 5, 20)  # Get more chunks for complex queries, max 20
        elif words_in_query < 5:
            num_chunks = max(base_k - 3, 5)   # Fewer chunks for simple queries, min 5
        else:
            num_chunks = base_k
            
        logger.info(f"Retrieving {num_chunks} chunks for query with {words_in_query} words")
        
        # Get search results with better error handling
        try:
            # Try multiple search strategies if needed
            results = search_similar_texts(expanded_query, num_chunks)
            
            # If we didn't get good results, try a more focused search
            if not results or len(results) < 3:
                logger.warning(f"Initial search returned insufficient results ({len(results) if results else 0}). Trying alternative query.")
                
                # Try with just key nouns from the query
                import re
                nouns = re.findall(r'\b[a-zA-Z]{3,}\b', original_query)
                alternative_query = " ".join(nouns)
                
                if alternative_query and alternative_query != expanded_query:
                    alternative_results = search_similar_texts(alternative_query, num_chunks)
                    if alternative_results and len(alternative_results) > len(results):
                        results = alternative_results
                        logger.info(f"Alternative query found {len(results)} results")
            
            logger.info(f"Found {len(results)} results")
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}\n{traceback.format_exc()}")
            # Return a fallback response
            return {
                "id": "chatcmpl-gurbani",
                "object": "chat.completion",
                "created": 1700,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I apologize, but I encountered an issue while searching the Guru Granth Sahib. The wisdom teaches us that patience and perseverance lead to spiritual growth. Please try your question again in a moment."
                    },
                    "finish_reason": "stop"
                }]
            }
        
        if not results:
            logger.warning("No results found for query")
            return {
                "id": "chatcmpl-gurbani",
                "object": "chat.completion",
                "created": 1700,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I couldn't find specific passages in the Guru Granth Sahib that address your question about " + 
                            original_query.lower() + ". Perhaps you could try rephrasing your question or asking about a related aspect of Sikh teachings?"
                    },
                    "finish_reason": "stop"
                }]
            }
        
        # Log the first result to help with debugging
        if results:
            logger.info(f"Top result - Section: {results[0]['section']}, Ang: {results[0]['ang_number']}")
            logger.info(f"Text snippet: {results[0]['text'][:100]}...")
        
        # Use the enhanced response generation with the original query for context
        response = format_results_with_llm(original_query, results)
        logger.info(f"Generated response of length {len(response)}")
        
        return {
            "id": "chatcmpl-gurbani",
            "object": "chat.completion",
            "created": 1700,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }]
        }
    except Exception as e:
        logger.error(f"Chat completion error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on application startup.
    
    This function checks if the ChromaDB collection exists and has data.
    If not, it logs an informative message about initializing the database.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
            count = collection.count()
            if count > 0:
                logger.info(f"ChromaDB collection '{COLLECTION_NAME}' exists with {count} documents")
            else:
                logger.warning(f"ChromaDB collection '{COLLECTION_NAME}' exists but is empty")
                logger.info("To initialize the database, run: python -m app.process_data")
        except Exception:
            logger.warning(f"ChromaDB collection '{COLLECTION_NAME}' does not exist")
            logger.info("To initialize the database, run: python -m app.process_data")
            
    except Exception as e:
        logger.error(f"Error connecting to ChromaDB: {str(e)}")


# Script entrypoint for running with Python directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)