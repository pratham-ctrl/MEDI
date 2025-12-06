"""Azure SQL Database Service for structured data storage"""

import logging
import pyodbc
import json
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)


class SQLDatabaseService:
    """Service for Azure SQL Database operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @contextmanager
    def get_connection(self, database: str = "users"):
        """
        Context manager for database connections
        
        Args:
            database: 'users' or 'drugs'
        
        Yields:
            Database connection object
        """
        conn_str = (
            settings.sql_connection_string_users 
            if database == "users" 
            else settings.sql_connection_string_drugs
        )
        
        conn = None
        try:
            conn = pyodbc.connect(conn_str)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute(self, sql: str, database: str = "users", params: tuple = None) -> None:
        """
        Execute SQL statement (DDL or DML)
        
        Args:
            sql: SQL statement to execute
            database: 'users' or 'drugs'
            params: Optional parameters for the query
        """
        with self.get_connection(database) as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            logger.info(f"Executed SQL on {database} database")
    
    # ====== User Operations ======
    
    def create_user(
        self,
        user_id: str,
        email: str,
        name: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user"""
        with self.get_connection("users") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Users (user_id, email, name, phone, created_at)
                VALUES (?, ?, ?, ?, GETDATE())
            """, (user_id, email, name, phone))
            conn.commit()
            
            logger.info(f"Created user: {user_id}")
            return self.get_user(user_id)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection("users") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, email, name, phone, created_at, last_login
                FROM Users WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "user_id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "phone": row[3],
                    "created_at": row[4],
                    "last_login": row[5]
                }
            return None
    
    # ====== Prescription Operations ======
    
    def save_prescription(
        self,
        prescription_id: str,
        user_id: str,
        document_blob_url: str,
        extracted_data: Dict[str, Any],
        ocr_confidence: float
    ) -> str:
        """Save prescription with extracted data"""
        with self.get_connection("users") as conn:
            cursor = conn.cursor()
            
            # Insert prescription
            cursor.execute("""
                INSERT INTO Prescriptions 
                (prescription_id, user_id, document_blob_url, extracted_data, ocr_confidence, upload_date)
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (
                prescription_id,
                user_id,
                document_blob_url,
                json.dumps(extracted_data),
                ocr_confidence
            ))
            
            # Insert medicines
            for medicine in extracted_data.get("medicines", []):
                cursor.execute("""
                    INSERT INTO PrescriptionMedicines
                    (medicine_id, prescription_id, medicine_name, dosage, frequency)
                    VALUES (NEWID(), ?, ?, ?, ?)
                """, (
                    prescription_id,
                    medicine.get("name"),
                    medicine.get("dosage"),
                    medicine.get("frequency")
                ))
            
            conn.commit()
            logger.info(f"Saved prescription: {prescription_id}")
            return prescription_id
    
    def get_prescription(self, prescription_id: str) -> Optional[Dict[str, Any]]:
        """Get prescription by ID"""
        with self.get_connection("users") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prescription_id, user_id, document_blob_url, extracted_data, 
                       ocr_confidence, upload_date
                FROM Prescriptions WHERE prescription_id = ?
            """, (prescription_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "prescription_id": row[0],
                    "user_id": row[1],
                    "document_blob_url": row[2],
                    "extracted_data": json.loads(row[3]) if row[3] else {},
                    "ocr_confidence": float(row[4]),
                    "upload_date": row[5]
                }
            return None
    
    def list_user_prescriptions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all prescriptions for a user"""
        with self.get_connection("users") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT TOP {limit} prescription_id, document_blob_url, 
                       ocr_confidence, upload_date
                FROM Prescriptions 
                WHERE user_id = ?
                ORDER BY upload_date DESC
            """, (user_id,))
            
            prescriptions = []
            for row in cursor.fetchall():
                prescriptions.append({
                    "prescription_id": row[0],
                    "document_blob_url": row[1],
                    "ocr_confidence": float(row[2]),
                    "upload_date": row[3]
                })
            
            return prescriptions
    
    # ====== Drug Database Operations ======
    
    def search_drugs(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search drugs by name (generic or brand)"""
        with self.get_connection("drugs") as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT TOP {limit} drug_id, generic_name, brand_names, category
                FROM DrugDatabase
                WHERE generic_name LIKE ? OR brand_names LIKE ?
                ORDER BY generic_name
            """, (f"%{query}%", f"%{query}%"))
            
            drugs = []
            for row in cursor.fetchall():
                drugs.append({
                    "drug_id": row[0],
                    "generic_name": row[1],
                    "brand_names": json.loads(row[2]) if row[2] else [],
                    "category": row[3]
                })
            
            return drugs
    
    def get_drug_info(self, drug_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed drug information"""
        with self.get_connection("drugs") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT drug_id, generic_name, brand_names, category, uses, 
                       dosage_adult, dosage_pediatric, side_effects_common, 
                       side_effects_serious, drug_interactions, contraindications, 
                       pregnancy_category, last_updated
                FROM DrugDatabase WHERE drug_id = ?
            """, (drug_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "drug_id": row[0],
                    "generic_name": row[1],
                    "brand_names": json.loads(row[2]) if row[2] else [],
                    "category": row[3],
                    "uses": json.loads(row[4]) if row[4] else [],
                    "dosage_adult": row[5],
                    "dosage_pediatric": row[6],
                    "side_effects_common": json.loads(row[7]) if row[7] else [],
                    "side_effects_serious": json.loads(row[8]) if row[8] else [],
                    "drug_interactions": json.loads(row[9]) if row[9] else [],
                    "contraindications": json.loads(row[10]) if row[10] else [],
                    "pregnancy_category": row[11],
                    "last_updated": row[12]
                }
            return None
    
    def insert_drug(self, drug_data: Dict[str, Any]) -> int:
        """Insert a new drug into the database"""
        with self.get_connection("drugs") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO DrugDatabase 
                (generic_name, brand_names, category, uses, dosage_adult, 
                 side_effects_common, side_effects_serious, drug_interactions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                drug_data.get("generic_name"),
                json.dumps(drug_data.get("brand_names", [])),
                drug_data.get("category"),
                json.dumps(drug_data.get("uses", [])),
                drug_data.get("dosage_adult"),
                json.dumps(drug_data.get("side_effects_common", [])),
                json.dumps(drug_data.get("side_effects_serious", [])),
                json.dumps(drug_data.get("drug_interactions", []))
            ))
            
            # Get the inserted ID
            cursor.execute("SELECT @@IDENTITY")
            drug_id = cursor.fetchone()[0]
            
            conn.commit()
            logger.info(f"Inserted drug: {drug_data.get('generic_name')} (ID: {drug_id})")
            return drug_id


# Global service instance
_sql_service = None


def get_sql_service() -> SQLDatabaseService:
    """Get or create the global SQL Database service instance"""
    global _sql_service
    if _sql_service is None:
        _sql_service = SQLDatabaseService()
    return _sql_service

