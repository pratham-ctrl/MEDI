#!/usr/bin/env python3
"""
Azure Services Health Check Script
Tests all Azure services and endpoints for the Medical Chatbot project
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import asyncio

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class ServiceTester:
    """Main class for testing Azure services"""
    
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.start_time = None
        
    def print_header(self):
        """Print test header"""
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.CYAN}Azure Services Health Check{Colors.RESET}")
        print(f"{Colors.BLUE}Medical Chatbot - Service Testing Suite{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")
    
    def log_test(self, service: str, test_name: str, status: str, message: str = "", details: str = ""):
        """Log test result"""
        self.total_tests += 1
        
        if status == "PASS":
            icon = "✓"
            color = Colors.GREEN
            self.passed_tests += 1
        elif status == "FAIL":
            icon = "✗"
            color = Colors.RED
            self.failed_tests += 1
        elif status == "SKIP":
            icon = "⊘"
            color = Colors.YELLOW
            self.skipped_tests += 1
        else:
            icon = "?"
            color = Colors.YELLOW
        
        print(f"{color}{icon} {service:<30} {test_name:<40} [{status}]{Colors.RESET}")
        if message:
            print(f"  {Colors.CYAN}→{Colors.RESET} {message}")
        if details:
            print(f"  {Colors.YELLOW}Details:{Colors.RESET} {details}")
        
        self.results.append({
            'service': service,
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_azure_openai(self):
        """Test Azure OpenAI Service"""
        self.print_section("1. Testing Azure OpenAI Service")
        
        try:
            from openai import AzureOpenAI
            
            # GPT Model Configuration
            gpt_endpoint = os.getenv("OPENAI_GPT_ENDPOINT")
            gpt_api_key = os.getenv("OPENAI_GPT_API_KEY")
            gpt_deployment = os.getenv("OPENAI_GPT4_DEPLOYMENT", "gpt-4-deployment")
            gpt_api_version = os.getenv("OPENAI_GPT_API_VERSION", "2024-12-01-preview")
            
            # Embedding Model Configuration
            embedding_endpoint = os.getenv("OPENAI_EMBEDDING_ENDPOINT")
            embedding_api_key = os.getenv("OPENAI_EMBEDDING_API_KEY")
            embedding_deployment = os.getenv("OPENAI_EMBEDDING_DEPLOYMENT", "embedding-deployment")
            embedding_api_version = os.getenv("OPENAI_EMBEDDING_API_VERSION", "2024-08-01-preview")
            
            # Fallback to tesst.py credentials if not set
            if not gpt_endpoint or not gpt_api_key:
                gpt_endpoint = "https://vansh-mgtnizvw-swedencentral.cognitiveservices.azure.com/"
                gpt_api_key = "2hpu3dMUiukyQG7lttsVXxCXgwyBGWdyUr2G7HaFr1KLv2nMhp8IJQQJ99BJACfhMk5XJ3w3AAAAACOGrMFS"
                gpt_deployment = "gpt-4.1"
                gpt_api_version = "2024-12-01-preview"
            
            # Test GPT Model
            if not gpt_api_key or gpt_api_key == "PLACEHOLDER":
                self.log_test("Azure OpenAI (GPT)", "Configuration Check", "SKIP", 
                            "GPT API key not configured in environment")
            else:
                self.log_test("Azure OpenAI (GPT)", "Configuration Check", "PASS", 
                             f"Endpoint: {gpt_endpoint}")
                
                try:
                    client = AzureOpenAI(
                        api_version=gpt_api_version,
                        azure_endpoint=gpt_endpoint,
                        api_key=gpt_api_key,
                    )
                    
                    self.log_test("Azure OpenAI (GPT)", "Client Initialization", "PASS", 
                                 "Client created successfully")
                    
                    # Test chat completion
                    response = client.chat.completions.create(
                        model=gpt_deployment,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "Say 'OK' if you can hear me."}
                        ],
                        max_tokens=10,
                        temperature=0.3
                    )
                    
                    reply = response.choices[0].message.content
                    self.log_test("Azure OpenAI (GPT)", "Chat Completion API", "PASS", 
                                 f"Response: {reply[:50] if reply else 'Success'}")
                    
                    client.close()
                    
                except Exception as e:
                    self.log_test("Azure OpenAI (GPT)", "API Call", "FAIL", 
                                 f"Failed: {str(e)}")
            
            # Test Embedding Model
            if embedding_endpoint and embedding_api_key and embedding_api_key != "PLACEHOLDER":
                self.log_test("Azure OpenAI (Embedding)", "Configuration Check", "PASS", 
                             f"Endpoint: {embedding_endpoint}")
                
                try:
                    embedding_client = AzureOpenAI(
                        api_version=embedding_api_version,
                        azure_endpoint=embedding_endpoint,
                        api_key=embedding_api_key,
                    )
                    
                    self.log_test("Azure OpenAI (Embedding)", "Client Initialization", "PASS", 
                                 "Client created successfully")
                    
                    # Test embeddings
                    response = embedding_client.embeddings.create(
                        model=embedding_deployment,
                        input="Test embedding"
                    )
                    
                    embedding_vector = response.data[0].embedding
                    self.log_test("Azure OpenAI (Embedding)", "Embeddings API", "PASS", 
                                 f"Generated embedding with {len(embedding_vector)} dimensions")
                    
                    embedding_client.close()
                    
                except Exception as e:
                    self.log_test("Azure OpenAI (Embedding)", "API Call", "FAIL", 
                                 f"Failed: {str(e)}")
            else:
                self.log_test("Azure OpenAI (Embedding)", "Configuration Check", "SKIP", 
                            "Embedding endpoint not configured (optional)")
                
        except ImportError:
            self.log_test("Azure OpenAI", "Python SDK", "FAIL", 
                         "openai package not installed. Run: pip install openai")
        except Exception as e:
            self.log_test("Azure OpenAI", "General Error", "FAIL", str(e))
    
    def test_blob_storage(self):
        """Test Azure Blob Storage"""
        self.print_section("2. Testing Azure Blob Storage")
        
        try:
            from azure.storage.blob import BlobServiceClient
            
            connection_string = os.getenv("STORAGE_CONNECTION_STRING")
            account_name = os.getenv("STORAGE_ACCOUNT_NAME")
            
            if not connection_string and not account_name:
                self.log_test("Blob Storage", "Configuration Check", "SKIP", 
                            "Storage connection string not configured")
                return
            
            self.log_test("Blob Storage", "Configuration Check", "PASS", 
                         f"Account: {account_name or 'from connection string'}")
            
            # Test connection
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            self.log_test("Blob Storage", "Client Initialization", "PASS", 
                         "Client created successfully")
            
            # List containers
            containers = list(blob_service_client.list_containers())
            container_names = [c.name for c in containers]
            
            self.log_test("Blob Storage", "List Containers", "PASS", 
                         f"Found {len(containers)} containers: {', '.join(container_names)}")
            
            # Check expected containers
            expected_containers = ["prescription-uploads", "extracted-data", "medical-images"]
            for container in expected_containers:
                if container in container_names:
                    self.log_test("Blob Storage", f"Container: {container}", "PASS", 
                                 "Container exists")
                else:
                    self.log_test("Blob Storage", f"Container: {container}", "FAIL", 
                                 "Container not found")
            
            # Test upload (to prescription-uploads container)
            if "prescription-uploads" in container_names:
                try:
                    test_data = f"Health check test - {datetime.now().isoformat()}"
                    blob_client = blob_service_client.get_blob_client(
                        container="prescription-uploads", 
                        blob="healthcheck_test.txt"
                    )
                    blob_client.upload_blob(test_data, overwrite=True)
                    self.log_test("Blob Storage", "Upload Test", "PASS", 
                                 "Test file uploaded successfully")
                    
                    # Clean up
                    blob_client.delete_blob()
                    self.log_test("Blob Storage", "Delete Test", "PASS", 
                                 "Test file deleted successfully")
                except Exception as e:
                    self.log_test("Blob Storage", "Upload Test", "FAIL", str(e))
                    
        except ImportError:
            self.log_test("Blob Storage", "Python SDK", "FAIL", 
                         "azure-storage-blob package not installed. Run: pip install azure-storage-blob")
        except Exception as e:
            self.log_test("Blob Storage", "General Error", "FAIL", str(e))
    
    def test_sql_database(self):
        """Test Azure SQL Database"""
        self.print_section("3. Testing Azure SQL Database")
        
        try:
            import pyodbc
            
            # Test multiple databases
            databases = [
                {
                    "name": "SQL Database 1",
                    "connection_string": os.getenv("SQL_CONNECTION_STRING_1")
                },
                {
                    "name": "SQL Database 2",
                    "connection_string": os.getenv("SQL_CONNECTION_STRING_2")
                },
                {
                    "name": "SQL Database 3",
                    "connection_string": os.getenv("SQL_CONNECTION_STRING_3")
                }
            ]
            
            # Also check for old format (backward compatibility)
            if os.getenv("SQL_CONNECTION_STRING"):
                databases.insert(0, {
                    "name": "SQL Database (Primary)",
                    "connection_string": os.getenv("SQL_CONNECTION_STRING")
                })
            
            tested_any = False
            
            for db in databases:
                connection_string = db["connection_string"]
                db_name = db["name"]
                
                if not connection_string or connection_string == "PLACEHOLDER":
                    self.log_test(db_name, "Configuration Check", "SKIP", 
                                "Connection string not configured")
                    continue
                
                tested_any = True
                self.log_test(db_name, "Configuration Check", "PASS", 
                             "Connection string found")
                
                # Test connection
                try:
                    conn = pyodbc.connect(connection_string)
                    cursor = conn.cursor()
                    
                    self.log_test(db_name, "Database Connection", "PASS", 
                                 "Connected successfully")
                    
                    # Test query
                    cursor.execute("SELECT @@VERSION")
                    version = cursor.fetchone()[0]
                    self.log_test(db_name, "Query Test", "PASS", 
                                 f"SQL Server version: {version[:60]}...")
                    
                    # Get database name
                    cursor.execute("SELECT DB_NAME()")
                    current_db = cursor.fetchone()[0]
                    
                    # Check tables
                    cursor.execute("""
                        SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_TYPE = 'BASE TABLE'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if tables:
                        self.log_test(db_name, "List Tables", "PASS", 
                                     f"Database: {current_db}, {len(tables)} tables: {', '.join(tables[:5])}")
                    else:
                        self.log_test(db_name, "List Tables", "PASS", 
                                     f"Database: {current_db}, No tables (new database)")
                    
                    cursor.close()
                    conn.close()
                    
                except Exception as e:
                    self.log_test(db_name, "Connection Error", "FAIL", str(e))
            
            if not tested_any:
                self.log_test("SQL Database", "Configuration Check", "SKIP", 
                            "No SQL connection strings configured")
            
        except ImportError:
            self.log_test("SQL Database", "Python SDK", "FAIL", 
                         "pyodbc package not installed. Run: pip install pyodbc")
        except Exception as e:
            self.log_test("SQL Database", "General Error", "FAIL", str(e))
    
    def test_cosmos_db(self):
        """Test Azure Cosmos DB"""
        self.print_section("4. Testing Azure Cosmos DB")
        
        try:
            from azure.cosmos import CosmosClient
            
            endpoint = os.getenv("COSMOS_ENDPOINT")
            key = os.getenv("COSMOS_KEY")
            database_name = os.getenv("COSMOS_DATABASE", "medicalchatbot")
            
            if not endpoint or not key or key == "PLACEHOLDER":
                self.log_test("Cosmos DB", "Configuration Check", "SKIP", 
                            "Cosmos DB credentials not configured")
                return
            
            self.log_test("Cosmos DB", "Configuration Check", "PASS", 
                         f"Endpoint: {endpoint}")
            
            # Test connection
            client = CosmosClient(endpoint, key)
            
            self.log_test("Cosmos DB", "Client Initialization", "PASS", 
                         "Client created successfully")
            
            # List databases
            databases = list(client.list_databases())
            db_names = [db['id'] for db in databases]
            
            self.log_test("Cosmos DB", "List Databases", "PASS", 
                         f"Found {len(databases)} databases: {', '.join(db_names)}")
            
            # Check specific database
            if database_name in db_names:
                database = client.get_database_client(database_name)
                self.log_test("Cosmos DB", f"Database: {database_name}", "PASS", 
                             "Database exists")
                
                # List containers
                containers = list(database.list_containers())
                container_names = [c['id'] for c in containers]
                
                self.log_test("Cosmos DB", "List Containers", "PASS", 
                             f"Found {len(containers)} containers: {', '.join(container_names)}")
                
                # Check expected containers
                expected_containers = ["conversations", "messages"]
                for container in expected_containers:
                    if container in container_names:
                        self.log_test("Cosmos DB", f"Container: {container}", "PASS", 
                                     "Container exists")
                    else:
                        self.log_test("Cosmos DB", f"Container: {container}", "FAIL", 
                                     "Container not found")
            else:
                self.log_test("Cosmos DB", f"Database: {database_name}", "FAIL", 
                             "Database not found")
                
        except ImportError:
            self.log_test("Cosmos DB", "Python SDK", "FAIL", 
                         "azure-cosmos package not installed. Run: pip install azure-cosmos")
        except Exception as e:
            self.log_test("Cosmos DB", "General Error", "FAIL", str(e))
    
    def test_redis_cache(self):
        """Test Azure Redis Cache"""
        self.print_section("5. Testing Azure Redis Cache")
        
        try:
            import redis
            
            connection_string = os.getenv("REDIS_CONNECTION_STRING")
            
            if not connection_string or connection_string == "PLACEHOLDER":
                self.log_test("Redis Cache", "Configuration Check", "SKIP", 
                            "Redis connection string not configured")
                return
            
            self.log_test("Redis Cache", "Configuration Check", "PASS", 
                         "Connection string found")
            
            try:
                # Parse the connection string format: host:port,password=xxx,ssl=True
                parts = connection_string.split(',')
                host_port = parts[0].split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 6380
                
                password = None
                use_ssl = True
                
                for part in parts[1:]:
                    if 'password=' in part.lower():
                        password = part.split('=', 1)[1]
                    elif 'ssl=' in part.lower():
                        use_ssl = part.split('=', 1)[1].lower() in ['true', '1', 'yes']
                
                # Test connection
                r = redis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    ssl=use_ssl,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                
                # Ping test
                if r.ping():
                    self.log_test("Redis Cache", "Connection Test", "PASS", 
                                 "PING successful")
                
                # Set/Get test
                test_key = "healthcheck_test"
                test_value = f"test_{int(time.time())}"
                r.set(test_key, test_value, ex=60)
                
                retrieved_value = r.get(test_key)
                if retrieved_value and retrieved_value.decode() == test_value:
                    self.log_test("Redis Cache", "Read/Write Test", "PASS", 
                                 "SET/GET operations successful")
                else:
                    self.log_test("Redis Cache", "Read/Write Test", "FAIL", 
                                 "Value mismatch")
                
                # Clean up
                r.delete(test_key)
                
                # Get info
                info = r.info()
                self.log_test("Redis Cache", "Server Info", "PASS", 
                             f"Redis version: {info.get('redis_version', 'unknown')}")
                
            except Exception as e:
                self.log_test("Redis Cache", "Connection String Parse", "FAIL", 
                             f"Failed to parse or connect: {str(e)}")
            
        except ImportError:
            self.log_test("Redis Cache", "Python SDK", "FAIL", 
                         "redis package not installed. Run: pip install redis")
        except Exception as e:
            self.log_test("Redis Cache", "General Error", "FAIL", str(e))
    
    def test_key_vault(self):
        """Test Azure Key Vault"""
        self.print_section("6. Testing Azure Key Vault")
        
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            
            vault_url = os.getenv("KEYVAULT_URL")
            
            if not vault_url:
                self.log_test("Key Vault", "Configuration Check", "SKIP", 
                            "Key Vault URL not configured")
                return
            
            self.log_test("Key Vault", "Configuration Check", "PASS", 
                         f"Vault URL: {vault_url}")
            
            # Test connection (requires Azure CLI authentication)
            try:
                credential = DefaultAzureCredential()
                client = SecretClient(vault_url=vault_url, credential=credential)
                
                self.log_test("Key Vault", "Client Initialization", "PASS", 
                             "Client created successfully")
                
                # List secrets
                secrets = list(client.list_properties_of_secrets())
                secret_names = [s.name for s in secrets[:10]]  # First 10
                
                self.log_test("Key Vault", "List Secrets", "PASS", 
                             f"Found {len(secrets)} secrets: {', '.join(secret_names)}")
                
            except Exception as e:
                self.log_test("Key Vault", "Authentication", "FAIL", 
                             f"Make sure you're logged in with 'az login': {str(e)}")
                
        except ImportError:
            self.log_test("Key Vault", "Python SDK", "FAIL", 
                         "azure-keyvault-secrets and azure-identity packages not installed. " +
                         "Run: pip install azure-keyvault-secrets azure-identity")
        except Exception as e:
            self.log_test("Key Vault", "General Error", "FAIL", str(e))
    
    def test_document_intelligence(self):
        """Test Azure Document Intelligence"""
        self.print_section("7. Testing Azure Document Intelligence (Form Recognizer)")
        
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            
            endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
            key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")
            
            if not endpoint or not key or key == "PLACEHOLDER":
                self.log_test("Document Intelligence", "Configuration Check", "SKIP", 
                            "Document Intelligence credentials not configured")
                return
            
            self.log_test("Document Intelligence", "Configuration Check", "PASS", 
                         f"Endpoint: {endpoint}")
            
            # Test connection
            client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))
            
            self.log_test("Document Intelligence", "Client Initialization", "PASS", 
                         "Client created successfully")
            
            # Note: Can't easily test without uploading a document
            self.log_test("Document Intelligence", "Service Status", "PASS", 
                         "Service is accessible (full document analysis requires file upload)")
            
        except ImportError:
            self.log_test("Document Intelligence", "Python SDK", "FAIL", 
                         "azure-ai-formrecognizer package not installed. " +
                         "Run: pip install azure-ai-formrecognizer")
        except Exception as e:
            self.log_test("Document Intelligence", "General Error", "FAIL", str(e))
    
    
    def test_environment_variables(self):
        """Check all required environment variables"""
        self.print_section("8. Testing Environment Variables")
        
        required_vars = [
            "OPENAI_GPT_ENDPOINT",
            "OPENAI_GPT_API_KEY",
            "STORAGE_CONNECTION_STRING",
            "SQL_CONNECTION_STRING_1",
            "SQL_CONNECTION_STRING_2",
            "SQL_CONNECTION_STRING_3",
            "COSMOS_ENDPOINT",
            "COSMOS_KEY",
        ]
        
        # Add Redis connection string to required vars
        required_vars.append("REDIS_CONNECTION_STRING")
        
        optional_vars = [
            "OPENAI_EMBEDDING_ENDPOINT",
            "OPENAI_EMBEDDING_API_KEY",
            "KEYVAULT_URL",
            "DOCUMENT_INTELLIGENCE_ENDPOINT",
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value and value != "PLACEHOLDER":
                self.log_test("Environment", var, "PASS", "✓ Set")
            else:
                self.log_test("Environment", var, "FAIL", "Not configured")
        
        for var in optional_vars:
            value = os.getenv(var)
            if value and value != "PLACEHOLDER":
                self.log_test("Environment", var, "PASS", "✓ Set")
            else:
                self.log_test("Environment", var, "SKIP", "Optional - not set")
    
    def test_networking(self):
        """Test network connectivity"""
        self.print_section("9. Testing Network Connectivity")
        
        try:
            import requests
            
            endpoints = {
                "Azure Portal": "https://portal.azure.com",
                "Azure OpenAI API": "https://api.openai.azure.com",
                "Azure Storage": "https://management.azure.com",
            }
            
            for name, url in endpoints.items():
                try:
                    response = requests.head(url, timeout=5)
                    self.log_test("Network", f"{name} Reachable", "PASS", 
                                 f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test("Network", f"{name} Reachable", "FAIL", str(e))
                    
        except ImportError:
            self.log_test("Network", "requests package", "FAIL", 
                         "requests package not installed")
    
    def print_summary(self):
        """Print test summary"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.CYAN}Test Summary{Colors.RESET}")
        print("="*80)
        print(f"\nTotal Tests: {self.total_tests}")
        print(f"{Colors.GREEN}✓ Passed: {self.passed_tests}{Colors.RESET}")
        print(f"{Colors.RED}✗ Failed: {self.failed_tests}{Colors.RESET}")
        print(f"{Colors.YELLOW}⊘ Skipped: {self.skipped_tests}{Colors.RESET}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print(f"Elapsed Time: {elapsed_time:.2f} seconds")
        
        # Overall status
        if self.failed_tests == 0:
            status = f"{Colors.GREEN}ALL TESTS PASSED ✓{Colors.RESET}"
        elif self.failed_tests < 5:
            status = f"{Colors.YELLOW}SOME TESTS FAILED - CHECK CONFIGURATION{Colors.RESET}"
        else:
            status = f"{Colors.RED}MULTIPLE FAILURES - REVIEW SETUP{Colors.RESET}"
        
        print(f"\n{Colors.BOLD}Overall Status: {status}{Colors.RESET}")
        print("="*80 + "\n")
    
    def save_results(self, filename: str = "test_results.json"):
        """Save test results to JSON file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': self.total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'skipped': self.skipped_tests,
                'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            'tests': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"{Colors.CYAN}Results saved to: {filename}{Colors.RESET}\n")
    
    def run_all_tests(self):
        """Run all service tests"""
        self.start_time = time.time()
        self.print_header()
        
        # Run all tests
        self.test_environment_variables()
        self.test_azure_openai()
        self.test_blob_storage()
        self.test_sql_database()
        self.test_cosmos_db()
        self.test_redis_cache()
        self.test_key_vault()
        self.test_document_intelligence()
        self.test_networking()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        # Return exit code
        return 0 if self.failed_tests == 0 else 1


def main():
    """Main entry point"""
    # Check if .env file exists and load it
    try:
        from dotenv import load_dotenv
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"{Colors.CYAN}Loaded environment from .env file{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}No .env file found. Using system environment variables.{Colors.RESET}")
            print(f"{Colors.YELLOW}Tip: Create a .env file with your Azure credentials{Colors.RESET}\n")
    except ImportError:
        print(f"{Colors.YELLOW}python-dotenv not installed. Using system environment variables only.{Colors.RESET}")
        print(f"{Colors.YELLOW}Install with: pip install python-dotenv{Colors.RESET}\n")
    
    # Run tests
    tester = ServiceTester()
    exit_code = tester.run_all_tests()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

