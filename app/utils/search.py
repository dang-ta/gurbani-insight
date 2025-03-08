# File: gurbani-insight/app/utils/search.py

"""
Search functionality for the Gurbani Insight application.

Provides functions for searching and retrieving relevant passages from the Guru Granth Sahib.
"""

import logging
import re
import traceback
from typing import List, Dict, Any, Optional
import chromadb
from app.config import CHROMA_DB_PATH, COLLECTION_NAME
from app.utils.embedding import get_embedding

logger = logging.getLogger(__name__)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)


def search_similar_texts(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search for texts similar to the query using ChromaDB.
    
    Args:
        query_text (str): The search query
        top_k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: List of search results with metadata
    """
    try:
        # Get collection
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        logger.info(f"Got collection with {collection.count()} documents")
        
        # Get embedding for the query
        try:
            logger.info(f"Getting embedding for query: {query_text[:50]}...")
            query_embedding = get_embedding(query_text)
            logger.info(f"Got embedding with {len(query_embedding)} dimensions")
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            logger.warning("Falling back to random embedding for search")
            # Use the fallback embedding from the embedding module
            query_embedding = get_embedding("")  # This will trigger fallback
        
        # Search
        logger.info(f"Searching with top_k={top_k}")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Check if we got any results
        if not results["ids"][0]:
            logger.warning("No results returned from ChromaDB")
            return []
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            # Safely get metadata values with defaults
            metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
            
            formatted_results.append({
                'score': results["distances"][0][i] if i < len(results["distances"][0]) else 1.0,
                'text': results["documents"][0][i] if i < len(results["documents"][0]) else "No text available.",
                'ang_number': metadata.get('ang_number', 0),
                'section': metadata.get('section', "Unknown"),
                'raag': metadata.get('raag', ""),
                'page_num': metadata.get('page_num', 0)
            })
        
        logger.info(f"Formatted {len(formatted_results)} results")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}\n{traceback.format_exc()}")
        # Return empty results instead of raising
        return []


def expand_query(query: str) -> str:
    """
    Expand the query with relevant terms to improve search results.
    
    Args:
        query (str): The original user query
        
    Returns:
        str: Expanded query for better semantic search
    """
    query_lower = query.lower()
    
    # Topic-specific expansion dictionary with more targeted terms
    topic_expansions = {
        "anger": ["krodh", "anger", "rage", "control emotions", "peace", "calm", "patience", 
                 "forgiveness", "tranquility", "conflict", "frustration", "equanimity"],
        
        "meditation": ["simran", "meditation", "prayer", "naam", "recitation", "jap", "focus", 
                      "concentration", "awareness", "mindfulness", "divine remembrance", "amrit vela"],
        
        "ego": ["haumai", "ego", "pride", "arrogance", "humility", "self", "identity", 
               "surrender", "submission", "attachment", "selfless", "nimrata"],
        
        "fear": ["bhau", "fear", "anxiety", "worry", "courage", "faith", "trust", 
                "divine protection", "surrender", "spiritual strength", "confidence"],
        
        "wealth": ["dhan", "wealth", "money", "prosperity", "greed", "contentment", "attachment", 
                  "possessions", "material", "spiritual wealth", "true riches", "santokh"],
        
        "relationships": ["family", "marriage", "love", "friendship", "community", "harmony", 
                         "unity", "service", "sangat", "compassion", "respect", "support"],
        
        "truth": ["sat", "truth", "reality", "honesty", "integrity", "authenticity", 
                 "falsehood", "illusion", "maya", "wisdom", "understanding", "realization"],
        
        "duty": ["dharam", "duty", "responsibility", "action", "karma", "righteousness", 
                "conduct", "ethics", "moral", "virtuous living", "discipline", "guidance"],
        
        "liberation": ["mukti", "liberation", "salvation", "freedom", "release", "enlightenment", 
                      "awakening", "realization", "union", "divine connection", "spiritual goal"],
        
        "suffering": ["dukh", "suffering", "pain", "difficulty", "challenge", "comfort", 
                     "relief", "peace", "healing", "acceptance", "resilience", "overcoming"]
    }
    
    # Common spiritual concepts
    spiritual_concepts = {
        "god": ["waheguru", "divine", "lord", "creator", "akal", "one", "supreme being", "truth", "hari", "prabh", "gopal", "ram"],
        "meditation": ["simran", "naam", "jap", "recitation", "devotion", "prayer", "worship", "bhajan", "kirtan"],
        "karma": ["action", "deed", "consequence", "dharma", "duty", "righteous", "virtue", "karam"],
        "peace": ["contentment", "happiness", "joy", "bliss", "tranquility", "shanti", "harmony", "santokh", "sukh", "anand"],
        "soul": ["atma", "spirit", "consciousness", "essence", "self", "being", "identity", "jot", "light"],
        "salvation": ["mukti", "liberation", "freedom", "enlightenment", "realization", "union", "jivan-mukti"],
        "illusion": ["maya", "attachment", "desire", "ego", "pride", "materialism", "worldly", "moh", "bharam", "haumai"],
        "guru": ["teacher", "guide", "master", "wisdom", "knowledge", "teachings", "instruction", "satguru", "sant"],
        "congregation": ["sangat", "community", "fellowship", "gathering", "company", "assembly", "sadh sangat", "sat sangat"],
        "equality": ["justice", "fairness", "impartiality", "oneness", "unity", "brotherhood", "sarbat da bhala"]
    }
    
    # First, check for topic-specific matches
    expanded_terms = []
    matched_topic = False
    
    for topic, terms in topic_expansions.items():
        if topic in query_lower or any(term in query_lower for term in terms[:3]):
            expanded_terms.extend(terms)
            matched_topic = True
            break
    
    # If no topic match, try the general spiritual concepts
    if not matched_topic:
        for concept, related_terms in spiritual_concepts.items():
            if concept in query_lower or any(term in query_lower for term in related_terms[:3]):
                expanded_terms.append(concept)
                expanded_terms.extend(related_terms[:5])
    
    # Extract key phrases based on question type
    question_type_additions = []
    if re.search(r'\b(how|ways?)\b', query_lower):
        question_type_additions = ["method", "technique", "practice", "approach", "guidance", "instruction", "path", "discipline"]
    elif re.search(r'\b(what|explain|mean|meaning)\b', query_lower):
        question_type_additions = ["definition", "concept", "teaching", "principle", "explanation", "wisdom", "understanding"]
    elif re.search(r'\b(why|reason|purpose)\b', query_lower):
        question_type_additions = ["purpose", "reason", "cause", "significance", "importance", "meaning", "goal"]
    elif re.search(r'\bwhen\b', query_lower):
        question_type_additions = ["time", "moment", "period", "circumstance", "condition", "stage", "phase"]
    
    # Add question type specific terms
    expanded_terms.extend(question_type_additions)
    
    # Ensure no duplicates and limit expansion size
    expanded_terms = list(set(expanded_terms))[:15]  # Limit to 15 terms
    
    # If we found relevant concepts, add them to the query
    if expanded_terms:
        expanded_query = f"{query} {' '.join(expanded_terms)}"
        logger.info(f"Expanded query: {query} → {expanded_query}")
        return expanded_query
    else:
        # If no specific match, use minimal generic expansion
        logger.info(f"No specific match found for expansion, using original query: {query}")
        return query