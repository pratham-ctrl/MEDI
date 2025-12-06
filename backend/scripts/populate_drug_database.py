"""Populate drug database with CDSCO data and generate embeddings"""

import logging
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sql_database import get_sql_service
from app.utils.vector_store import get_drug_database_store
from app.utils.embeddings import prepare_document_for_vectorization
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_cdsco_data(file_path: str):
    """
    Load CDSCO drug data from file
    
    Args:
        file_path: Path to CDSCO data file (CSV or JSON)
    
    Yields:
        Drug data dict
    """
    # This is a placeholder - in production, load actual CDSCO data
    # For now, return empty to use sample data
    return []


def get_sample_drugs():
    """Get comprehensive sample drug data"""
    return [
        {
            "generic_name": "Paracetamol",
            "brand_names": ["Crocin", "Dolo 650", "Calpol", "Metacin", "Pacimol"],
            "category": "Analgesic, Antipyretic",
            "uses": "Treatment of mild to moderate pain including headache, muscle aches, arthritis, backache, toothache, cold, and fever. First-line treatment for fever in adults and children.",
            "side_effects_common": ["Nausea", "Stomach pain", "Loss of appetite", "Headache"],
            "side_effects_serious": ["Liver damage with overdose", "Severe allergic reactions", "Stevens-Johnson syndrome", "Toxic epidermal necrolysis"],
            "drug_interactions": ["Warfarin (increased bleeding risk)", "Alcohol (liver damage)", "Isoniazid", "Carbamazepine"],
            "contraindications": ["Severe liver disease", "Severe kidney disease", "Alcohol dependence"],
            "dosage_adult": "500-1000mg every 4-6 hours as needed, maximum 4000mg per day",
            "dosage_child": "10-15mg/kg every 4-6 hours, maximum 5 doses in 24 hours",
            "pregnancy_category": "B",
            "warnings": ["Do not exceed recommended dose", "Risk of liver damage with overdose", "Avoid alcohol consumption", "Consult doctor if symptoms persist >3 days"],
            "storage": "Store at room temperature away from moisture and heat"
        },
        {
            "generic_name": "Amoxicillin",
            "brand_names": ["Amoxil", "Moxikind", "Novamox", "Wymox"],
            "category": "Antibiotic (Penicillin)",
            "uses": "Treatment of bacterial infections including respiratory tract infections, ear infections, urinary tract infections, skin infections, and dental infections.",
            "side_effects_common": ["Diarrhea", "Nausea", "Vomiting", "Rash", "Stomach upset"],
            "side_effects_serious": ["Severe allergic reactions", "Clostridium difficile colitis", "Liver problems", "Seizures"],
            "drug_interactions": ["Oral contraceptives (reduced effectiveness)", "Methotrexate", "Allopurinol", "Probenecid"],
            "contraindications": ["Penicillin allergy", "Infectious mononucleosis", "History of jaundice with amoxicillin"],
            "dosage_adult": "250-500mg every 8 hours or 500-875mg every 12 hours depending on infection severity",
            "dosage_child": "20-40mg/kg/day in divided doses every 8 hours",
            "pregnancy_category": "B",
            "warnings": ["Complete full course even if feeling better", "Do not use if allergic to penicillin", "May cause diarrhea", "Report severe diarrhea immediately"],
            "storage": "Store at room temperature. Reconstituted suspension should be refrigerated and used within 14 days"
        },
        {
            "generic_name": "Metformin",
            "brand_names": ["Glycomet", "Glucophage", "Obimet", "Formet"],
            "category": "Antidiabetic (Biguanide)",
            "uses": "First-line treatment for type 2 diabetes mellitus. Used to control blood sugar levels along with diet and exercise.",
            "side_effects_common": ["Nausea", "Diarrhea", "Stomach upset", "Metallic taste", "Loss of appetite"],
            "side_effects_serious": ["Lactic acidosis", "Vitamin B12 deficiency", "Hypoglycemia when combined with other drugs"],
            "drug_interactions": ["Contrast dye (stop before imaging)", "Alcohol", "Insulin", "Sulfonylureas"],
            "contraindications": ["Severe kidney disease", "Liver disease", "Heart failure", "Metabolic acidosis"],
            "dosage_adult": "Start with 500mg once or twice daily, gradually increase to 500-2000mg per day in divided doses",
            "dosage_child": "Not recommended for children under 10 years",
            "pregnancy_category": "B",
            "warnings": ["Take with food to reduce GI side effects", "Regular blood sugar monitoring required", "Avoid excessive alcohol", "Stop before surgery or imaging with contrast"],
            "storage": "Store at room temperature away from moisture"
        },
        {
            "generic_name": "Atorvastatin",
            "brand_names": ["Lipitor", "Atorva", "Storvas", "Atocor"],
            "category": "Statin (Lipid-lowering agent)",
            "uses": "Treatment of high cholesterol and triglycerides. Prevention of cardiovascular disease in high-risk patients.",
            "side_effects_common": ["Muscle pain", "Joint pain", "Diarrhea", "Heartburn", "Headache"],
            "side_effects_serious": ["Rhabdomyolysis", "Liver problems", "Memory problems", "Increased blood sugar"],
            "drug_interactions": ["Grapefruit juice", "Cyclosporine", "Gemfibrozil", "Niacin", "Erythromycin"],
            "contraindications": ["Active liver disease", "Pregnancy", "Breastfeeding"],
            "dosage_adult": "10-80mg once daily, usually taken in the evening",
            "dosage_child": "Not recommended for children under 10 years",
            "pregnancy_category": "X",
            "warnings": ["Report unexplained muscle pain", "Regular liver function tests", "Avoid grapefruit juice", "Do not take during pregnancy"],
            "storage": "Store at room temperature away from light and moisture"
        },
        {
            "generic_name": "Omeprazole",
            "brand_names": ["Omez", "Prilosec", "Omepral", "Omepraz"],
            "category": "Proton Pump Inhibitor",
            "uses": "Treatment of gastroesophageal reflux disease (GERD), stomach and duodenal ulcers, Zollinger-Ellison syndrome, and erosive esophagitis.",
            "side_effects_common": ["Headache", "Nausea", "Diarrhea", "Stomach pain", "Gas"],
            "side_effects_serious": ["Bone fractures", "Vitamin B12 deficiency", "Clostridium difficile infection", "Kidney problems"],
            "drug_interactions": ["Clopidogrel (reduced effectiveness)", "Warfarin", "Diazepam", "Phenytoin"],
            "contraindications": ["Hypersensitivity to proton pump inhibitors"],
            "dosage_adult": "20-40mg once daily before breakfast for 4-8 weeks",
            "dosage_child": "10-20mg once daily depending on weight",
            "pregnancy_category": "C",
            "warnings": ["Take before meals", "Long-term use may increase fracture risk", "May mask stomach cancer symptoms", "Report persistent diarrhea"],
            "storage": "Store at room temperature in a dry place"
        }
    ]


