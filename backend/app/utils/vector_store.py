"""Blob Storage Vector Store for RAG operations"""

import logging
import json
import numpy as np
import io
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.services.blob_storage import get_blob_service
from app.services.azure_openai import get_openai_service
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""
    document_id: str
    chunk_index: int
    content: str
    similarity_score: float
    metadata: Dict[str, Any]


class BlobVectorStore:
    """
    Vector store implementation using Azure Blob Storage
    Stores embeddings as .npy files with metadata JSON files
    """
    
    def __init__(self, container_name: str):
        """
        Initialize vector store
        
        Args:
            container_name: Blob container name (e.g., 'medical-knowledge')
        """
        self.container_name = container_name
        self.blob_service = get_blob_service()
        self.openai_service = get_openai_service()
        logger.info(f"Vector store initialized for container: {container_name}")
    
    def store_document_embeddings(
        self,
        document_id: str,
        text_chunks: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Store document embeddings in blob storage
        
        Args:
            document_id: Unique document identifier
            text_chunks: List of text chunks to embed
            metadata: Optional metadata about the document
            user_id: Optional user ID (for user-specific documents)
        
        Returns:
            Blob URL of stored embeddings
        """
        try:
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(text_chunks)} chunks")
            embeddings = self.openai_service.generate_embeddings(text_chunks)
            
            # Convert to numpy array for efficient storage
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Create blob path
            if user_id:
                blob_prefix = f"{user_id}/{document_id}"
            else:
                blob_prefix = document_id
            
            # Store embeddings as .npy file
            embeddings_blob_name = f"{blob_prefix}_embeddings.npy"
            embeddings_bytes = io.BytesIO()
            np.save(embeddings_bytes, embeddings_array)
            embeddings_bytes.seek(0)
            
            embeddings_url = self.blob_service.upload_file(
                container_name=self.container_name,
                blob_name=embeddings_blob_name,
                data=embeddings_bytes,
                content_type="application/octet-stream"
            )
            
            # Store metadata and chunks
            metadata_blob_name = f"{blob_prefix}_metadata.json"
            metadata_content = {
                "document_id": document_id,
                "user_id": user_id,
                "num_chunks": len(text_chunks),
                "chunks": text_chunks,
                "embedding_dimension": settings.EMBEDDING_DIMENSION,
                "metadata": metadata or {}
            }
            
            metadata_bytes = json.dumps(metadata_content, indent=2).encode('utf-8')
            self.blob_service.upload_bytes(
                container_name=self.container_name,
                blob_name=metadata_blob_name,
                data=metadata_bytes
            )
            
            logger.info(f"Stored embeddings for document: {document_id}")
            return embeddings_url
            
        except Exception as e:
            logger.error(f"Error storing document embeddings: {str(e)}")
            raise
    
    def search_similar(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        min_similarity: float = 0.0
    ) -> List[VectorSearchResult]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            user_id: Optional user ID to filter results
            min_similarity: Minimum similarity score threshold
        
        Returns:
            List of VectorSearchResult objects
        """
        try:
            # Generate query embedding
            logger.debug(f"Generating query embedding for: {query[:50]}...")
            query_embeddings = self.openai_service.generate_embeddings([query])
            query_vector = np.array(query_embeddings[0], dtype=np.float32)
            
            # List all embedding files in container
            prefix = f"{user_id}/" if user_id else None
            blob_list = self.blob_service.list_blobs(
                container_name=self.container_name,
                prefix=prefix
            )
            
            # Filter for embedding files only
            embedding_blobs = [b for b in blob_list if b.endswith('_embeddings.npy')]
            
            if not embedding_blobs:
                logger.warning(f"No embeddings found in container: {self.container_name}")
                return []
            
            # Calculate similarities
            results = []
            for embedding_blob in embedding_blobs:
                try:
                    # Load embeddings
                    embeddings_bytes = self.blob_service.download_file(
                        container_name=self.container_name,
                        blob_name=embedding_blob
                    )
                    embeddings_array = np.load(io.BytesIO(embeddings_bytes))
                    
                    # Calculate cosine similarities
                    similarities = self._cosine_similarity(query_vector, embeddings_array)
                    
                    # Load metadata
                    metadata_blob = embedding_blob.replace('_embeddings.npy', '_metadata.json')
                    metadata_bytes = self.blob_service.download_file(
                        container_name=self.container_name,
                        blob_name=metadata_blob
                    )
                    metadata = json.loads(metadata_bytes.decode('utf-8'))
                    
                    # Create results for each chunk
                    for chunk_idx, similarity in enumerate(similarities):
                        if similarity >= min_similarity:
                            results.append(VectorSearchResult(
                                document_id=metadata['document_id'],
                                chunk_index=chunk_idx,
                                content=metadata['chunks'][chunk_idx],
                                similarity_score=float(similarity),
                                metadata=metadata.get('metadata', {})
                            ))
                    
                except Exception as e:
                    logger.warning(f"Error processing blob {embedding_blob}: {str(e)}")
                    continue
            
            # Sort by similarity and return top-k
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            top_results = results[:top_k]
            
            logger.info(f"Found {len(top_results)} similar chunks (top-{top_k})")
            return top_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise
    
    def delete_document(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete document embeddings and metadata
        
        Args:
            document_id: Document identifier
            user_id: Optional user ID
        
        Returns:
            True if deleted successfully
        """
        try:
            blob_prefix = f"{user_id}/{document_id}" if user_id else document_id
            
            # Delete embeddings file
            embeddings_blob = f"{blob_prefix}_embeddings.npy"
            self.blob_service.delete_file(self.container_name, embeddings_blob)
            
            # Delete metadata file
            metadata_blob = f"{blob_prefix}_metadata.json"
            self.blob_service.delete_file(self.container_name, metadata_blob)
            
            logger.info(f"Deleted document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def list_documents(
        self,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents in the vector store
        
        Args:
            user_id: Optional user ID to filter results
        
        Returns:
            List of document metadata
        """
        try:
            prefix = f"{user_id}/" if user_id else None
            blob_list = self.blob_service.list_blobs(
                container_name=self.container_name,
                prefix=prefix
            )
            
            # Filter for metadata files
            metadata_blobs = [b for b in blob_list if b.endswith('_metadata.json')]
            
            documents = []
            for metadata_blob in metadata_blobs:
                try:
                    metadata_bytes = self.blob_service.download_file(
                        container_name=self.container_name,
                        blob_name=metadata_blob
                    )
                    metadata = json.loads(metadata_bytes.decode('utf-8'))
                    documents.append(metadata)
                except Exception as e:
                    logger.warning(f"Error loading metadata {metadata_blob}: {str(e)}")
                    continue
            
            logger.debug(f"Listed {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    @staticmethod
    def _cosine_similarity(
        query_vector: np.ndarray,
        document_vectors: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity between query and document vectors
        
        Args:
            query_vector: Query embedding (1D array)
            document_vectors: Document embeddings (2D array)
        
        Returns:
            Array of similarity scores
        """
        # Normalize vectors
        query_norm = query_vector / np.linalg.norm(query_vector)
        doc_norms = document_vectors / np.linalg.norm(document_vectors, axis=1, keepdims=True)
        
        # Calculate dot product (cosine similarity)
        similarities = np.dot(doc_norms, query_norm)
        
        return similarities


# Pre-configured vector stores for different domains
def get_medical_knowledge_store() -> BlobVectorStore:
    """Get vector store for medical knowledge (WHO, ICMR)"""
    return BlobVectorStore(settings.BLOB_CONTAINER_MEDICAL_KNOWLEDGE)


def get_drug_database_store() -> BlobVectorStore:
    """Get vector store for drug database"""
    return BlobVectorStore(settings.BLOB_CONTAINER_DRUG_DATABASE)


def get_user_documents_store() -> BlobVectorStore:
    """Get vector store for user documents"""
    return BlobVectorStore(settings.BLOB_CONTAINER_PRESCRIPTIONS_VECTORS)

