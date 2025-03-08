# File: gurbani-insight/app/utils/response.py

"""
Response formatting utilities for the Gurbani Insight application.

Provides functions for formatting search results into readable responses.
"""

import logging
import re
import requests
from typing import List, Dict, Any
from app.utils.embedding import get_best_available_model

logger = logging.getLogger(__name__)


def format_results(results: List[Dict[str, Any]], format_type: str = "default") -> str:
    """
    Format search results into a readable string.
    
    Args:
        results (List[Dict[str, Any]]): Search results
        format_type (str): Format type ("default", "chat", "summary", or "paragraph")
        
    Returns:
        str: Formatted results
    """
    if not results:
        return "No results were found for your query. Please try a different question."
        
    if format_type == "paragraph":
        return _format_as_paragraph(results)
    elif format_type == "summary":
        return _format_as_summary(results)
    elif format_type == "chat":
        return _format_as_chat(results)
    else:  # default format
        return _format_as_default(results)


def _format_as_paragraph(results: List[Dict[str, Any]]) -> str:
    """
    Format results as a coherent paragraph.
    
    Args:
        results (List[Dict[str, Any]]): Search results
        
    Returns:
        str: Formatted paragraph response
    """
    # Create a coherent paragraph response using only English text from the passages
    response = "According to the Guru Granth Sahib, "
    
    # Process each passage to extract meaningful English sentences
    english_sentences = []
    
    for r in results:
        # Filter out non-English or transliteration text
        text = r['text']
        
        # Replace "Dh", "N" and other non-English markers
        text = re.sub(r'\b[A-Z][a-z]*[A-Z]\w*\b', '', text)  # Remove words with internal capitals like "DhSangat"
        text = re.sub(r'\b[A-Z]{1,2}[a-z]+\b', '', text)     # Remove words starting with 1-2 caps like "Dh"
        
        # Split into sentences
        sentences = re.split(r'[.?!]', text)
        
        for sentence in sentences:
            # Clean up the sentence
            sentence = sentence.strip()
            
            # Skip if too short or contains transliteration markers
            if len(sentence) < 10 or re.search(r'-[a-z]{2,}', sentence):
                continue
                
            # Skip if the sentence has too many non-English words
            words = sentence.split()
            if len(words) < 3:
                continue
            
            # Skip sentences that don't start with a capital letter or "the"
            if not (sentence[0].isupper() or sentence.lower().startswith('the')):
                continue
            
            # Add to our collection if it's meaningful
            if len(sentence) > 20 and sentence not in english_sentences:
                english_sentences.append(sentence)
    
    # Combine sentences into a coherent paragraph
    if english_sentences:
        # Start with core concept sentences
        core_concepts = [s for s in english_sentences if 
                    re.search(r'(?i)god|lord|divine|creator|universal|creation', s)]
        
        # Add other sentences
        other_sentences = [s for s in english_sentences if s not in core_concepts]
        
        # Combine in a logical order
        all_sentences = core_concepts + other_sentences
        
        # Limit to reasonable paragraph length
        selected_sentences = all_sentences[:12]  # Adjust number as needed
        
        # Join into paragraph
        response += ' '.join(selected_sentences) + '.'
        
        # Remove double periods
        response = response.replace('..', '.')
    else:
        response += "the nature of God is described in profound spiritual terms. The teachings emphasize that God is the One Universal Creator, beyond description and infinite in nature. The Lord is described as supreme over all creation, with no equal in power or glory. The Guru Granth Sahib teaches that God is present in all things, from the beginning to the end, and is accessible through meditation, devotion, and the company of the holy."
    
    # Add source references at the end
    response += "\n\nThis wisdom comes from "
    source_refs = []
    for i, r in enumerate(results):
        source = f"{r['section']}, Ang: {r['ang_number']}"
        if r['raag'] and r['raag'] != "None" and r['raag'] != "Unknown":
            source += f", Raag: {r['raag']}"
        source_refs.append(source)
    
    response += "; ".join(source_refs) + " of the Guru Granth Sahib."
        
    return response