def populate_sql_database():
    """Populate SQL database with drug data"""
    logger.info("Populating SQL drug database...")
    
    sql_service = get_sql_service()
    drugs = get_sample_drugs()
    
    populated_count = 0
    
    for drug in drugs:
        try:
            # Check if drug already exists
            existing = sql_service.search_drugs(drug["generic_name"], limit=1)
            if existing:
                logger.info(f"Drug already exists: {drug['generic_name']}")
                continue
            
            # Insert drug
            insert_query = """
            INSERT INTO DrugDatabase (
                generic_name, brand_names, category, uses,
                side_effects_common, side_effects_serious,
                drug_interactions, contraindications,
                dosage_adult, dosage_child, pregnancy_category,
                warnings, storage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            import json
            params = (
                drug["generic_name"],
                json.dumps(drug["brand_names"]),
                drug["category"],
                drug["uses"],
                json.dumps(drug["side_effects_common"]),
                json.dumps(drug["side_effects_serious"]),
                json.dumps(drug["drug_interactions"]),
                json.dumps(drug["contraindications"]),
                drug["dosage_adult"],
                drug.get("dosage_child"),
                drug.get("pregnancy_category"),
                json.dumps(drug["warnings"]),
                drug.get("storage")
            )
            
            sql_service.execute(insert_query, database="drugs", params=params)
            populated_count += 1
            logger.info(f"✅ Inserted drug: {drug['generic_name']}")
            
        except Exception as e:
            logger.error(f"Error inserting drug {drug['generic_name']}: {str(e)}")
            continue
    
    return populated_count


def generate_drug_embeddings():
    """Generate and store embeddings for drugs"""
    logger.info("Generating drug embeddings...")
    
    sql_service = get_sql_service()
    vector_store = get_drug_database_store()
    drugs = sql_service.search_drugs("", limit=1000)  # Get all drugs
    
    indexed_count = 0
    
    for drug in drugs:
        try:
            # Create comprehensive text for embedding
            drug_text = f"""
            Medicine: {drug['generic_name']}
            Brand Names: {', '.join(drug.get('brand_names', []))}
            Category: {drug.get('category', '')}
            
            Uses: {drug.get('uses', '')}
            
            Dosage (Adult): {drug.get('dosage_adult', '')}
            Dosage (Child): {drug.get('dosage_child', 'Consult doctor')}
            
            Common Side Effects: {', '.join([se.get('effect', se) if isinstance(se, dict) else se for se in drug.get('side_effects_common', [])])}
            Serious Side Effects: {', '.join([se.get('effect', se) if isinstance(se, dict) else se for se in drug.get('side_effects_serious', [])])}
            
            Drug Interactions: {', '.join(drug.get('drug_interactions', []))}
            Contraindications: {', '.join(drug.get('contraindications', []))}
            
            Warnings: {', '.join(drug.get('warnings', []))}
            """
            
            # Prepare and store embeddings
            chunks = prepare_document_for_vectorization(drug_text, chunk_size=300)
            
            vector_store.store_document_embeddings(
                document_id=f"drug_{drug['drug_id']}",
                text_chunks=chunks,
                metadata={
                    "drug_id": drug['drug_id'],
                    "generic_name": drug['generic_name'],
                    "category": drug.get('category', '')
                }
            )
            
            indexed_count += 1
            logger.info(f"✅ Indexed embeddings: {drug['generic_name']}")
            
        except Exception as e:
            logger.error(f"Error generating embeddings for {drug.get('generic_name', 'unknown')}: {str(e)}")
            continue
    
    return indexed_count


def main():
    """Main function to populate drug database"""
    logger.info("Starting drug database population...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Populate SQL database
    sql_count = populate_sql_database()
    logger.info(f"Populated {sql_count} drugs in SQL database")
    
    # Generate embeddings
    vector_count = generate_drug_embeddings()
    logger.info(f"Generated embeddings for {vector_count} drugs")
    
    logger.info("✅ Drug database population completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

