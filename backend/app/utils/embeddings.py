"""Embedding generation utilities"""

import logging
from typing import List
from app.services.azure_openai import get_openai_service
from app.config import settings

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = None,
    overlap: int = None
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to chunk
        chunk_size: Number of words per chunk (default from settings)
        overlap: Number of overlapping words (default from settings)
    
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap is None:
        overlap = settings.CHUNK_OVERLAP
    
    # Split into words
    words = text.split()
    
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        chunks.append(chunk_text)
        
        # Move start position with overlap
        start = end - overlap
        
        # Break if we've covered all words
        if end >= len(words):
            break
    
    logger.debug(f"Chunked text into {len(chunks)} chunks")
    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts
    
    Args:
        texts: List of text strings
    
    Returns:
        List of embedding vectors
    """
    openai_service = get_openai_service()
    return openai_service.generate_embeddings(texts)


async def agenerate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings asynchronously
    
    Args:
        texts: List of text strings
    
    Returns:
        List of embedding vectors
    """
    openai_service = get_openai_service()
    return await openai_service.agenerate_embeddings(texts)


def batch_generate_embeddings(
    texts: List[str],
    batch_size: int = 16
) -> List[List[float]]:
    """
    Generate embeddings in batches for large text lists
    
    Args:
        texts: List of text strings
        batch_size: Number of texts per batch
    
    Returns:
        List of embedding vectors
    """
    openai_service = get_openai_service()
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = openai_service.generate_embeddings(batch)
        all_embeddings.extend(batch_embeddings)
        logger.debug(f"Generated embeddings for batch {i//batch_size + 1}")
    
    return all_embeddings


def prepare_document_for_vectorization(
    text: str,
    chunk_size: int = None,
    overlap: int = None
) -> List[str]:
    """
    Prepare a document for vectorization by cleaning and chunking
    
    Args:
        text: Document text
        chunk_size: Words per chunk
        overlap: Overlapping words
    
    Returns:
        List of cleaned and chunked text
    """
    # Clean text
    text = text.strip()
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Chunk text
    chunks = chunk_text(text, chunk_size, overlap)
    
    logger.info(f"Prepared document: {len(chunks)} chunks from {len(text)} characters")
    return chunks

