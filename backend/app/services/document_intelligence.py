"""Azure Document Intelligence Service for OCR and document analysis"""

import logging
from typing import Dict, Any, BinaryIO
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentIntelligenceService:
    """Singleton service for Azure Document Intelligence operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance
    
    def __init__(self):
        """Initialize Document Intelligence client"""
        if self._client is None:
            self._client = DocumentAnalysisClient(
                endpoint=settings.DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.DOCUMENT_INTELLIGENCE_KEY)
            )
            logger.info("Document Intelligence client initialized")
    
    def analyze_document(
        self,
        document: BinaryIO,
        model_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze a document using Azure Document Intelligence
        
        Args:
            document: File-like object containing the document
            model_id: Model ID to use (defaults to prebuilt-read)
        
        Returns:
            Extracted document data
        """
        if model_id is None:
            model_id = settings.DOCUMENT_INTELLIGENCE_MODEL_ID
        
        try:
            poller = self._client.begin_analyze_document(
                model_id=model_id,
                document=document
            )
            
            result = poller.result()
            logger.info(f"Document analysis completed with {len(result.pages)} pages")
            
            return self._process_result(result)
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    def analyze_document_from_url(
        self,
        document_url: str,
        model_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze a document from URL using Azure Document Intelligence
        
        Args:
            document_url: URL of the document
            model_id: Model ID to use (defaults to prebuilt-read)
        
        Returns:
            Extracted document data
        """
        if model_id is None:
            model_id = settings.DOCUMENT_INTELLIGENCE_MODEL_ID
        
        try:
            poller = self._client.begin_analyze_document_from_url(
                model_id=model_id,
                document_url=document_url
            )
            
            result = poller.result()
            logger.info(f"Document analysis from URL completed")
            
            return self._process_result(result)
            
        except Exception as e:
            logger.error(f"Error analyzing document from URL: {str(e)}")
            raise
    
    def _process_result(self, result) -> Dict[str, Any]:
        """
        Process Document Intelligence result into structured format
        
        Args:
            result: AnalyzeResult object from Document Intelligence
        
        Returns:
            Structured dictionary with extracted data
        """
        extracted_data = {
            "full_text": "",
            "pages": [],
            "tables": [],
            "key_value_pairs": {},
            "confidence_scores": []
        }
        
        # Extract text from all pages
        for page in result.pages:
            page_text = []
            page_info = {
                "page_number": page.page_number,
                "width": page.width,
                "height": page.height,
                "lines": []
            }
            
            # Extract lines
            if hasattr(page, 'lines'):
                for line in page.lines:
                    line_text = line.content
                    page_text.append(line_text)
                    page_info["lines"].append({
                        "text": line_text,
                        "confidence": line.confidence if hasattr(line, 'confidence') else 1.0
                    })
                    extracted_data["confidence_scores"].append(
                        line.confidence if hasattr(line, 'confidence') else 1.0
                    )
            
            page_content = "\n".join(page_text)
            extracted_data["full_text"] += page_content + "\n\n"
            extracted_data["pages"].append(page_info)
        
        # Extract tables
        if hasattr(result, 'tables'):
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "confidence": cell.confidence if hasattr(cell, 'confidence') else 1.0
                    })
                
                extracted_data["tables"].append(table_data)
        
        # Extract key-value pairs (if available)
        if hasattr(result, 'key_value_pairs'):
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key = kv_pair.key.content
                    value = kv_pair.value.content
                    extracted_data["key_value_pairs"][key] = value
        
        # Calculate overall confidence
        if extracted_data["confidence_scores"]:
            overall_confidence = sum(extracted_data["confidence_scores"]) / len(extracted_data["confidence_scores"])
            extracted_data["overall_confidence"] = round(overall_confidence, 3)
        else:
            extracted_data["overall_confidence"] = 0.0
        
        return extracted_data
    
    def extract_prescription_data(
        self,
        document: BinaryIO
    ) -> Dict[str, Any]:
        """
        Extract prescription-specific data from a document
        This is a specialized method that processes OCR results to extract medicines, dosage, etc.
        
        Args:
            document: File-like object containing the prescription
        
        Returns:
            Structured prescription data
        """
        # First, perform standard OCR
        ocr_result = self.analyze_document(document)
        
        # Extract prescription-specific fields
        prescription_data = {
            "medicines": [],
            "doctor_name": None,
            "hospital_name": None,
            "prescription_date": None,
            "patient_name": None,
            "diagnosis": None,
            "additional_notes": None,
            "overall_confidence": ocr_result.get("overall_confidence", 0.0)
        }
        
        # Parse the text to extract structured information
        # This is a simplified version - in production, use custom trained models
        full_text = ocr_result.get("full_text", "")
        lines = full_text.split("\n")
        
        # Look for common patterns (this is basic - enhance with NLP/regex)
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Extract doctor name
            if "dr." in line_lower or "doctor" in line_lower:
                if not prescription_data["doctor_name"]:
                    prescription_data["doctor_name"] = line.strip()
            
            # Extract diagnosis
            if "diagnosis:" in line_lower or "dx:" in line_lower:
                prescription_data["diagnosis"] = line.split(":", 1)[1].strip() if ":" in line else None
            
            # Look for medicine patterns (very basic - needs enhancement)
            # In production, use custom model trained on Indian prescriptions
            if any(indicator in line_lower for indicator in ["tab", "cap", "syrup", "mg", "ml"]):
                # This is a potential medicine line
                medicine = {
                    "name": line.strip(),
                    "dosage": None,
                    "frequency": None,
                    "confidence": ocr_result.get("overall_confidence", 0.0)
                }
                prescription_data["medicines"].append(medicine)
        
        logger.info(f"Extracted {len(prescription_data['medicines'])} medicines from prescription")
        
        return prescription_data


# Global service instance
_document_service = None


def get_document_service() -> DocumentIntelligenceService:
    """Get or create the global Document Intelligence service instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentIntelligenceService()
    return _document_service

