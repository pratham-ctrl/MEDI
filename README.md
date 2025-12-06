# Medi Project

Medi is a comprehensive medical chatbot and document management backend system supported by Azure cloud infrastructure. The codebase includes API services, intelligent agents for medical question answering, document uploads, and integration with cloud storage/databases.

## Project Structure

```
backend/
  app/
    agents/       # AI and document agents for medical QA and orchestration
    api/          # FastAPI endpoints and route handlers
    config.py     # Configuration and settings
    main.py       # FastAPI app entrypoint
    models/       # SQLAlchemy or Pydantic models for chat, users, docs, drugs
    services/     # Azure cloud services integrations
    utils/        # Utility helpers (auth, embeddings, vector store, etc)
  requirements.txt # Python dependencies for backend
  scripts/        # Utility scripts for database/storage setup
  tests/          # Test suite for backend app

docs/             # Guides, architecture diagrams, and setup documentation
medichat/         # Frontend code/html and screenshots for UI flows
```

## Key Features

- **Authentication & User Management**
- **Medical QA Agents** powered by LLMs
- **Secure Document Upload & Retrieval**
- **Drug Information Database**
- **Integration with Azure (Cognitive Services, Blob Storage, SQL/Cosmos DB)**
- **Profile management and chat with agents**

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd medi/backend
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   (Or use a virtual environment as preferred.)

3. **Environment variables:**
   - Copy `test/env.example` as your local `.env` file and set your Azure/cloud keys and database configs.
   - See documentation in `/docs` for required secrets/setup.

4. **Run database & Azure resource setup:**
   - Scripts for initializing Cosmos DB, Blob Storage, and SQL schemas are in `backend/scripts/`.
   - Example:
     ```bash
     python scripts/setup_cosmos_db.py
     python scripts/create_blob_containers.py
     python scripts/setup_sql_schema.py
     ```

5. **Start Backend API:**
   ```bash
   uvicorn app.main:app --reload
   ```
   - The API will be available at `http://localhost:8000` by default.

6. **Run Tests:**
   ```bash
   pytest
   ```

## Documentation & Guides

- **Full architecture and Azure setup:**
  - See `/docs/complete architecture/Complete_Architecture_Documentation.md`
  - Azure setup guide: `/docs/azure service setup guide/Azure_Services_Setup_Guide.md`
- **Product requirements & diagrams:**
  - `/docs/prd/medical_chatbot_prd.md`
  - `/docs/diagrams/` for SVG and Mermaid architecture diagrams

## Scripts

- For populating and testing cloud resources, refer to the scripts in `backend/scripts/`:
  - Indexing, database population, and document intelligence tools
  - See the top of each script for its usage instructions

## Frontend

- Frontend HTML samples, flows, and screenshots are in the `medichat/` directory.
- Frontend is not included as a complete React/Vue app in this codebase.

---

## License

Consult the project owner for license details, usage, and contribution guidelines.
