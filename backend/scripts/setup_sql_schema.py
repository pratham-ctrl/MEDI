"""Setup SQL database schemas"""

import logging
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sql_database import get_sql_service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL Schema Definitions
USERS_SCHEMA = """
-- Users table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
    CREATE TABLE Users (
        user_id NVARCHAR(50) PRIMARY KEY,
        email NVARCHAR(255) UNIQUE NOT NULL,
        name NVARCHAR(100),
        phone NVARCHAR(20),
        date_of_birth DATE,
        gender NVARCHAR(10),
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE(),
        last_login DATETIME NULL
    );
    
    CREATE INDEX idx_users_email ON Users(email);
    
    PRINT 'Users table created successfully';
END
ELSE
BEGIN
    PRINT 'Users table already exists';
    
    -- Add last_login column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Users') AND name = 'last_login')
    BEGIN
        ALTER TABLE Users ADD last_login DATETIME NULL;
        PRINT 'Added last_login column to Users table';
    END
END
"""

PRESCRIPTIONS_SCHEMA = """
-- Prescriptions table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Prescriptions' AND xtype='U')
BEGIN
    CREATE TABLE Prescriptions (
        prescription_id NVARCHAR(50) PRIMARY KEY,
        user_id NVARCHAR(50) NOT NULL,
        document_blob_url NVARCHAR(500),
        filename NVARCHAR(255),
        upload_date DATETIME DEFAULT GETDATE(),
        extracted_data NVARCHAR(MAX), -- JSON
        ocr_confidence DECIMAL(5,4),
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_prescriptions_user ON Prescriptions(user_id);
    CREATE INDEX idx_prescriptions_date ON Prescriptions(upload_date DESC);
    
    PRINT 'Prescriptions table created successfully';
END
ELSE
BEGIN
    PRINT 'Prescriptions table already exists';
END
"""

PRESCRIPTION_MEDICINES_SCHEMA = """
-- PrescriptionMedicines table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PrescriptionMedicines' AND xtype='U')
BEGIN
    CREATE TABLE PrescriptionMedicines (
        medicine_id INT IDENTITY(1,1) PRIMARY KEY,
        prescription_id NVARCHAR(50) NOT NULL,
        medicine_name NVARCHAR(200),
        dosage NVARCHAR(50),
        frequency NVARCHAR(50),
        duration NVARCHAR(50),
        instructions NVARCHAR(500),
        FOREIGN KEY (prescription_id) REFERENCES Prescriptions(prescription_id) ON DELETE CASCADE
    );
    
    CREATE INDEX idx_medicines_prescription ON PrescriptionMedicines(prescription_id);
    CREATE INDEX idx_medicines_name ON PrescriptionMedicines(medicine_name);
    
    PRINT 'PrescriptionMedicines table created successfully';
END
ELSE
BEGIN
    PRINT 'PrescriptionMedicines table already exists';
END
"""

DRUG_DATABASE_SCHEMA = """
-- DrugDatabase table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DrugDatabase' AND xtype='U')
BEGIN
    CREATE TABLE DrugDatabase (
        drug_id INT IDENTITY(1,1) PRIMARY KEY,
        generic_name NVARCHAR(200) NOT NULL,
        brand_names NVARCHAR(MAX), -- JSON array
        category NVARCHAR(100),
        uses NVARCHAR(MAX),
        side_effects_common NVARCHAR(MAX), -- JSON array
        side_effects_serious NVARCHAR(MAX), -- JSON array
        drug_interactions NVARCHAR(MAX), -- JSON array
        contraindications NVARCHAR(MAX), -- JSON array
        dosage_adult NVARCHAR(200),
        dosage_child NVARCHAR(200),
        pregnancy_category NVARCHAR(10),
        warnings NVARCHAR(MAX), -- JSON array
        storage NVARCHAR(500),
        last_updated DATETIME DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_drugs_generic ON DrugDatabase(generic_name);
    CREATE INDEX idx_drugs_category ON DrugDatabase(category);
    
    PRINT 'DrugDatabase table created successfully';
END
ELSE
BEGIN
    PRINT 'DrugDatabase table already exists';
END
"""


