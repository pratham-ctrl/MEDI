"""Drug lookup API routes"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.models.drug import DrugInfo, DrugSearchResult
from app.agents.drug_agent import get_drug_agent
from app.services.sql_database import get_sql_service
from app.services.redis_cache import get_redis_service
from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=List[DrugSearchResult])
async def search_drugs(
    q: str = Query(..., min_length=2, description="Search query for medicine name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for drugs by name
    
    Args:
        q: Search query
        limit: Maximum results
        current_user: Authenticated user
    
    Returns:
        List of matching drugs
    """
    try:
        logger.info(f"Drug search: {q}")
        
        # Check cache first
        redis_service = get_redis_service()
        cached = redis_service.get_cached_drug_search(q)
        if cached:
            logger.debug(f"Drug search cache hit: {q}")
            return cached[:limit]
        
        # Search SQL database
        sql_service = get_sql_service()
        drugs = sql_service.search_drugs(q, limit)
        
        results = [
            DrugSearchResult(
                drug_id=drug["drug_id"],
                generic_name=drug["generic_name"],
                brand_names=drug.get("brand_names", []),
                category=drug.get("category", ""),
                uses_summary=drug.get("uses", "")[:200] + "..." if len(drug.get("uses", "")) > 200 else drug.get("uses", "")
            )
            for drug in drugs
        ]
        
        # Cache results
        redis_service.cache_drug_search(q, results)
        
        logger.info(f"Found {len(results)} drugs for query: {q}")
        return results
        
    except Exception as e:
        logger.error(f"Error searching drugs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching drugs"
        )


@router.get("/{drug_id}", response_model=DrugInfo)
async def get_drug_info(
    drug_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed drug information by ID
    
    Args:
        drug_id: Drug identifier
        current_user: Authenticated user
    
    Returns:
        Detailed drug information
    """
    try:
        logger.info(f"Get drug info: {drug_id}")
        
        # Check cache
        redis_service = get_redis_service()
        cached = redis_service.get_cached_drug_info_by_id(drug_id)
        if cached:
            logger.debug(f"Drug info cache hit: {drug_id}")
            return DrugInfo(**cached)
        
        # Get from SQL
        sql_service = get_sql_service()
        drug = sql_service.get_drug_info(drug_id)
        
        if not drug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Drug not found"
            )
        
        drug_info = DrugInfo(
            drug_id=drug["drug_id"],
            generic_name=drug["generic_name"],
            brand_names=drug.get("brand_names", []),
            category=drug.get("category", ""),
            uses=drug.get("uses", ""),
            dosage_adult=drug.get("dosage_adult", ""),
            dosage_child=drug.get("dosage_child"),
            side_effects_common=drug.get("side_effects_common", []),
            side_effects_serious=drug.get("side_effects_serious", []),
            drug_interactions=drug.get("drug_interactions", []),
            contraindications=drug.get("contraindications", []),
            pregnancy_category=drug.get("pregnancy_category"),
            warnings=drug.get("warnings", []),
            storage=drug.get("storage"),
            last_updated=drug.get("last_updated")
        )
        
        # Cache
        redis_service.cache_drug_info_by_id(drug_id, drug_info.dict())
        
        logger.info(f"Retrieved drug info: {drug['generic_name']}")
        return drug_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving drug information"
        )


@router.get("/detailed/{drug_name}")
async def get_drug_detailed(
    drug_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive drug information using Drug Agent
    This uses both SQL and RAG for complete information
    
    Args:
        drug_name: Medicine name
        current_user: Authenticated user
    
    Returns:
        Detailed drug information with AI-generated response
    """
    try:
        logger.info(f"Get detailed drug info via agent: {drug_name}")
        
        # Call Drug Agent
        drug_agent = get_drug_agent()
        query = f"Tell me about {drug_name}"
        response = await drug_agent.process(query, {"user_id": current_user["user_id"]})
        
        return {
            "drug_name": drug_name,
            "information": response["content"],
            "sources": response.get("sources", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed drug info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving detailed drug information"
        )

