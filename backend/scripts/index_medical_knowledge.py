"""Index medical knowledge base (WHO, ICMR) to vector store"""

import logging
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.vector_store import get_medical_knowledge_store
from app.utils.embeddings import prepare_document_for_vectorization
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_medical_documents(data_dir: str):
    """
    Load medical documents from directory
    
    Args:
        data_dir: Directory containing medical documents
    
    Yields:
        Tuple of (document_id, content, metadata)
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return
    
    # Look for text files, PDFs, etc.
    for file_path in data_path.rglob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            document_id = file_path.stem
            metadata = {
                "filename": file_path.name,
                "source": "medical_knowledge",
                "type": "guideline"
            }
            
            yield document_id, content, metadata
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            continue


def index_sample_medical_knowledge():
    """Index sample medical knowledge (when no documents available)"""
    logger.info("Indexing sample medical knowledge...")
    
    vector_store = get_medical_knowledge_store()
    
    # Sample medical knowledge
    sample_documents = [
        {
            "id": "diabetes_management",
            "content": """
            Diabetes Mellitus Management Guidelines
            
            Type 2 Diabetes Management:
            - First-line treatment: Lifestyle modification (diet and exercise)
            - If HbA1c >6.5% after 3 months, start Metformin
            - Target HbA1c: <7% for most adults, <6.5% for younger without complications
            - Monitor blood glucose regularly
            - Annual screening for complications (retinopathy, nephropathy, neuropathy)
            
            Lifestyle Modifications:
            - 150 minutes moderate exercise per week
            - Reduce refined carbohydrates and sugars
            - Increase fiber intake
            - Maintain healthy weight (BMI 18.5-24.9)
            - Quit smoking
            
            Warning Signs:
            - Severe hypoglycemia: Confusion, sweating, shakiness
            - Hyperglycemia: Excessive thirst, frequent urination, blurred vision
            - Diabetic ketoacidosis: Fruity breath, nausea, abdominal pain
            
            Source: WHO Guidelines on Diabetes Management 2023
            """,
            "metadata": {"source": "WHO", "topic": "diabetes", "year": 2023}
        },
        {
            "id": "hypertension_guidelines",
            "content": """
            Hypertension Management Guidelines
            
            Blood Pressure Classification:
            - Normal: <120/80 mmHg
            - Elevated: 120-129/<80 mmHg
            - Stage 1 HTN: 130-139/80-89 mmHg
            - Stage 2 HTN: ≥140/90 mmHg
            
            Treatment Approach:
            - Stage 1: Lifestyle modification for 3-6 months
            - If no improvement or Stage 2: Start medication
            - First-line drugs: ACE inhibitors, ARBs, Calcium channel blockers, Diuretics
            
            Lifestyle Modifications:
            - DASH diet (Dietary Approaches to Stop Hypertension)
            - Reduce sodium to <2g/day
            - Regular exercise (30 min/day, 5 days/week)
            - Limit alcohol consumption
            - Stress management
            - Maintain healthy weight
            
            Monitoring:
            - Home blood pressure monitoring
            - Regular check-ups every 3-6 months
            - Annual kidney function tests
            
            Source: ICMR Guidelines for Hypertension 2023
            """,
            "metadata": {"source": "ICMR", "topic": "hypertension", "year": 2023}
        },
        {
            "id": "fever_management",
            "content": """
            Fever Management in Adults and Children
            
            Definition:
            - Fever: Body temperature >100.4°F (38°C)
            - High fever: >103°F (39.4°C)
            
            Common Causes:
            - Viral infections (cold, flu, COVID-19)
            - Bacterial infections (UTI, pneumonia)
            - Inflammatory conditions
            
            Home Management:
            - Rest and adequate sleep
            - Increase fluid intake (water, ORS, soup)
            - Paracetamol 500-1000mg every 4-6 hours for adults
            - Tepid sponging with lukewarm water
            - Light, comfortable clothing
            
            When to Seek Medical Attention:
            - Fever >103°F (39.4°C) lasting >3 days
            - Severe headache with stiff neck
            - Difficulty breathing
            - Persistent vomiting
            - Confusion or altered consciousness
            - Infants <3 months with any fever
            - Fever with rash
            
            Children Specific:
            - Paracetamol: 10-15mg/kg every 4-6 hours
            - Never give aspirin to children
            - Monitor for dehydration
            
            Source: WHO Guidelines on Fever Management
            """,
            "metadata": {"source": "WHO", "topic": "fever", "year": 2023}
        },
        {
            "id": "respiratory_infections",
            "content": """
            Respiratory Tract Infections Management
            
            Upper Respiratory Tract Infections (Common Cold):
            - Usually viral, self-limiting
            - Duration: 7-10 days
            - Treatment: Symptomatic relief
            - Paracetamol for fever/pain
            - Decongestants for nasal congestion
            - Adequate rest and fluids
            - Antibiotics NOT recommended unless bacterial infection confirmed
            
            Lower Respiratory Tract Infections (Bronchitis, Pneumonia):
            - May require antibiotics if bacterial
            - Seek medical attention if:
              * Difficulty breathing
              * Chest pain
              * High fever >102°F for >3 days
              * Coughing blood
              * Worsening symptoms
            
            Prevention:
            - Hand hygiene
            - Avoid close contact with sick people
            - Vaccination (flu, pneumococcal)
            - Avoid smoking and air pollution
            
            COVID-19 Considerations:
            - Get tested if symptoms present
            - Isolate if positive
            - Follow local health guidelines
            - Seek emergency care for severe symptoms
            
            Source: WHO Respiratory Infections Guidelines 2023
            """,
            "metadata": {"source": "WHO", "topic": "respiratory", "year": 2023}
        },
        {
            "id": "gastroenteritis",
            "content": """
            Gastroenteritis Management
            
            Symptoms:
            - Diarrhea (loose, watery stools)
            - Nausea and vomiting
            - Abdominal cramps
            - Low-grade fever
            - Dehydration signs
            
            Treatment:
            - Oral Rehydration Solution (ORS) - most important
            - Zinc supplementation for children
            - Continue normal diet when tolerated
            - BRAT diet: Bananas, Rice, Applesauce, Toast
            - Probiotics may help
            - Avoid dairy products temporarily
            
            Medications:
            - Generally avoid anti-diarrheal medications
            - Antibiotics only if bacterial infection confirmed
            - Antiemetics if severe vomiting
            
            Dehydration Signs:
            - Decreased urination
            - Dry mouth and tongue
            - Sunken eyes
            - Lethargy
            - In infants: Sunken fontanelle
            
            Seek Medical Attention:
            - Severe dehydration
            - Blood in stool
            - High fever >102°F
            - Symptoms lasting >3 days
            - Severe abdominal pain
            - Infants and elderly at higher risk
            
            Prevention:
            - Hand hygiene
            - Safe food handling
            - Clean drinking water
            - Rotavirus vaccination for infants
            
            Source: ICMR Guidelines on Diarrheal Diseases
            """,
            "metadata": {"source": "ICMR", "topic": "gastroenteritis", "year": 2023}
        }
    ]
    
    indexed_count = 0
    
    for doc in sample_documents:
        try:
            # Prepare document
            chunks = prepare_document_for_vectorization(doc["content"])
            
            # Store in vector store
            vector_store.store_document_embeddings(
                document_id=doc["id"],
                text_chunks=chunks,
                metadata=doc["metadata"]
            )
            
            indexed_count += 1
            logger.info(f"✅ Indexed: {doc['id']} ({len(chunks)} chunks)")
            
        except Exception as e:
            logger.error(f"Error indexing {doc['id']}: {str(e)}")
            continue
    
    return indexed_count


def main():
    """Main function to index medical knowledge"""
    logger.info("Starting medical knowledge indexing...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Try to load from data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "medical_knowledge")
    
    indexed_count = 0
    
    # Check if data directory exists
    if os.path.exists(data_dir):
        logger.info(f"Loading medical documents from: {data_dir}")
        vector_store = get_medical_knowledge_store()
        
        for document_id, content, metadata in load_medical_documents(data_dir):
            try:
                chunks = prepare_document_for_vectorization(content)
                vector_store.store_document_embeddings(
                    document_id=document_id,
                    text_chunks=chunks,
                    metadata=metadata
                )
                indexed_count += 1
                logger.info(f"✅ Indexed: {document_id} ({len(chunks)} chunks)")
            except Exception as e:
                logger.error(f"Error indexing {document_id}: {str(e)}")
    else:
        logger.info("No medical documents directory found. Using sample knowledge...")
        indexed_count = index_sample_medical_knowledge()
    
    logger.info(f"✅ Medical knowledge indexing completed! Indexed {indexed_count} documents.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

