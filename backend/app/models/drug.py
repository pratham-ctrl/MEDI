"""Pydantic models for drug information"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DrugInteraction(BaseModel):
    """Drug interaction information"""
    drug_name: str
    severity: str  # mild, moderate, severe
    description: str


class SideEffect(BaseModel):
    """Side effect information"""
    effect: str
    severity: str  # common, rare, serious
    description: Optional[str] = None


class DrugInfo(BaseModel):
    """Complete drug information"""
    drug_id: int
    generic_name: str
    brand_names: List[str] = []
    category: Optional[str] = None
    uses: List[str] = []
    dosage_adult: Optional[str] = None
    dosage_pediatric: Optional[str] = None
    side_effects_common: List[SideEffect] = []
    side_effects_serious: List[SideEffect] = []
    drug_interactions: List[DrugInteraction] = []
    food_interactions: List[str] = []
    contraindications: List[str] = []
    precautions: List[str] = []
    pregnancy_category: Optional[str] = None
    storage_instructions: Optional[str] = None
    last_updated: datetime
    source: str = "CDSCO"
    
    class Config:
        json_schema_extra = {
            "example": {
                "drug_id": 1,
                "generic_name": "Metformin",
                "brand_names": ["Glucophage", "Glycomet"],
                "category": "Antidiabetic",
                "uses": ["Type 2 Diabetes", "PCOS"],
                "dosage_adult": "500-2550mg daily in divided doses",
                "side_effects_common": [
                    {"effect": "Nausea", "severity": "common", "description": "Usually temporary"}
                ],
                "pregnancy_category": "B",
                "source": "CDSCO"
            }
        }


class DrugSearch(BaseModel):
    """Drug search request"""
    query: str = Field(..., min_length=2)
    limit: int = Field(default=10, ge=1, le=50)


class DrugSearchResult(BaseModel):
    """Drug search result item"""
    drug_id: int
    generic_name: str
    brand_names: List[str]
    category: Optional[str]
    relevance_score: float = Field(ge=0.0, le=1.0)


class DrugSearchResponse(BaseModel):
    """Drug search response"""
    query: str
    total_results: int
    results: List[DrugSearchResult]
    from_cache: bool = False


class DrugDetailRequest(BaseModel):
    """Request for detailed drug information"""
    drug_id: Optional[int] = None
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None


class DrugComparisonRequest(BaseModel):
    """Request to compare multiple drugs"""
    drug_ids: List[int] = Field(..., min_items=2, max_items=5)


class DrugComparisonResponse(BaseModel):
    """Drug comparison response"""
    drugs: List[DrugInfo]
    common_uses: List[str]
    interaction_warnings: List[str]

