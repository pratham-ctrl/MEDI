"""Setup Cosmos DB containers"""

import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cosmos_db import get_cosmos_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_containers():
    """Verify that Cosmos DB containers are set up"""
    logger.info("Verifying Cosmos DB containers...")
    
    try:
        # Just initializing the service will create containers if they don't exist
        cosmos_service = get_cosmos_service()
        logger.info("✅ All Cosmos DB containers verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying containers: {str(e)}")
        return False


def main():
    """Main function to setup Cosmos DB"""
    logger.info("Starting Cosmos DB setup...")
    logger.info(f"Database: {settings.COSMOS_DATABASE}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Verify containers (they're auto-created on service initialization)
    if not verify_containers():
        logger.error("Failed to verify Cosmos DB containers")
        return False
    
    logger.info("✅ Cosmos DB setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

