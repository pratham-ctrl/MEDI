"""Pydantic models for document processing"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Document type enumeration"""
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    MEDICAL_BILL = "medical_bill"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MedicineInfo(BaseModel):
    """Extracted medicine information"""
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Metformin",
                "generic_name": "Metformin HCl",
                "dosage": "500mg",
                "frequency": "BD (twice daily)",
                "duration": "30 days",
                "instructions": "Take after meals",
                "confidence": 0.95
            }
        }


class ExtractedData(BaseModel):
    """Complete extracted data from document"""
    medicines: List[MedicineInfo] = []
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescription_date: Optional[str] = None
    patient_name: Optional[str] = None
    diagnosis: Optional[str] = None
    additional_notes: Optional[str] = None
    overall_confidence: float = Field(ge=0.0, le=1.0)


class DocumentUpload(BaseModel):
    """Document upload response"""
    job_id: str
    status: DocumentStatus
    message: str
    estimated_time_seconds: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "doc_123abc",
                "status": "processing",
                "message": "Document uploaded successfully, processing started",
                "estimated_time_seconds": 10
            }
        }


# Alias for backwards compatibility
DocumentUploadResponse = DocumentUpload


class DocumentProcessingStatus(BaseModel):
    """Document processing status"""
    document_id: str
    status: DocumentStatus
    progress: int = Field(ge=0, le=100, default=0)
    message: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    """Document analysis response"""
    document_id: str
    status: DocumentStatus
    extracted_data: Optional[ExtractedData] = None
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class DocumentAnalysis(BaseModel):
    """Complete document analysis result"""
    document_id: str
    user_id: str
    document_type: DocumentType
    file_name: str
    file_size_bytes: int
    upload_date: datetime
    status: DocumentStatus
    extracted_data: Optional[ExtractedData] = None
    raw_blob_url: str
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "user_id": "user_456",
                "document_type": "prescription",
                "file_name": "prescription_2025-10-17.jpg",
                "file_size_bytes": 2458624,
                "upload_date": "2025-10-17T10:00:00Z",
                "status": "completed",
                "extracted_data": {
                    "medicines": [],
                    "doctor_name": "Dr. Sharma",
                    "overall_confidence": 0.92
                },
                "raw_blob_url": "https://storage.blob.core.windows.net/...",
                "processing_time_ms": 8450
            }
        }


class DocumentStatusResponse(BaseModel):
    """Document processing status response"""
    job_id: str
    status: DocumentStatus
    progress: int = Field(ge=0, le=100)  # Percentage
    result: Optional[DocumentAnalysis] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "doc_123abc",
                "status": "processing",
                "progress": 65,
                "result": None
            }
        }


class DocumentListItem(BaseModel):
    """Document list item for user's documents"""
    document_id: str
    file_name: str
    document_type: DocumentType
    upload_date: datetime
    status: DocumentStatus
    medicine_count: int
    confidence: float


class DocumentListResponse(BaseModel):
    """List of user's documents"""
    user_id: str
    total_count: int
    documents: List[DocumentListItem]