def _format_as_summary(results: List[Dict[str, Any]]) -> str:
    """
    Format results as a bullet point summary.
    
    Args:
        results (List[Dict[str, Any]]): Search results
        
    Returns:
        str: Formatted summary response
    """
    # Create a concise, direct response using only text from the passages
    response = "Based on the Guru Granth Sahib:\n\n"
    
    # Add core teachings from each passage without repeating similar content
    unique_points = set()
    
    for r in results:
        # Split text into sentences for easier handling
        sentences = r['text'].split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15:  # Skip very short fragments
                # Create a simplified version for duplicate detection
                simplified = ' '.join(sentence.lower().split())
                if simplified not in unique_points:
                    unique_points.add(simplified)
                    response += f"• {sentence}.\n"
    
    # Add source references at the end
    response += "\n---\n"
    response += "Sources from Guru Granth Sahib:\n"
    for i, r in enumerate(results):
        response += f"- {r['section']}, Ang: {r['ang_number']}"
        if r['raag'] and r['raag'] != "None" and r['raag'] != "Unknown":
            response += f", Raag: {r['raag']}"
        response += "\n"
        
    return response


def _format_as_chat(results: List[Dict[str, Any]]) -> str:
    """
    Format results as a chat response with passages.
    
    Args:
        results (List[Dict[str, Any]]): Search results
        
    Returns:
        str: Formatted chat response
    """
    response = "Here are passages from Guru Granth Sahib that may answer your question:\n\n"
    
    for i, r in enumerate(results):
        response += f"**Passage {i+1}**\n"
        response += f"Section: {r['section']}\n"
        response += f"Ang: {r['ang_number']}\n"
        
        if r['raag'] and r['raag'] != "None" and r['raag'] != "Unknown":
            response += f"Raag: {r['raag']}\n"
            
        response += f"Text: {r['text']}\n\n"
        
    return response


def _format_as_default(results: List[Dict[str, Any]]) -> str:
    """
    Format results with default formatting including scores.
    
    Args:
        results (List[Dict[str, Any]]): Search results
        
    Returns:
        str: Default formatted response
    """
    response = ""
    
    for i, r in enumerate(results):
        response += f"Section: {r['section']}\n"
        response += f"Ang: {r['ang_number']}\n"
        
        if r['raag'] and r['raag'] != "None" and r['raag'] != "Unknown":
            response += f"Raag: {r['raag']}\n"
            
        response += f"Text: {r['text']}\n"
        response += f"Score: {r['score']:.4f}\n\n"
        
    return response


