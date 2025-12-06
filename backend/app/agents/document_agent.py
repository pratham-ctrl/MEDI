"""Document Agent for prescription analysis"""

import logging
import uuid
from typing import Dict, Any, Optional, BinaryIO
from app.services.document_intelligence import get_document_service
from app.services.blob_storage import get_blob_service
from app.services.sql_database import get_sql_service
from app.utils.vector_store import get_user_documents_store
from app.utils.embeddings import prepare_document_for_vectorization, generate_embeddings
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentAgent:
    """
    Document Agent - Analyzes medical documents and prescriptions
    Uses Azure Document Intelligence for OCR
    """
    
    def __init__(self):
        self.document_service = get_document_service()
        self.blob_service = get_blob_service()
        self.sql_service = get_sql_service()
        self.vector_store = get_user_documents_store()
        logger.info("Document Agent initialized")
    
    async def process_document(
        self,
        document: BinaryIO,
        user_id: str,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Process an uploaded medical document
        
        Args:
            document: File object
            user_id: User identifier
            filename: Original filename
            content_type: MIME type
        
        Returns:
            Dict with extraction results
        """
        try:
            logger.info(f"Processing document for user {user_id}: {filename}")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Step 1: Save raw document to Blob Storage
            blob_name = f"{user_id}/{document_id}_{filename}"
            document.seek(0)  # Reset file pointer
            blob_url = self.blob_service.upload_file(
                container_name=settings.BLOB_CONTAINER_PRESCRIPTIONS_UPLOADS,
                blob_name=blob_name,
                data=document,
                metadata={"user_id": user_id, "filename": filename},
                content_type=content_type
            )
            
            logger.info(f"Saved raw document to blob: {blob_url}")
            
            # Step 2: Perform OCR and extraction
            document.seek(0)
            extracted_data = self.document_service.extract_prescription_data(document)
            
            logger.info(f"OCR completed with confidence: {extracted_data['overall_confidence']}")
            
            # Step 3: Save to SQL database
            prescription_id = self.sql_service.save_prescription(
                prescription_id=document_id,
                user_id=user_id,
                document_blob_url=blob_url,
                extracted_data=extracted_data,
                ocr_confidence=extracted_data["overall_confidence"]
            )
            
            # Step 4: Generate and store embeddings
            if extracted_data.get("full_text"):
                await self._store_embeddings(
                    document_id=document_id,
                    user_id=user_id,
                    text=extracted_data["full_text"],
                    metadata=extracted_data
                )
            
            # Step 5: Format response
            response = {
                "document_id": document_id,
                "status": "completed",
                "extracted_data": {
                    "medicines": extracted_data.get("medicines", []),
                    "doctor_name": extracted_data.get("doctor_name"),
                    "prescription_date": extracted_data.get("prescription_date"),
                    "diagnosis": extracted_data.get("diagnosis")
                },
                "confidence": extracted_data["overall_confidence"],
                "blob_url": blob_url,
                "needs_review": extracted_data["overall_confidence"] < settings.OCR_CONFIDENCE_THRESHOLD
            }
            
            logger.info(f"Document processing completed: {document_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    async def _store_embeddings(
        self,
        document_id: str,
        user_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """Store document embeddings in vector store"""
        try:
            # Prepare text for vectorization
            chunks = prepare_document_for_vectorization(text)
            
            # Store in vector store
            self.vector_store.store_document_embeddings(
                document_id=document_id,
                text_chunks=chunks,
                metadata=metadata,
                user_id=user_id
            )
            
            logger.info(f"Stored embeddings for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            # Don't fail the entire process if embedding storage fails
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID from SQL"""
        try:
            return self.sql_service.get_prescription(document_id)
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
    
    def list_user_documents(
        self,
        user_id: str,
        limit: int = 50
    ) -> list:
        """List all documents for a user"""
        try:
            return self.sql_service.list_user_prescriptions(user_id, limit)
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []


# Global agent instance
_document_agent = None


def get_document_agent() -> DocumentAgent:
    """Get or create the global Document agent instance"""
    global _document_agent
    if _document_agent is None:
        _document_agent = DocumentAgent()
    return _document_agent

