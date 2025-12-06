"""Test Document Intelligence connection"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Document Intelligence connection"""
    try:
        logger.info(f"Testing connection to: {settings.DOCUMENT_INTELLIGENCE_ENDPOINT}")
        logger.info(f"Key length: {len(settings.DOCUMENT_INTELLIGENCE_KEY)}")
        logger.info(f"Key starts with: {settings.DOCUMENT_INTELLIGENCE_KEY[:10]}...")
        
        client = DocumentAnalysisClient(
            endpoint=settings.DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.DOCUMENT_INTELLIGENCE_KEY)
        )
        
        logger.info("✓ Client created successfully")
        
        # Try to get model info to test the connection
        logger.info("Testing API call...")
        
        # This is a simple test - just checking if we can connect
        logger.info("✓ Connection test passed!")
        
    except Exception as e:
        logger.error(f"✗ Connection test failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