def format_results_with_llm(original_query: str, results: List[Dict[str, Any]]) -> str:
    """
    Generate a more coherent response using a language model.
    
    Args:
        original_query (str): The user's original question
        results (List[Dict[str, Any]]): List of retrieved passages
        
    Returns:
        str: Formatted results with LLM-generated answer
    """
    # Extract the raw text and metadata from results
    passages = []
    sources = []
    relevant_contexts = []
    
    # Process each result to extract key information
    for r in results:
        passage_text = r['text']
        source = f"{r['section']}, Ang: {r['ang_number']}"
        if r['raag'] and r['raag'] != "None" and r['raag'] != "Unknown":
            source += f", Raag: {r['raag']}"
        
        passages.append(passage_text)
        sources.append(source)
        
        # Extract sentences that might be specifically relevant to the query
        query_terms = set(original_query.lower().split())
        for sentence in re.split(r'[.!?]', passage_text):
            sentence = sentence.strip()
            # Check if sentence contains query terms
            sentence_terms = set(sentence.lower().split())
            if query_terms.intersection(sentence_terms) and len(sentence) > 20:
                relevant_contexts.append(sentence)
    
    # Add the most relevant contexts to the beginning of the prompt
    relevant_context_text = ""
    if relevant_contexts:
        relevant_context_text = "Most relevant contexts:\n" + "\n".join([f"- {ctx}" for ctx in relevant_contexts[:5]])
    
    # Combine the passages into a single text
    combined_text = " ".join(passages)
    
    # Find the best available model
    model = get_best_available_model()
    
    # Try to generate a response with the selected model
    if model:
        try:
            logger.info(f"Generating answer with model: {model}")
            
            # Improved prompt that focuses on specificity and answering the exact question
            prompt = f"""
            I'll help you answer this specific question about the Guru Granth Sahib:
            
            QUESTION: "{original_query}"
            
            {relevant_context_text}
            
            Here are relevant passages from the Guru Granth Sahib:
            
            {combined_text}
            
            Please provide a specific, detailed response that directly answers the question. Your response should:
            
            1. Directly address the specific question being asked (about {original_query.lower()})
            2. Provide concrete guidance, examples, or principles from the Guru Granth Sahib!
            3. Reference specific concepts or teachings that are relevant to this topic!
            4. Be practical and applicable, not just general spiritual advice
            5. Avoid generic spiritual statements that could apply to any question
            6. Be clear, profound, and spiritually insightful
            7. Stay on topic!
            8. Be 4-6 sentences in length
            
            Provide ONLY the conversational response with no introduction or explanation.
            """
            
            # Call Ollama LLM with improved parameters
            logger.info(f"Sending request to Ollama")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,  # Lower temperature for more focused responses
                        "num_predict": 500,  # Allow for longer responses
                        "top_p": 0.85        # More focused token selection
                    }
                },
                timeout=25  # Increased timeout for more complex generation
            )
            
            logger.info(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                answer = response.json().get('response', '').strip()
                # Check if the answer is reasonable
                if len(answer) > 100:  # Ensure it's not too short
                    logger.info(f"Successfully generated answer with {model}")
                    return f"{answer}\n\nThis insight is based on teachings from {'; '.join(sources[:3])} of the Guru Granth Sahib."
                else:
                    logger.warning(f"Answer too short ({len(answer)} chars): {answer}")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to Ollama API. Is Ollama running?")
        except Exception as e:
            logger.error(f"Error generating answer with {model}: {e}")
    else:
        logger.warning("No LLM model available")
    
    # Enhanced fallback response generation that's more question-specific
    logger.warning("Falling back to question-specific template response")
    
    # Create a more topic-specific fallback response based on the query
    query_lower = original_query.lower()
    
    # Different templates for different question types
    if any(term in query_lower for term in ["anger", "angry", "frustration", "upset"]):
        fallback_response = "The Guru Granth Sahib teaches that anger (krodh) is one of the five passions that distance us from spiritual truth. To manage anger, the sacred text advises regular meditation (simran), cultivating forgiveness, and remembering that all happens within God's will (hukam). By recognizing the divine light in all beings, we naturally become less reactive and more compassionate. The Gurbani also suggests that practicing contentment (santokh) and humility (nimrata) helps diminish anger and fosters inner peace."
    
    elif any(term in query_lower for term in ["meditation", "meditate", "simran", "pray", "prayer"]):
        fallback_response = "The Guru Granth Sahib emphasizes meditation (simran) on God's Name as the primary path to spiritual growth. The sacred text teaches that effective meditation involves focusing the mind with complete devotion, repeating God's Name with each breath, and maintaining awareness throughout daily activities. The Gurbani advises joining the company of saintly people (sadh sangat) to strengthen your practice, and suggests early morning (amrit vela) as the optimal time for meditation. Through consistent practice, one experiences inner peace, spiritual awakening, and liberation from the cycle of suffering."
    
    elif any(term in query_lower for term in ["ego", "pride", "arrogance", "haumai"]):
        fallback_response = "According to the Guru Granth Sahib, ego (haumai) is the primary obstacle on the spiritual path. The sacred text teaches that ego creates separation from the divine and causes suffering through attachment and false identification. To overcome ego, the Gurbani prescribes selfless service (seva), meditation on God's Name, and surrendering to divine will (hukam). By recognizing that all accomplishments come from God rather than oneself, and by cultivating humility in the company of spiritually awakened souls, one gradually dissolves the ego and realizes the divine presence within."
    
    else:
        # General fallback that tries to be somewhat specific to the query
        # Extract key nouns from the query to make the response more relevant
        nouns = [word for word in query_lower.split() if word not in ["how", "what", "when", "where", "why", "is", "are", "to", "the", "and", "or", "of", "in", "with", "about", "can", "do", "does", "should", "would", "i", "me", "my", "mine", "we", "our", "us"]]
        topic = " and ".join(nouns[:2]) if nouns else "this spiritual matter"
        
        fallback_response = f"The Guru Granth Sahib addresses {topic} by emphasizing the importance of divine remembrance, truthful living, and selfless service. The sacred texts teach that by meditating on God's Name, we develop the spiritual wisdom to overcome obstacles and live in alignment with divine will. Through regular practice, cultivation of virtues like compassion, humility, and contentment, and by keeping the company of spiritually awakened souls, we experience transformation and find practical solutions to life's challenges."
    
    return f"{fallback_response}\n\nThis insight is based on teachings from {'; '.join(sources[:3] if sources else ['various sections'])} of the Guru Granth Sahib."