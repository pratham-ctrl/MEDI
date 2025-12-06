"""Azure Blob Storage Service for document and vector storage"""

import logging
import io
from typing import Optional, BinaryIO, Dict
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError
from app.config import settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Singleton service for Azure Blob Storage operations"""
    
    _instance = None
    _blob_service_client: Optional[BlobServiceClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Blob Storage client"""
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(
                settings.STORAGE_CONNECTION_STRING
            )
            logger.info("Blob Storage client initialized")
            self._ensure_containers_exist()
    
    def _ensure_containers_exist(self):
        """Ensure all required containers exist"""
        containers = [
            settings.BLOB_CONTAINER_PRESCRIPTIONS_UPLOADS,
            settings.BLOB_CONTAINER_PRESCRIPTIONS_VECTORS,
            settings.BLOB_CONTAINER_MEDICAL_KNOWLEDGE,
            settings.BLOB_CONTAINER_DRUG_DATABASE,
        ]
        
        for container_name in containers:
            try:
                container_client = self._blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    logger.info(f"Created container: {container_name}")
            except Exception as e:
                logger.warning(f"Error ensuring container {container_name}: {str(e)}")
    
    def upload_file(
        self,
        container_name: str,
        blob_name: str,
        data: BinaryIO,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to Blob Storage
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
            data: File-like object or bytes
            metadata: Optional metadata dict
            content_type: Optional content type (e.g., 'image/jpeg')
        
        Returns:
            Blob URL
        """
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Upload with metadata
            blob_client.upload_blob(
                data,
                metadata=metadata,
                content_settings=ContentSettings(content_type=content_type) if content_type else None,
                overwrite=True
            )
            
            logger.info(f"Uploaded blob: {container_name}/{blob_name}")
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {str(e)}")
            raise
    
    def download_file(
        self,
        container_name: str,
        blob_name: str
    ) -> bytes:
        """
        Download a file from Blob Storage
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
        
        Returns:
            File contents as bytes
        """
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_data = blob_client.download_blob()
            content = blob_data.readall()
            
            logger.debug(f"Downloaded blob: {container_name}/{blob_name}")
            return content
            
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {container_name}/{blob_name}")
            raise
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {str(e)}")
            raise
    
    def delete_file(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Delete a file from Blob Storage
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
        
        Returns:
            True if deleted, False if not found
        """
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {container_name}/{blob_name}")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {container_name}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {str(e)}")
            raise
    
    def generate_sas_url(
        self,
        container_name: str,
        blob_name: str,
        expiry_hours: int = 1
    ) -> str:
        """
        Generate a Shared Access Signature URL for temporary access
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
            expiry_hours: Hours until expiration (default: 1)
        
        Returns:
            SAS URL string
        """
        try:
            sas_token = generate_blob_sas(
                account_name=settings.STORAGE_ACCOUNT_NAME,
                container_name=container_name,
                blob_name=blob_name,
                account_key=settings.STORAGE_ACCOUNT_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            sas_url = (
                f"https://{settings.STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
                f"{container_name}/{blob_name}?{sas_token}"
            )
            
            logger.debug(f"Generated SAS URL for {blob_name} (expires in {expiry_hours}h)")
            return sas_url
            
        except Exception as e:
            logger.error(f"Error generating SAS URL: {str(e)}")
            raise
    
    def list_blobs(
        self,
        container_name: str,
        prefix: Optional[str] = None
    ) -> list:
        """
        List blobs in a container
        
        Args:
            container_name: Name of the container
            prefix: Optional prefix to filter blobs (e.g., 'user_123/')
        
        Returns:
            List of blob names
        """
        try:
            container_client = self._blob_service_client.get_container_client(container_name)
            
            blob_list = []
            for blob in container_client.list_blobs(name_starts_with=prefix):
                blob_list.append(blob.name)
            
            logger.debug(f"Listed {len(blob_list)} blobs in {container_name}")
            return blob_list
            
        except Exception as e:
            logger.error(f"Error listing blobs in {container_name}: {str(e)}")
            raise
    
    def get_blob_metadata(
        self,
        container_name: str,
        blob_name: str
    ) -> Dict[str, str]:
        """
        Get metadata for a blob
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
        
        Returns:
            Dictionary of metadata
        """
        try:
            blob_client = self._blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            metadata = properties.metadata or {}
            
            logger.debug(f"Retrieved metadata for {blob_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting metadata for {blob_name}: {str(e)}")
            raise
    
    def upload_bytes(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload bytes directly to Blob Storage (helper for numpy arrays, etc.)
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob (file path)
            data: Raw bytes to upload
            metadata: Optional metadata dict
        
        Returns:
            Blob URL
        """
        return self.upload_file(
            container_name=container_name,
            blob_name=blob_name,
            data=io.BytesIO(data),
            metadata=metadata
        )


# Global service instance
_blob_service = None


def get_blob_service() -> BlobStorageService:
    """Get or create the global Blob Storage service instance"""
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobStorageService()
    return _blob_service

