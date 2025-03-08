# File: gurbani-insight/app/process_data.py

"""
Data processing script for the Gurbani Insight application.

Processes the Guru Granth Sahib PDF, extracts text, and stores it in ChromaDB.
"""

import os
import re
import pandas as pd
from tqdm import tqdm
import pypdf
import logging
import chromadb
from app.config import CHROMA_DB_PATH, COLLECTION_NAME, PDF_PATH, CSV_PATH
from app.utils.embedding import get_embedding

logger = logging.getLogger(__name__)


def identify_raag(text):
    """
    Identify Raag from text.
    
    Args:
        text (str): Text to process
        
    Returns:
        str or None: Identified raag name, or None if not found
    """
    raag_patterns = [
        r'Raag[u]?\s+([A-Za-z\s]+)',
        r'rwgu\s+([A-Za-z\s]+)'
    ]
    
    for pattern in raag_patterns:
        match = re.search(pattern, text)
        if match:
            raag = match.group(1).strip()
            raag = re.sub(r'\s+', ' ', raag)
            return raag
    return None


def identify_section(text):
    """
    Enhanced section identification for Guru Granth Sahib.
    
    Args:
        text (str): Text to process
        
    Returns:
        str or None: Identified section name, or None if not found
    """
    # First, check for Mool Mantar by its distinctive phrases
    mool_mantar_indicators = [
        "One Universal Creator God",
        "The Name Is Truth",
        "Creative Being Personified",
        "No Fear. No Hatred"
    ]
    
    if any(indicator in text for indicator in mool_mantar_indicators):
        return "Mool Mantar"
    
    # Define sections with their indicators
    sections = {
        'japji': {
            'name': 'Japji Sahib',
            'indicators': ['japji', 'listening-truth', 'by the karma of past actions']
        },
        'jaap': {
            'name': 'Jaap Sahib',
            'indicators': ['jaap sahib', 'infinite destroyer']
        },
        'rehras': {
            'name': 'Rehras Sahib',
            'indicators': ['rehras', 'evening prayers']
        },
        'anand': {
            'name': 'Anand Sahib',
            'indicators': ['anand sahib', 'song of bliss']
        },
        'asa_di_var': {
            'name': 'Asa Di Var',
            'indicators': ['asa di var', 'ballad of asa']
        },
        'sukhmani': {
            'name': 'Sukhmani Sahib',
            'indicators': ['sukhmani', 'pearl of peace']
        }
    }
    
    lower_text = text.lower()
    for section_info in sections.values():
        if any(indicator in lower_text for indicator in section_info['indicators']):
            return section_info['name']
    
    return None


