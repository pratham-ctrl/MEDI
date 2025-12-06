"""Document management API routes"""

import logging
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
from app.models.document import (
    DocumentUploadResponse,
    DocumentProcessingStatus,
    DocumentAnalysisResponse,
    DocumentListItem
)
from app.agents.document_agent import get_document_agent
from app.api.dependencies import get_current_user, validate_file_upload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a medical document (prescription, report)
    
    Args:
        file: Uploaded file
        current_user: Authenticated user
    
    Returns:
        Upload response with job_id for tracking
    """
    try:
        logger.info(f"Document upload from user {current_user['user_id']}: {file.filename}")
        
        # Validate file
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        await validate_file_upload(file.content_type, file_size)
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Process document (async in production, sync for now)
        document_agent = get_document_agent()
        
        # Reset file pointer and process
        import io
        file_obj = io.BytesIO(content)
        
        result = await document_agent.process_document(
            document=file_obj,
            user_id=current_user["user_id"],
            filename=file.filename,
            content_type=file.content_type
        )
        
        logger.info(f"Document processed: {result['document_id']}")
        
        return DocumentUploadResponse(
            job_id=job_id,
            document_id=result["document_id"],
            status="completed",
            message="Document uploaded and processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=DocumentProcessingStatus)
async def get_processing_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get document processing status
    
    Args:
        job_id: Job identifier
        current_user: Authenticated user
    
    Returns:
        Processing status and results
    """
    # TODO: Implement async job tracking with Redis
    # For now, return completed status
    return DocumentProcessingStatus(
        job_id=job_id,
        status="completed",
        progress=100,
        message="Processing completed"
    )


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Synchronous document analysis for immediate results
    Used by frontend page 4 for document analysis
    
    Args:
        file: Uploaded file
        current_user: Authenticated user
    
    Returns:
        Detailed analysis results
    """
    try:
        logger.info(f"Synchronous analysis from user {current_user['user_id']}: {file.filename}")
        
        # Validate file
        content = await file.read()
        await validate_file_upload(file.content_type, len(content))
        
        # Process document
        document_agent = get_document_agent()
        
        import io
        file_obj = io.BytesIO(content)
        
        result = await document_agent.process_document(
            document=file_obj,
            user_id=current_user["user_id"],
            filename=file.filename,
            content_type=file.content_type
        )
        
        return DocumentAnalysisResponse(
            document_id=result["document_id"],
            extracted_data=result["extracted_data"],
            confidence=result["confidence"],
            needs_review=result["needs_review"],
            blob_url=result["blob_url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentAnalysisResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get document by ID
    
    Args:
        document_id: Document identifier
        current_user: Authenticated user
    
    Returns:
        Document details and extracted data
    """
    try:
        document_agent = get_document_agent()
        document = document_agent.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify ownership
        if document["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return DocumentAnalysisResponse(
            document_id=document["prescription_id"],
            extracted_data=document["extracted_data"],
            confidence=document["ocr_confidence"],
            needs_review=document["ocr_confidence"] < 0.75,
            blob_url=document["document_blob_url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving document"
        )


@router.get("/", response_model=List[DocumentListItem])
async def list_documents(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    List user's documents
    
    Args:
        current_user: Authenticated user
        limit: Maximum number of documents to return
    
    Returns:
        List of documents
    """
    try:
        document_agent = get_document_agent()
        documents = document_agent.list_user_documents(
            user_id=current_user["user_id"],
            limit=limit
        )
        
        return [
            DocumentListItem(
                document_id=doc["prescription_id"],
                filename=doc.get("filename", "Unknown"),
                upload_date=doc["upload_date"],
                confidence=doc["ocr_confidence"],
                medicines_count=len(doc.get("extracted_data", {}).get("medicines", []))
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing documents"
        )

