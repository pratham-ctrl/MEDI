"""Create required blob storage containers"""

import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.blob_storage import get_blob_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_containers():
    """Create all required blob containers"""
    
    blob_service = get_blob_service()
    
    containers = [
        "prescription-vectors",
        "medical-knowledge", 
        "drug-database"
    ]
    
    for container_name in containers:
        try:
            blob_service.create_container(container_name)
            logger.info(f"✅ Created container: {container_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Container already exists: {container_name}")
            else:
                logger.error(f"Error creating {container_name}: {str(e)}")
                return False
    
    return True


def main():
    """Main function"""
    logger.info("Creating blob storage containers...")
    logger.info(f"Storage Account: {settings.AZURE_STORAGE_CONNECTION_STRING[:50]}...")
    
    if create_containers():
        logger.info("✅ All blob containers created successfully!")
        return True
    else:
        logger.error("Failed to create some containers")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

