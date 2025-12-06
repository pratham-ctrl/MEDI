# Azure Configuration Master Sheet
## Medical Chatbot - Complete Service Configuration Reference

**Version:** 1.0  
**Last Updated:** October 15, 2025  
**Project:** Medical Document Chatbot  
**Environment:** Production

> ⚠️ **SECURITY WARNING:** This file contains sensitive credentials. Never commit to Git. Add to .gitignore immediately!

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Azure Account Details](#azure-account-details)
3. [Resource Group & Networking](#resource-group--networking)
4. [Security - Key Vault](#security---key-vault)
5. [Storage Services](#storage-services)
6. [Database Services](#database-services)
7. [AI Services](#ai-services)
8. [Compute Services](#compute-services)
9. [Networking & Gateway](#networking--gateway)
10. [Authentication](#authentication)
11. [Monitoring & Logging](#monitoring--logging)
12. [Environment Variables (.env)](#environment-variables-env)
13. [Connection Strings](#connection-strings)
14. [API Endpoints Reference](#api-endpoints-reference)

---

## Quick Reference

### Essential URLs
| Service | URL/Endpoint |
|---------|-------------|
| **Main API** | `https://[YOUR_APP_SERVICE].azurewebsites.net` |
| **API Gateway** | `https://[YOUR_APIM].azure-api.net` |
| **CDN Endpoint** | `https://[YOUR_CDN].azureedge.net` |
| **Azure Portal** | `https://portal.azure.com` |
| **AI Studio** | `https://ai.azure.com` |

### Most Used Secrets
| Secret Name | Location | Usage |
|-------------|----------|-------|
| `openai-api-key` | Key Vault | OpenAI API calls |
| `sql-connection-string` | Key Vault | Database access |
| `storage-connection-string` | Key Vault | Blob storage |
| `app-insights-connection-string` | Key Vault | Monitoring |

---

## Azure Account Details

### Subscription Information
```yaml
Subscription Name: ________________________________
Subscription ID: __________________________________
Tenant ID: ________________________________________
Azure AD Directory: _______________________________
Primary Location: Central India
Secondary Location: South India
```

### Account Credentials
```yaml
Azure Portal Email: _______________________________
Azure Portal Password: [Use Azure AD]
Multi-Factor Auth: Enabled ☐ Yes ☐ No
```

### Billing Information
```yaml
Payment Method: ___________________________________
Billing Email: ____________________________________
Budget Alert Threshold: $__________ per month
Cost Center/Tag: __________________________________
```

---

## Resource Group & Networking

### Resource Group
```yaml
Name: medical-chatbot-rg
Location: centralindia
Tags:
  Environment: Production
  Project: MedicalChatbot
  ManagedBy: [YOUR_NAME]
  CostCenter: [YOUR_COST_CENTER]
```

### Virtual Network
```yaml
VNet Name: medical-chatbot-vnet
Address Space: 10.0.0.0/16

Subnets:
  - Name: default-subnet
    Address Range: 10.0.1.0/24
  
  - Name: app-service-subnet
    Address Range: 10.0.2.0/24
  
  - Name: ai-services-subnet
    Address Range: 10.0.3.0/24

NSG Name: medical-chatbot-nsg
```

### Network Security Rules
```yaml
Allowed Inbound:
  - HTTPS (443) from *
  - HTTP (80) from * (redirect to HTTPS)
  
Allowed Outbound:
  - All Azure services
  - HTTPS to external APIs
```

---

## Security - Key Vault

### Key Vault Configuration
```yaml
Key Vault Name: _________________________________
Key Vault URL: https://_________________________.vault.azure.net/
Location: centralindia

Access Policies:
  - Your User Object ID: __________________________
  - App Service Managed Identity: __________________
  - Function App Managed Identity: _________________

Settings:
  Soft Delete: Enabled (90 days)
  Purge Protection: Enabled
  Access Model: Vault access policy
```

### Secrets Stored in Key Vault

#### Core Services
| Secret Name | Description | Value/Reference |
|-------------|-------------|-----------------|
| `openai-api-key` | Azure OpenAI API Key | `[FILL AFTER SETUP]` |
| `openai-endpoint` | Azure OpenAI Endpoint | `[FILL AFTER SETUP]` |
| `document-intelligence-key` | Document Intelligence Key | `[FILL AFTER SETUP]` |
| `document-intelligence-endpoint` | Doc Intelligence Endpoint | `[FILL AFTER SETUP]` |
| `ai-search-key` | Azure AI Search Admin Key | `[FILL AFTER SETUP]` |

#### Storage & Databases
| Secret Name | Description | Value/Reference |
|-------------|-------------|-----------------|
| `storage-connection-string` | Blob Storage Connection | `[FILL AFTER SETUP]` |
| `sql-connection-string` | SQL Database Connection | `[FILL AFTER SETUP]` |
| `cosmos-connection-string` | Cosmos DB Connection | `[FILL AFTER SETUP]` |
| `redis-connection-string` | Redis Cache Connection | `[FILL AFTER SETUP]` |

#### Communication & Monitoring
| Secret Name | Description | Value/Reference |
|-------------|-------------|-----------------|
| `app-insights-connection-string` | Application Insights | `[FILL AFTER SETUP]` |
| `communication-services-key` | SMS/Email Service | `[FILL AFTER SETUP]` |

#### Authentication
| Secret Name | Description | Value/Reference |
|-------------|-------------|-----------------|
| `b2c-client-id` | Azure AD B2C App ID | `[FILL AFTER SETUP]` |
| `b2c-client-secret` | Azure AD B2C Secret | `[FILL AFTER SETUP]` |
| `jwt-secret-key` | JWT Token Secret | `[GENERATE RANDOM]` |

---

## Storage Services

### Azure Blob Storage
```yaml
Storage Account Name: _____________________________
Storage Account Type: StorageV2 (general purpose v2)
Replication: LRS (Locally Redundant)
Performance: Standard
Access Tier: Hot
Location: centralindia

Primary Endpoints:
  Blob: https://_________________________.blob.core.windows.net/
  Table: https://_________________________.table.core.windows.net/
  Queue: https://_________________________.queue.core.windows.net/
  File: https://_________________________.file.core.windows.net/

Access Keys:
  Key 1: ___________________________________________
  Key 2: ___________________________________________

Connection String:
  Primary: _________________________________________
  Secondary: _______________________________________
```

#### Blob Containers
| Container Name | Access Level | Purpose |
|----------------|--------------|---------|
| `prescription-uploads` | Private | User prescription images |
| `extracted-data` | Private | OCR extraction results (JSON) |
| `medical-images` | Private | X-rays, scans, lab reports |

### Azure Redis Cache
```yaml
Redis Cache Name: _________________________________
Tier: Basic C1 (1 GB)
Location: centralindia

Connection Details:
  Host: _________________________.redis.cache.windows.net
  Port (SSL): 6380
  Port (Non-SSL): 6379 [Disabled]

Access Keys:
  Primary Key: _____________________________________
  Secondary Key: ___________________________________

Connection String (SSL):
  ____________________________.redis.cache.windows.net:6380,password=_________________________,ssl=True
```

---

## Database Services

### Azure SQL Database

#### SQL Server
```yaml
Server Name: _______________________________.database.windows.net
Location: centralindia
Version: 12.0
Admin Login: sqladmin

Admin Password: ___________________________________
[Store in Key Vault and password manager]

Server Firewall Rules:
  - AllowAzureServices (0.0.0.0)
  - AllowMyIP: [YOUR_IP_ADDRESS]
```

#### Databases
**Database 1: User Data**
```yaml
Database Name: medicalchatbot-users
Service Tier: Standard S2 (50 DTUs)
Max Size: 250 GB
Collation: SQL_Latin1_General_CP1_CI_AS

Tables:
  - Users
  - Prescriptions
  - PrescriptionMedicines
  - UserProfiles
```

**Database 2: Drug Information**
```yaml
Database Name: medicalchatbot-drugs
Service Tier: Standard S2 (50 DTUs)
Max Size: 250 GB
Collation: SQL_Latin1_General_CP1_CI_AS

Tables:
  - DrugDatabase
  - DrugInteractions
  - BrandGenericMapping
```

#### Connection Strings
```yaml
ADO.NET:
Server=tcp:____________________.database.windows.net,1433;
Initial Catalog=medicalchatbot-users;
Persist Security Info=False;
User ID=sqladmin;
Password=__________________________;
MultipleActiveResultSets=False;
Encrypt=True;
TrustServerCertificate=False;
Connection Timeout=30;

ODBC:
Driver={ODBC Driver 18 for SQL Server};
Server=tcp:____________________.database.windows.net,1433;
Database=medicalchatbot-users;
Uid=sqladmin;
Pwd=__________________________;
Encrypt=yes;
TrustServerCertificate=no;

Python (pyodbc):
Driver={ODBC Driver 18 for SQL Server};
Server=tcp:____________________.database.windows.net,1433;
Database=medicalchatbot-users;
Uid=sqladmin;
Pwd=__________________________;
Encrypt=yes;
TrustServerCertificate=no;
```

### Azure Cosmos DB
```yaml
Account Name: _____________________________________
API: Core (SQL)
Location: centralindia
Consistency Level: Session
Multi-region Writes: Disabled

Primary Endpoint:
  https://_________________________.documents.azure.com:443/

Primary Key: ______________________________________
Secondary Key: ____________________________________

Database Name: medicalchatbot

Containers:
  - Name: conversations
    Partition Key: /user_id
    Throughput: 400 RU/s (autoscale)
  
  - Name: messages
    Partition Key: /conversation_id
    Throughput: 400 RU/s (autoscale)

Connection String:
AccountEndpoint=https://_________________.documents.azure.com:443/;
AccountKey=________________________________________;
```

---

## AI Services

### Azure OpenAI Service
```yaml
Resource Name: ____________________________________
Location: eastus (or swedencentral for GPT-4)
Pricing Tier: Standard S0

Endpoint: https://__________________.openai.azure.com/
API Version: 2024-08-01-preview

API Keys:
  Key 1: ___________________________________________
  Key 2: ___________________________________________
```

#### Model Deployments
**Deployment 1: GPT-4 (Orchestrator)**
```yaml
Deployment Name: gpt-4-deployment
Model: gpt-4
Model Version: 0613
Capacity (TPM): 80,000
Capacity (RPM): 800

Usage Configuration:
  Temperature: 0.3
  Max Tokens: 500
  Top P: 0.9
```

**Deployment 2: Text Embeddings**
```yaml
Deployment Name: embedding-deployment
Model: text-embedding-ada-002
Model Version: 2
Capacity (TPM): 120,000
Dimensions: 1536
```

### Azure Document Intelligence
```yaml
Resource Name: ____________________________________
Location: centralindia
Pricing Tier: S0

Endpoint: https://____________________.cognitiveservices.azure.com/
API Version: 2023-07-31

API Keys:
  Key 1: ___________________________________________
  Key 2: ___________________________________________

Custom Models:
  - Model ID: custom-prescription-model
    Training Status: [Trained/Not Trained]
    Accuracy: _______% (target: >85%)
```

### Azure AI Search (Vector Database)
```yaml
Service Name: _____________________________________
Location: centralindia
Pricing Tier: Standard S1
Replicas: 2
Partitions: 1
Storage: 25 GB

Search Endpoint: https://_________________.search.windows.net
API Version: 2024-05-01-preview

Admin Keys:
  Primary Key: _____________________________________
  Secondary Key: ___________________________________

Query Keys:
  Key 1: ___________________________________________
  Key 2: ___________________________________________

Indexes Created:
  - medical-knowledge-index
  - drug-database-index
  - user-documents-index
```

### Azure AI Foundry (Machine Learning)
```yaml
Workspace Name: ___________________________________
Location: centralindia
Resource Group: medical-chatbot-rg

Workspace URL: https://ml.azure.com/?wsid=/subscriptions/______

Compute Instances:
  [List your compute instances]

Model Endpoints:
```

**Endpoint 1: Med42-Llama3**
```yaml
Endpoint Name: med42-llama3-endpoint
Model: m42-health-llama3-med42-70b
Instance Type: Standard_NC24ads_A100_v4
Instance Count: 2

Scoring URI: https://_________________.inference.ml.azure.com/score
Swagger URI: https://_________________.inference.ml.azure.com/swagger.json

API Key: __________________________________________
```

**Endpoint 2: BioGPT**
```yaml
Endpoint Name: biogpt-endpoint
Model: microsoft-biogpt-large
Instance Type: Standard_NC12s_v3
Instance Count: 1

Scoring URI: https://_________________.inference.ml.azure.com/score
Swagger URI: https://_________________.inference.ml.azure.com/swagger.json

API Key: __________________________________________
```

**Endpoint 3: BiomedCLIP**
```yaml
Endpoint Name: biomedclip-endpoint
Model: BiomedCLIP-PubMedBERT-base
Instance Type: Standard_D4s_v3
Instance Count: 1

Scoring URI: https://_________________.inference.ml.azure.com/score
Swagger URI: https://_________________.inference.ml.azure.com/swagger.json

API Key: __________________________________________
```

---

## Compute Services

### Azure App Service
```yaml
App Service Plan:
  Name: medical-chatbot-plan
  Pricing Tier: S1 (Standard)
  Operating System: Linux
  Workers: 2
  Location: centralindia

Web App:
  Name: ____________________________________________
  URL: https://_________________________.azurewebsites.net
  Runtime: Python 3.11
  Always On: Enabled
  HTTPS Only: Enabled

Deployment Settings:
  Deployment Method: [GitHub Actions / Azure DevOps / FTP]
  Repository: ______________________________________
  Branch: main

Managed Identity:
  System Assigned: Enabled
  Principal ID: ____________________________________
  Tenant ID: _______________________________________

App Settings (Environment Variables):
  KEYVAULT_URL: https://_____________.vault.azure.net/
  ENVIRONMENT: production
  PYTHON_VERSION: 3.11
  [Add more as needed]
```

### Azure Functions
```yaml
Function App Name: ________________________________
URL: https://_________________________.azurewebsites.net
Runtime: Python 3.11
Hosting Plan: Consumption
Location: centralindia

Storage Account (for Functions):
  Name: _____________________________________________
  Connection String: ________________________________

Managed Identity:
  System Assigned: Enabled
  Principal ID: ____________________________________

Functions Deployed:
  - process-document-async (Blob Trigger)
  - send-notifications (Timer Trigger)
  - cleanup-old-data (Timer Trigger)
  - generate-reports (HTTP Trigger)

Function Keys:
  Host Key (Master): ________________________________
  Function Keys: ____________________________________
```

---

## Networking & Gateway

### Azure CDN
```yaml
CDN Profile Name: _________________________________
Pricing Tier: Standard Microsoft
Location: Global

CDN Endpoint:
  Name: _____________________________________________
  URL: https://_________________________.azureedge.net
  Origin: [Your App Service URL]
  Origin Host Header: [Your App Service URL]

Custom Domain: [If configured]
  Domain: ___________________________________________
  SSL Certificate: __________________________________
```

### Azure Application Gateway
```yaml
Gateway Name: _____________________________________
Tier: WAF V2
Location: centralindia
Capacity: 2-10 (autoscale)

Frontend:
  Public IP Name: appgw-public-ip
  Public IP Address: ________________________________

Backend Pools:
  - Name: api-backend-pool
    Targets: [Your App Service URL]

HTTP Settings:
  - Name: api-http-settings
    Port: 443
    Protocol: HTTPS
    Cookie-based affinity: Disabled

Listeners:
  - Name: https-listener
    Port: 443
    Protocol: HTTPS
    SSL Certificate: __________________________________

Rules:
  - Name: api-routing-rule
    Listener: https-listener
    Backend Pool: api-backend-pool

WAF Configuration:
  Mode: Prevention
  Rule Set: OWASP 3.2
```

### Azure API Management
```yaml
APIM Instance Name: _______________________________
Pricing Tier: Developer (or Standard for production)
Location: centralindia

Gateway URL: https://_________________.azure-api.net
Management API: https://_________________.management.azure-api.net
Developer Portal: https://_________________.developer.azure-api.net

Publisher Details:
  Publisher Name: Medical Chatbot
  Publisher Email: __________________________________

Managed Identity:
  System Assigned: Enabled
  Principal ID: ____________________________________

Subscription Keys:
  Primary Key: _____________________________________
  Secondary Key: ___________________________________

APIs Configured:
  - Medical Chatbot API v1
    Backend URL: [Your App Service URL]
    Base Path: /api/v1

Policies Applied:
  - Rate Limiting: 100 calls/minute per user
  - JWT Validation: Azure AD B2C
  - CORS: Enabled
  - Request/Response Logging: Enabled
```

---

## Authentication

### Azure AD B2C
```yaml
Tenant Name: medicalchatbot.onmicrosoft.com
Tenant ID: ________________________________________
Primary Domain: medicalchatbot.onmicrosoft.com

Location: United States (or closest to your region)

App Registration:
  Application Name: Medical Chatbot Web App
  Application (client) ID: __________________________
  Directory (tenant) ID: ____________________________
  
Client Secrets:
  Secret 1 Description: production-secret
  Secret 1 Value: ___________________________________
  Secret 1 Expires: _________________________________

Redirect URIs:
  - https://_________________________.azurewebsites.net/auth/callback
  - https://localhost:3000/auth/callback (for dev)
  - [Add production domain]

User Flows:
  Sign up and sign in:
    Name: B2C_1_signupsignin
    Identity Providers: Email signup
    User Attributes: Email, Display Name, Phone Number

Authority URL:
https://medicalchatbot.b2clogin.com/medicalchatbot.onmicrosoft.com/B2C_1_signupsignin

Token Endpoint:
https://medicalchatbot.b2clogin.com/medicalchatbot.onmicrosoft.com/B2C_1_signupsignin/oauth2/v2.0/token

JWKS Endpoint:
https://medicalchatbot.b2clogin.com/medicalchatbot.onmicrosoft.com/B2C_1_signupsignin/discovery/v2.0/keys
```

---

## Monitoring & Logging

### Application Insights
```yaml
Resource Name: ____________________________________
Location: centralindia
Workspace-based: Yes

Instrumentation Key: ______________________________
Connection String: ________________________________

Log Analytics Workspace:
  Name: medical-chatbot-logs
  Workspace ID: ____________________________________
  Primary Key: _____________________________________

Application Map: Enabled
Live Metrics: Enabled
Sampling Rate: Adaptive (default)
Data Retention: 90 days
```

### Azure Monitor
```yaml
Action Groups:
  - Name: medical-chatbot-alerts
    Short Name: MedAlert
    Email Receivers:
      - Name: admin
        Email: _______________________________________
    SMS Receivers: [Optional]
      - Name: on-call
        Phone: _______________________________________

Alert Rules:
  1. High Error Rate
     Condition: Exceptions > 10 in 5 minutes
     Severity: Critical
     Action Group: medical-chatbot-alerts
  
  2. Slow Response Time
     Condition: Avg response time > 5 seconds
     Severity: Warning
     Action Group: medical-chatbot-alerts
  
  3. High Costs
     Condition: Daily cost > $100
     Severity: Warning
     Action Group: medical-chatbot-alerts
```

### Azure Communication Services
```yaml
Resource Name: ____________________________________
Location: Global
Data Location: United States

Connection String: ________________________________

Email Service:
  Domain: ___________________________________________
  From Email: _______________________________________

SMS Service:
  Phone Number: [If purchased]
  Capabilities: SMS Outbound
```

---

## Environment Variables (.env)

### Create this file in your project root (DO NOT COMMIT!)

```bash
# ==========================================
# AZURE CONFIGURATION
# ==========================================

# Subscription
AZURE_SUBSCRIPTION_ID=
AZURE_TENANT_ID=
AZURE_RESOURCE_GROUP=medical-chatbot-rg
AZURE_LOCATION=centralindia

# ==========================================
# KEY VAULT
# ==========================================
KEYVAULT_NAME=
KEYVAULT_URL=https://.vault.azure.net/

# ==========================================
# STORAGE
# ==========================================
STORAGE_ACCOUNT_NAME=
STORAGE_ACCOUNT_KEY=
STORAGE_CONNECTION_STRING=
BLOB_CONTAINER_PRESCRIPTIONS=prescription-uploads
BLOB_CONTAINER_EXTRACTED=extracted-data
BLOB_CONTAINER_IMAGES=medical-images

# ==========================================
# DATABASES
# ==========================================

# SQL Database
SQL_SERVER=.database.windows.net
SQL_DATABASE=medicalchatbot-users
SQL_USERNAME=sqladmin
SQL_PASSWORD=
SQL_CONNECTION_STRING=

# Cosmos DB
COSMOS_ACCOUNT=
COSMOS_ENDPOINT=https://.documents.azure.com:443/
COSMOS_KEY=
COSMOS_DATABASE=medicalchatbot
COSMOS_CONTAINER_CONVERSATIONS=conversations
COSMOS_CONTAINER_MESSAGES=messages

# Redis Cache
REDIS_HOST=.redis.cache.windows.net
REDIS_PORT=6380
REDIS_PASSWORD=
REDIS_CONNECTION_STRING=

# ==========================================
# AI SERVICES
# ==========================================

# Azure OpenAI
OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-08-01-preview
OPENAI_ENDPOINT=https://.openai.azure.com/
OPENAI_API_KEY=
OPENAI_GPT4_DEPLOYMENT=gpt-4-deployment
OPENAI_EMBEDDING_DEPLOYMENT=embedding-deployment

# Document Intelligence
DOCUMENT_INTELLIGENCE_ENDPOINT=https://.cognitiveservices.azure.com/
DOCUMENT_INTELLIGENCE_KEY=
DOCUMENT_INTELLIGENCE_MODEL=custom-prescription-model

# Azure AI Search
AI_SEARCH_ENDPOINT=https://.search.windows.net
AI_SEARCH_KEY=
AI_SEARCH_API_VERSION=2024-05-01-preview
AI_SEARCH_INDEX_MEDICAL=medical-knowledge-index
AI_SEARCH_INDEX_DRUGS=drug-database-index
AI_SEARCH_INDEX_USERS=user-documents-index

# Azure ML Endpoints
AML_MED42_ENDPOINT=https://.inference.ml.azure.com/score
AML_MED42_KEY=
AML_BIOGPT_ENDPOINT=https://.inference.ml.azure.com/score
AML_BIOGPT_KEY=
AML_BIOMEDCLIP_ENDPOINT=https://.inference.ml.azure.com/score
AML_BIOMEDCLIP_KEY=

# ==========================================
# AUTHENTICATION
# ==========================================
B2C_TENANT_NAME=medicalchatbot
B2C_TENANT_ID=
B2C_CLIENT_ID=
B2C_CLIENT_SECRET=
B2C_USER_FLOW=B2C_1_signupsignin
B2C_AUTHORITY=https://medicalchatbot.b2clogin.com/medicalchatbot.onmicrosoft.com/B2C_1_signupsignin

JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ==========================================
# COMPUTE
# ==========================================
APP_SERVICE_URL=https://.azurewebsites.net
FUNCTION_APP_URL=https://.azurewebsites.net
API_GATEWAY_URL=https://.azure-api.net

# ==========================================
# MONITORING
# ==========================================
APPLICATIONINSIGHTS_CONNECTION_STRING=
APPLICATIONINSIGHTS_INSTRUMENTATION_KEY=
LOG_LEVEL=INFO

# ==========================================
# COMMUNICATION
# ==========================================
COMMUNICATION_SERVICES_CONNECTION_STRING=
EMAIL_FROM_ADDRESS=
SMS_FROM_NUMBER=

# ==========================================
# APPLICATION SETTINGS
# ==========================================
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=.azurewebsites.net,localhost
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_DAY=5000

# File Upload
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=jpg,jpeg,png,pdf

# AI Configuration
DEFAULT_MODEL_TEMPERATURE=0.5
DEFAULT_MAX_TOKENS=1024
ENABLE_RAG=True
RAG_TOP_K=5

# ==========================================
# EXTERNAL SERVICES (if any)
# ==========================================
# SENDGRID_API_KEY=
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
```

---

## Connection Strings

### Quick Copy-Paste Connection Strings

#### Azure SQL Database (Python - SQLAlchemy)
```python
connection_string = (
    "mssql+pyodbc://sqladmin:PASSWORD@SERVER.database.windows.net:1433/"
    "medicalchatbot-users?driver=ODBC+Driver+18+for+SQL+Server"
)
```

#### Azure SQL Database (Python - pyodbc)
```python
connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:SERVER.database.windows.net,1433;"
    "Database=medicalchatbot-users;"
    "Uid=sqladmin;"
    "Pwd=PASSWORD;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)
```

#### Cosmos DB (Python)
```python
from azure.cosmos import CosmosClient

endpoint = "https://ACCOUNT.documents.azure.com:443/"
key = "YOUR_KEY"
client = CosmosClient(endpoint, key)
```

#### Blob Storage (Python)
```python
from azure.storage.blob import BlobServiceClient

connection_string = "YOUR_CONNECTION_STRING"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
```

#### Redis Cache (Python)
```python
import redis

r = redis.Redis(
    host='HOST.redis.cache.windows.net',
    port=6380,
    password='YOUR_KEY',
    ssl=True
)
```

#### Azure OpenAI (Python)
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="YOUR_KEY",
    api_version="2024-08-01-preview",
    azure_endpoint="https://RESOURCE.openai.azure.com/"
)
```

---

## API Endpoints Reference

### Internal Azure Service Endpoints

#### Azure OpenAI
```
Endpoint: https://[RESOURCE].openai.azure.com/
Chat Completions: /openai/deployments/[DEPLOYMENT]/chat/completions?api-version=2024-08-01-preview
Embeddings: /openai/deployments/[DEPLOYMENT]/embeddings?api-version=2024-08-01-preview
```

#### Document Intelligence
```
Endpoint: https://[RESOURCE].cognitiveservices.azure.com/
Analyze Document: /formrecognizer/documentModels/[MODEL]:analyze?api-version=2023-07-31
Get Result: /formrecognizer/documentModels/[MODEL]/analyzeResults/[RESULT_ID]?api-version=2023-07-31
```

#### Azure AI Search
```
Endpoint: https://[RESOURCE].search.windows.net
Create Index: /indexes?api-version=2024-05-01-preview
Search: /indexes/[INDEX]/docs/search?api-version=2024-05-01-preview
Upload Docs: /indexes/[INDEX]/docs/index?api-version=2024-05-01-preview
```

### Your Application API Endpoints

#### Authentication
```
POST   /api/v1/auth/signup
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/verify
```

#### Documents
```
POST   /api/v1/documents/upload
GET    /api/v1/documents/{id}
GET    /api/v1/documents/list
DELETE /api/v1/documents/{id}
POST   /api/v1/documents/{id}/correct
```

#### Chat
```
POST   /api/v1/chat/message
GET    /api/v1/chat/history/{conversation_id}
GET    /api/v1/chat/conversations
DELETE /api/v1/chat/{conversation_id}
WS     /api/v1/chat/stream
```

#### Medicines
```
GET    /api/v1/medicines/{name}
GET    /api/v1/medicines/search?q={query}
GET    /api/v1/medicines/interactions?medicines={list}
POST   /api/v1/medicines/check-interaction
```

#### User Profile
```
GET    /api/v1/profile
PUT    /api/v1/profile
POST   /api/v1/profile/prescriptions
GET    /api/v1/profile/prescriptions
DELETE /api/v1/profile/prescriptions/{id}
```

---

## Additional Configuration Files

### .gitignore (IMPORTANT!)
```gitignore
# Environment variables
.env
.env.local
.env.production
Azure_Configuration_Master_Sheet.md

# Azure credentials
*.publishsettings
*.azurePubxml

# Keys and secrets
*.key
*.pem
secrets.json
config.production.json

# IDE
.vscode/
.idea/
*.swp

# Python
__pycache__/
*.pyc
venv/
env/

# Node
node_modules/
npm-debug.log

# OS
.DS_Store
Thumbs.db
```

### config.json Template
```json
{
  "azure": {
    "subscription_id": "",
    "resource_group": "medical-chatbot-rg",
    "location": "centralindia"
  },
  "services": {
    "openai": {
      "endpoint": "",
      "api_version": "2024-08-01-preview",
      "deployments": {
        "gpt4": "gpt-4-deployment",
        "embedding": "embedding-deployment"
      }
    },
    "storage": {
      "account_name": "",
      "containers": {
        "prescriptions": "prescription-uploads",
        "extracted": "extracted-data",
        "images": "medical-images"
      }
    },
    "databases": {
      "sql": {
        "server": "",
        "database": "medicalchatbot-users"
      },
      "cosmos": {
        "account": "",
        "database": "medicalchatbot"
      }
    }
  }
}
```

---

## Maintenance Schedule

### Regular Tasks

#### Daily
- [ ] Check Application Insights for errors
- [ ] Monitor costs in Cost Management
- [ ] Review failed requests in APIM

#### Weekly
- [ ] Review and rotate access logs
- [ ] Check storage usage
- [ ] Update budget alerts if needed

#### Monthly
- [ ] Rotate API keys (where possible)
- [ ] Review and update drug database
- [ ] Update medical knowledge base
- [ ] Security audit of access policies

#### Quarterly
- [ ] Review and optimize costs
- [ ] Update AI model deployments
- [ ] Retrain custom Document Intelligence model
- [ ] Review and update compliance documentation

---

## Emergency Contacts

### Azure Support
```
Azure Support Portal: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
Phone: [Your region's support number]
Severity Levels:
  - Critical (A): Production down
  - High (B): Significant impact
  - Medium (C): Moderate impact
  - Low (D): Minimal impact
```

### Team Contacts
```
Technical Lead: _______________________________________
DevOps Engineer: ______________________________________
On-Call Engineer: _____________________________________
Product Manager: ______________________________________
```

### Service Status
```
Azure Status: https://status.azure.com
Service Health: https://portal.azure.com/#blade/Microsoft_Azure_Health/AzureHealthBrowseBlade
```

---

## Backup & Disaster Recovery

### Backup Configuration
```yaml
SQL Database:
  Automated Backups: Enabled
  Retention: 7 days
  Point-in-time Restore: Enabled
  Geo-replication: [Enabled/Disabled]

Blob Storage:
  Soft Delete: Enabled (7 days)
  Versioning: Enabled
  Snapshot Policy: Daily

Cosmos DB:
  Continuous Backup: Enabled
  Backup Interval: Every 4 hours
  Backup Retention: 30 days

Manual Backup Schedule:
  - Weekly full backup: Every Sunday 2:00 AM UTC
  - Daily incremental: Every day 2:00 AM UTC
```

### Disaster Recovery Plan
```yaml
Recovery Point Objective (RPO): 4 hours
Recovery Time Objective (RTO): 8 hours

Failover Regions:
  Primary: Central India
  Secondary: South India

DR Runbook:
  1. Assess incident severity
  2. Notify team and stakeholders
  3. Initiate failover procedures
  4. Verify service restoration
  5. Post-incident review
```

---

## Security Checklist

### Pre-Production Security Review
- [ ] All secrets stored in Key Vault
- [ ] Managed identities enabled where possible
- [ ] No hardcoded credentials in code
- [ ] HTTPS enforced on all endpoints
- [ ] API rate limiting configured
- [ ] WAF enabled and configured
- [ ] Network security groups configured
- [ ] SQL firewall rules restrictive
- [ ] Blob storage containers private
- [ ] Soft delete enabled on critical resources
- [ ] Audit logging enabled
- [ ] Application Insights configured
- [ ] Budget alerts configured
- [ ] Backup strategy tested
- [ ] Disaster recovery plan documented
- [ ] Compliance requirements met (DPDPA, etc.)

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Oct 15, 2025 | Initial Setup | Created configuration template |
| | | | |

---

## Notes & Reminders

### Important Notes
1. **NEVER commit this file to Git** - Add to .gitignore immediately
2. Store a backup copy in a secure password manager (1Password, LastPass, etc.)
3. Rotate keys every 90 days for compliance
4. Review access policies monthly
5. Update this document whenever configuration changes

### Quick Commands to Get Values

```bash
# Get OpenAI Key
az cognitiveservices account keys list --name [OPENAI_NAME] --resource-group medical-chatbot-rg --query key1 -o tsv

# Get Storage Connection String
az storage account show-connection-string --name [STORAGE_NAME] --resource-group medical-chatbot-rg --query connectionString -o tsv

# Get SQL Connection String
echo "Server=tcp:[SQL_SERVER].database.windows.net,1433;Database=medicalchatbot-users;User ID=sqladmin;Password=[PASSWORD];Encrypt=true;"

# Get Key Vault Secret
az keyvault secret show --vault-name [KEYVAULT_NAME] --name openai-api-key --query value -o tsv

# List all resources
az resource list --resource-group medical-chatbot-rg --output table
```

---

**END OF CONFIGURATION SHEET**

**Last Updated:** [FILL IN DATE]  
**Next Review:** [FILL IN DATE]  
**Owner:** [YOUR NAME]

---

> 🔒 **Remember:** Keep this document secure and updated. This is your single source of truth for all Azure configurations.

