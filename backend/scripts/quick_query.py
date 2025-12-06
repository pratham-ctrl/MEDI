"""Quick database query tool"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sql_database import get_sql_service

def query_users_db():
    """Query users database"""
    sql_service = get_sql_service()
    
    print("\n" + "="*60)
    print("USERS DATABASE - Tables")
    print("="*60)
    
    with sql_service.get_connection("users") as conn:
        cursor = conn.cursor()
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        print(f"Total Users: {user_count}")
        
        # Count prescriptions
        cursor.execute("SELECT COUNT(*) FROM Prescriptions")
        prescription_count = cursor.fetchone()[0]
        print(f"Total Prescriptions: {prescription_count}")
        
        # Show users if any
        if user_count > 0:
            print("\nUsers:")
            cursor.execute("SELECT TOP 5 user_id, email, name FROM Users")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]} ({row[2]})")

def query_drugs_db():
    """Query drugs database"""
    sql_service = get_sql_service()
    
    print("\n" + "="*60)
    print("DRUGS DATABASE - Tables")
    print("="*60)
    
    with sql_service.get_connection("drugs") as conn:
        cursor = conn.cursor()
        
        # Count drugs
        cursor.execute("SELECT COUNT(*) FROM DrugDatabase")
        drug_count = cursor.fetchone()[0]
        print(f"Total Drugs: {drug_count}")
        
        # Show drugs if any
        if drug_count > 0:
            print("\nTop 10 Drugs:")
            cursor.execute("SELECT TOP 10 drug_id, generic_name, category FROM DrugDatabase")
            for row in cursor.fetchall():
                print(f"  - {row[0]}: {row[1]} ({row[2]})")

if __name__ == "__main__":
    try:
        query_users_db()
        query_drugs_db()
        print("\n" + "="*60 + "\n")
    except Exception as e:
        print(f"Error: {e}")