def create_users_database():
    """Create users database and tables"""
    logger.info("Creating users database tables...")
    
    sql_service = get_sql_service()
    
    try:
        # Execute schema creation for users database
        sql_service.execute(USERS_SCHEMA)
        sql_service.execute(PRESCRIPTIONS_SCHEMA)
        sql_service.execute(PRESCRIPTION_MEDICINES_SCHEMA)
        
        logger.info("Users database tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating users database: {str(e)}")
        return False


def create_drugs_database():
    """Create drugs database and tables"""
    logger.info("Creating drugs database tables...")
    
    try:
        sql_service = get_sql_service()
        # Execute on drugs database, not users database
        sql_service.execute(DRUG_DATABASE_SCHEMA, database="drugs")
        
        logger.info("Drugs database tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating drugs database: {str(e)}")
        return False


def insert_sample_data():
    """Insert sample test data"""
    logger.info("Inserting sample data...")
    
    sql_service = get_sql_service()
    
    try:
        # Sample user
        sample_user = """
        IF NOT EXISTS (SELECT * FROM Users WHERE user_id = 'user_123')
        BEGIN
            INSERT INTO Users (user_id, email, name)
            VALUES ('user_123', 'test@example.com', 'Test User');
            PRINT 'Sample user inserted';
        END
        """
        sql_service.execute(sample_user)
        
        # Sample drugs
        sample_drugs = """
        IF NOT EXISTS (SELECT * FROM DrugDatabase WHERE generic_name = 'Paracetamol')
        BEGIN
            INSERT INTO DrugDatabase (
                generic_name, brand_names, category, uses,
                side_effects_common, side_effects_serious,
                dosage_adult, dosage_child, warnings
            )
            VALUES (
                'Paracetamol',
                '["Crocin", "Dolo", "Calpol"]',
                'Analgesic, Antipyretic',
                'Used to treat pain and fever',
                '["Nausea", "Stomach pain", "Loss of appetite"]',
                '["Liver damage (with overdose)", "Allergic reactions"]',
                '500-1000mg every 4-6 hours, max 4g/day',
                '10-15mg/kg every 4-6 hours',
                '["Do not exceed recommended dose", "Avoid alcohol", "Consult doctor if symptoms persist"]'
            );
            
            INSERT INTO DrugDatabase (
                generic_name, brand_names, category, uses,
                side_effects_common, side_effects_serious,
                dosage_adult, dosage_child, warnings
            )
            VALUES (
                'Amoxicillin',
                '["Amoxil", "Moxikind", "Novamox"]',
                'Antibiotic',
                'Used to treat bacterial infections',
                '["Diarrhea", "Nausea", "Vomiting", "Rash"]',
                '["Severe allergic reactions", "Clostridium difficile colitis"]',
                '250-500mg every 8 hours',
                '20-40mg/kg/day in divided doses',
                '["Complete full course", "Do not use if allergic to penicillin", "Consult doctor"]'
            );
            
            INSERT INTO DrugDatabase (
                generic_name, brand_names, category, uses,
                side_effects_common, side_effects_serious,
                dosage_adult, dosage_child, warnings
            )
            VALUES (
                'Metformin',
                '["Glycomet", "Glucophage", "Obimet"]',
                'Antidiabetic',
                'Used to treat type 2 diabetes',
                '["Nausea", "Diarrhea", "Stomach upset", "Metallic taste"]',
                '["Lactic acidosis", "Vitamin B12 deficiency"]',
                '500-2000mg per day in divided doses',
                'Not recommended for children',
                '["Take with food", "Regular blood sugar monitoring", "Avoid alcohol"]'
            );
            
            PRINT 'Sample drugs inserted';
        END
        """
        sql_service.execute(sample_drugs)
        
        logger.info("Sample data inserted successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error inserting sample data: {str(e)}")
        return False


def main():
    """Main function to setup all schemas"""
    logger.info("Starting SQL database schema setup...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Create users database
    if not create_users_database():
        logger.error("Failed to create users database")
        return False
    
    # Create drugs database
    if not create_drugs_database():
        logger.error("Failed to create drugs database")
        return False
    
    # Insert sample data
    if not insert_sample_data():
        logger.warning("Failed to insert sample data (non-critical)")
    
    logger.info("✅ SQL database schema setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