def extract_ang_number(text, page_num):
    """
    Enhanced Ang number extraction with special handling for initial pages.
    
    Args:
        text (str): Text to process
        page_num (int): PDF page number
        
    Returns:
        int or None: Extracted Ang number, or None if not found
    """
    # Special handling for initial pages
    if page_num <= 6:  # Adjust this number based on PDF structure
        if "One Universal Creator God" in text or "The Name Is Truth" in text:
            return 1
        return None
    
    # Regular Ang number extraction
    patterns = [
        r'pMnw\s*(\d+)',  # Standard Gurmukhi
        r'AMg\s*(\d+)',   # Alternative spelling
        r'Ang\s*(\d+)',   # English
        r'Page\s*(\d+)'   # Direct English
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            ang_num = int(match.group(1))
            # Validate Ang number (adjust range as needed)
            if 1 <= ang_num <= 1430:
                return ang_num
    
    return None


def clean_text_with_context(text, page_num):
    """
    Enhanced version of clean_text that includes page number for better context.
    
    Args:
        text (str): Text to clean
        page_num (int): PDF page number
        
    Returns:
        tuple: (cleaned_text, context_dict)
    """
    context = {
        'ang_number': extract_ang_number(text, page_num),
        'raag': identify_raag(text),
        'section': identify_section(text)
    }
    
    cleaned_text = clean_text(text)
    
    return cleaned_text, context


def extract_english_translation(line):
    """
    Extract only the English translation from a line of text.
    
    Args:
        line (str): Line of text to process
        
    Returns:
        str: Extracted English translation, or empty string if not found
    """
    # Skip lines containing Gurmukhi script
    if re.search(r'[\u0A00-\u0A7F]', line):
        parts = re.split(r'[\u0A00-\u0A7F]+.*?]', line)
        if len(parts) > 1:
            line = parts[-1]
        else:
            return ""

    # Look for English text that starts with capital letter
    matches = re.findall(r'[A-Z][^.!?]*[.!?]', line)
    
    if matches:
        # Join complete English sentences
        return ' '.join(matches).strip()
    
    # Alternative: look for English after common separators
    if ']' in line:
        parts = line.split(']')
        if len(parts) > 1 and re.match(r'^[A-Z]', parts[-1].strip()):
            return parts[-1].strip()
    
    return ""


def clean_text(text):
    """
    Clean text to keep only English translations.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text with only English translations
    """
    if "Sentence By Sentence English Translation" in text or "database also by:" in text:
        return ""
    
    english_translations = []
    lines = text.split('\n')
    
    for line in lines:
        # Skip header and metadata lines
        if any(x in line for x in ["pMnw", "Phonetic", "Transliteration by:", "************************", "||"]):
            continue
            
        # Get English translation
        english_part = extract_english_translation(line)
        if english_part:
            # Additional cleaning
            english_part = re.sub(r'\([^)]*\)', '', english_part)  # Remove parentheses
            english_part = re.sub(r'\|\|.*?\|\|', '', english_part)  # Remove verse numbers
            english_part = re.sub(r'\s+', ' ', english_part)  # Normalize whitespace
            english_part = english_part.strip()
            
            # Verify it's a proper English sentence
            if (len(english_part.split()) > 2 and  # At least 3 words
                english_part[0].isupper() and      # Starts with capital letter
                not any(char.isdigit() for char in english_part)):  # No numbers
                english_translations.append(english_part)
    
    return ' '.join(english_translations)


def preprocess_gurbani_pdf(pdf_path):
    """
    Enhanced preprocessing with contextual information.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of chunks with metadata
    """
    logger.info(f"Processing PDF: {pdf_path}")
    pdf_reader = pypdf.PdfReader(pdf_path)
    chunks = []
    current_chunk = []
    current_length = 0
    target_chunk_size = 200
    
    # Track context across pages
    current_context = {
        'ang_number': None,
        'raag': None,
        'section': None
    }
    
    # Skip first page (contains header information)
    for page_num in tqdm(range(1, len(pdf_reader.pages)), desc="Processing pages"):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        
        blocks = text.split('\n\n')
        for block in blocks:
            # Pass page_num to clean_text_with_context
            cleaned_text, block_context = clean_text_with_context(block, page_num)
            
            # Update current context if new information is found
            current_context.update({k: v for k, v in block_context.items() if v is not None})
            
            if cleaned_text:
                words = cleaned_text.split()
                current_chunk.extend(words)
                current_length += len(words)
                
                if current_length >= target_chunk_size:
                    chunk_text = ' '.join(current_chunk)
                    if len(chunk_text.split()) > 50:  # Ensure minimum chunk size
                        chunks.append({
                            'id': len(chunks),
                            'text': chunk_text,
                            'page_num': page_num + 1,
                            'ang_number': current_context['ang_number'],
                            'raag': current_context['raag'],
                            'section': current_context['section'],
                            'prev_chunk_id': len(chunks) - 1 if len(chunks) > 0 else None,
                            'next_chunk_id': len(chunks) + 1  # Will be updated for last chunk
                        })
                    current_chunk = []
                    current_length = 0
    
    # Add any remaining content
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if len(chunk_text.split()) > 50:
            chunks.append({
                'id': len(chunks),
                'text': chunk_text,
                'page_num': page_num + 1,
                'ang_number': current_context['ang_number'],
                'raag': current_context['raag'],
                'section': current_context['section'],
                'prev_chunk_id': len(chunks) - 1 if len(chunks) > 0 else None,
                'next_chunk_id': None
            })
    
    # Fix next_chunk_id for last chunk
    if chunks:
        chunks[-1]['next_chunk_id'] = None
    
    logger.info(f"Generated {len(chunks)} chunks from PDF")
    return chunks


def load_chunks_to_chromadb(chunks):
    """
    Load chunks into ChromaDB.
    
    Args:
        chunks (list): List of chunks to load
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Connecting to ChromaDB at: {CHROMA_DB_PATH}")
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Check if collection exists
        try:
            collection = client.get_collection(name=COLLECTION_NAME)
            logger.info(f"Collection '{COLLECTION_NAME}' already exists with {collection.count()} documents")
            # Optional: delete existing collection
            client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection '{COLLECTION_NAME}'")
        except Exception as e:
            logger.info(f"Collection '{COLLECTION_NAME}' does not exist: {str(e)}")
        
        # Create collection
        collection = client.create_collection(name=COLLECTION_NAME)
        logger.info(f"Created collection '{COLLECTION_NAME}'")
        
        # Process chunks in batches
        batch_size = 50
        for i in tqdm(range(0, len(chunks), batch_size), desc="Loading chunks to ChromaDB"):
            batch = chunks[i:i + batch_size]
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for chunk in batch:
                # Generate embedding
                try:
                    embedding = get_embedding(chunk['text'])
                    
                    # Add to batch
                    ids.append(str(chunk['id']))
                    embeddings.append(embedding)
                    metadatas.append({
                        'ang_number': int(chunk['ang_number']) if chunk['ang_number'] is not None else 0,
                        'section': str(chunk['section']) if chunk['section'] is not None else "Unknown",
                        'raag': str(chunk['raag']) if chunk['raag'] is not None else "",
                        'page_num': int(chunk['page_num']),
                        'prev_chunk_id': int(chunk['prev_chunk_id']) if chunk['prev_chunk_id'] is not None else -1,
                        'next_chunk_id': int(chunk['next_chunk_id']) if chunk['next_chunk_id'] is not None else -1
                    })
                    documents.append(chunk['text'])
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk['id']}: {str(e)}")
                    continue
            
            # Add batch to collection
            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                logger.info(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} to ChromaDB")
        
        logger.info(f"Successfully loaded {len(chunks)} chunks to ChromaDB")
        return True
    except Exception as e:
        logger.error(f"Error loading chunks to ChromaDB: {str(e)}")
        return False


def save_chunks_to_csv(chunks, csv_path):
    """
    Save chunks to CSV file.
    
    Args:
        chunks (list): List of chunks to save
        csv_path (str): Path to save CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        df = pd.DataFrame(chunks)
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(chunks)} chunks to {csv_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving chunks to CSV: {str(e)}")
        return False


def load_data_from_csv(csv_path):
    """
    Load data from CSV file into ChromaDB.
    
    Args:
        csv_path (str): Path to CSV file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Loading data from CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Convert DataFrame to chunks format
        chunks = []
        for _, row in df.iterrows():
            chunks.append({
                'id': int(row['id']),
                'text': row['text'],
                'page_num': int(row['page_num']),
                'ang_number': int(row['ang_number']) if not pd.isna(row['ang_number']) else None,
                'raag': row['raag'] if not pd.isna(row['raag']) else None,
                'section': row['section'] if not pd.isna(row['section']) else None,
                'prev_chunk_id': int(row['prev_chunk_id']) if not pd.isna(row['prev_chunk_id']) else None,
                'next_chunk_id': int(row['next_chunk_id']) if not pd.isna(row['next_chunk_id']) else None
            })
        
        # Load chunks to ChromaDB
        success = load_chunks_to_chromadb(chunks)
        return success
    except Exception as e:
        logger.error(f"Error loading data from CSV: {str(e)}")
        return False


def process():
    """
    Main processing function that handles the full data processing pipeline.
    """
    try:
        # Check if CSV exists
        if os.path.exists(CSV_PATH):
            logger.info(f"CSV file exists: {CSV_PATH}")
            # Load data from CSV
            load_data_from_csv(CSV_PATH)
        else:
            # Check if PDF exists
            if os.path.exists(PDF_PATH):
                logger.info(f"PDF file exists: {PDF_PATH}")
                # Process PDF
                chunks = preprocess_gurbani_pdf(PDF_PATH)
                # Save to CSV
                save_chunks_to_csv(chunks, CSV_PATH)
                # Load to ChromaDB
                load_chunks_to_chromadb(chunks)
            else:
                logger.error(f"Neither CSV nor PDF file exists. Please provide at least one of them.")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error in processing pipeline: {str(e)}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run processing
    success = process()
    
    if success:
        logger.info("Processing completed successfully")
    else:
        logger.error("Processing failed")