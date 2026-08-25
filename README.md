App link: https://marketmind-ai-i66o.onrender.com/ 
# MarketMind AI

(Since it's a free platform, it will take time to show upon clicking on link or may crash bec of limited RAM and other resources provided by platform)
### AI-Powered Job Market Intelligence Platform with Hybrid Retrieval-Augmented Generation

MarketMind AI is an end-to-end job market intelligence platform designed to collect, normalize, enrich, analyze, retrieve, and interpret job-market data from multiple sources.

The system combines a **FastAPI backend, PostgreSQL, automated data pipelines, NLP/ML-based job enrichment, vector retrieval, LangChain, ChromaDB, Hugging Face embeddings, Groq-hosted LLM inference, and a React frontend** to transform raw job postings into structured market intelligence.

Rather than functioning as a conventional job listing application, MarketMind AI provides two complementary intelligence layers:

1. **Structured analytics** over normalized job-market data.
2. **Natural-language market intelligence** through a hybrid RAG pipeline combining structured database evidence with semantic retrieval.

---

## Overview

Online job postings contain valuable information about:

- skill demand,
- hiring companies,
- job families,
- experience requirements,
- geographic distribution,
- remote-work availability,
- employment types,
- and broader hiring trends.

However, job data collected from different sources is heterogeneous and difficult to analyze directly.

MarketMind AI implements an end-to-end pipeline:

```text
Job Sources
    │
    ▼
Data Collection
    │
    ▼
Transformation & Normalization
    │
    ▼
PostgreSQL
    │
    ▼
Job Enrichment
    │
    ├──────────────► Analytics Engine
    │
    ▼
Document Construction
    │
    ▼
Embedding Generation
    │
    ▼
Chroma Vector Store
    │
    ▼
Hybrid Retrieval
    │
    ▼
Context Construction
    │
    ▼
Groq LLM
    │
    ▼
Evidence-Grounded Market Intelligence
```

The processed data is exposed through a FastAPI REST API and consumed by a React-based dashboard.

---

# Key Features

## Multi-Source Job Collection

The project contains a modular collection layer for retrieving job postings from multiple sources.

Current collector modules include:

```text
collectors/
├── adzuna.py
├── arbeitnow.py
├── remoteok.py
├── weworkremotely.py
├── manager.py
└── base.py
```

The collector architecture separates source-specific acquisition logic from downstream processing.

This allows additional job sources to be incorporated without redesigning the rest of the pipeline.

---

## ETL and Data Normalization

Raw job postings from different sources may use inconsistent schemas, location formats, titles, skills, and metadata.

MarketMind AI processes collected records through transformation and normalization stages before persistence.

The pipeline contains components for:

- source-specific transformation,
- location normalization,
- skill extraction,
- skill normalization,
- job enrichment,
- semantic job classification,
- duplicate-aware loading,
- and enrichment of existing records.

Relevant modules include:

```text
pipeline/
├── transformer.py
├── arbeitnow_transformer.py
├── remoteok_transformer.py
├── load.py
├── enrich_jobs.py
├── enrich_existing.py
├── normalize_existing_locations.py
└── enrichment/
    ├── database_enricher.py
    ├── existing_skill_enricher.py
    ├── job_enricher.py
    ├── location_normalizer.py
    ├── semantic_classifier.py
    ├── skill_extractor.py
    └── skill_normalizer.py
```

---

## PostgreSQL Data Layer

Structured job-market information is stored in PostgreSQL.

The database layer uses:

- **SQLAlchemy** for ORM/database access,
- **Alembic** for schema migrations,
- repository abstractions for data access.

Core entities include:

- Jobs
- Companies
- Locations
- Skills

Repository modules isolate database operations from application and intelligence logic.

```text
database/
├── connection.py
├── models.py
└── repositories/
    ├── base_repository.py
    ├── company_repository.py
    ├── job_repository.py
    ├── location_repository.py
    ├── skill_repository.py
    └── unit_of_work.py
```

The production database is hosted using **Neon PostgreSQL**.

---

# AI / ML Layer

MarketMind AI incorporates machine-learning and NLP components during job enrichment and retrieval.

## Semantic Job Classification

The enrichment pipeline contains a semantic classifier for mapping heterogeneous job titles/descriptions into normalized job families.

The repository also contains evaluation pipelines for comparing classification strategies.

```text
pipeline/
├── evaluate_attributes.py
├── evaluate_hybrid.py
├── evaluate_rules_v2.py
├── evaluate_rules_v3.py
├── evaluate_semantic.py
└── evaluate_transformer.py
```

Evaluation datasets and prediction outputs are maintained under:

```text
datasets/evaluation/
```

This enables classification approaches to be evaluated against labeled data rather than relying solely on manually defined mappings.

---

## Skill Extraction and Normalization

Job descriptions are processed to identify relevant technical and professional skills.

Extracted skills are normalized before being associated with jobs, enabling aggregate analyses such as:

- most demanded skills,
- skill frequency,
- skill demand across job families,
- and skill-based retrieval.

---

# Retrieval-Augmented Generation

The AI intelligence layer uses a Retrieval-Augmented Generation architecture to answer natural-language questions about the job market.

The RAG subsystem includes:

```text
rag/
├── document_builder.py
├── index_sync.py
├── retriever.py
└── vector_store.py
```

## Embeddings

Job documents are converted into vector representations using a Sentence Transformer embedding model.

Configured embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The embedding layer enables semantic retrieval based on meaning rather than exact keyword matching.

---

## ChromaDB Vector Store

Generated embeddings are stored in a Chroma vector collection.

The vector index supports semantic retrieval of job postings relevant to a user's question.

Example:

```text
User:
"What skills are commonly required for remote software engineering jobs?"

                    │
                    ▼

            Query Processing

                    │
          ┌─────────┴─────────┐
          ▼                   ▼

Structured Retrieval     Semantic Retrieval
   PostgreSQL                 Chroma
          │                   │
          └─────────┬─────────┘
                    ▼

              Context Builder

                    ▼

                Groq LLM

                    ▼

          Evidence-Grounded Answer
```

---

# Hybrid Retrieval Architecture

MarketMind AI is designed around hybrid retrieval rather than relying exclusively on vector similarity.

The intelligence layer contains:

```text
intelligence/
├── answer_generator.py
├── citation_builder.py
├── context_builder.py
├── hybrid_retriever.py
├── intelligence_service.py
├── llm_service.py
├── query_engine.py
├── query_planner.py
└── response_synthesizer.py
```

The architecture separates:

- query planning,
- structured retrieval,
- semantic retrieval,
- context construction,
- LLM interaction,
- response synthesis,
- and evidence/citation construction.

This separation makes the intelligence pipeline easier to extend and evaluate.

---

# LLM Integration

Large-language-model inference is performed through the Groq API.

Current configuration:

```text
LLM_MODEL=llama-3.3-70b-versatile
```

The LLM operates over retrieved context rather than being treated as the source of job-market data.

This design aims to produce responses grounded in the application's collected dataset.

---

# Market Analytics

The analytics layer provides structured insights over the PostgreSQL dataset.

Available analytics include:

- total jobs,
- total companies,
- total locations,
- unique skills,
- remote job percentage,
- job-family distribution,
- top skills,
- remote-work distribution,
- experience distribution,
- employment-type distribution,
- country distribution,
- and company distribution.

Relevant modules:

```text
analytics/
├── market_analytics.py
└── skill_analytics.py
```

---

# REST API

The backend is implemented using FastAPI.

API routers are separated by responsibility:

```text
api/routers/
├── analytics.py
├── intelligence.py
├── jobs.py
└── system.py
```

Major endpoint groups include:

```text
/analytics/*
/jobs/*
/intelligence/*
/system/*
```

Examples:

```http
GET /analytics/overview
GET /analytics/job-families
GET /analytics/skills
GET /analytics/remote
GET /analytics/experience
GET /analytics/job-types
GET /analytics/countries
GET /analytics/companies

GET /jobs
GET /jobs/{job_id}

POST /intelligence/ask

GET /system/dataset-status
```

FastAPI also provides interactive API documentation during local development.

```text
http://127.0.0.1:8000/docs
```

---

# Frontend

The user interface is implemented using React and Vite.

Main pages include:

```text
frontend/src/pages/
├── Dashboard.jsx
├── Intelligence.jsx
├── JobDetail.jsx
└── JobExplorer.jsx
```

The frontend communicates with FastAPI through an Axios API client.

Major user-facing capabilities include:

### Dashboard

Visualizes job-market statistics and distributions.

### Job Explorer

Provides access to processed job records and filtering capabilities.

### Job Detail

Displays detailed information for individual job records.

### Ask AI

Provides a natural-language interface to the job-market intelligence pipeline.

---

# Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, Axios |
| Backend | FastAPI, Python, Uvicorn |
| Database | PostgreSQL, SQLAlchemy |
| Database Migrations | Alembic |
| Data Processing | Pandas |
| Collection | Requests, BeautifulSoup, lxml |
| ML / NLP | PyTorch, Transformers, Sentence Transformers |
| Embeddings | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| RAG | LangChain |
| LLM | Llama 3.3 70B via Groq |
| Backend Deployment | Render |
| Frontend Deployment | Render |
| Production Database | Neon PostgreSQL |
| Containerization | Docker |
| Version Control | Git, GitHub |

---

# Project Architecture

```text
                         ┌───────────────────────┐
                         │     Job Sources       │
                         │                       │
                         │ Adzuna / Arbeitnow /  │
                         │ RemoteOK / WWR        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      Collectors       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ Transformation &      │
                         │ Normalization         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │      PostgreSQL       │
                         │        Neon           │
                         └───────┬───────┬───────┘
                                 │       │
                    ┌────────────┘       └────────────┐
                    ▼                                 ▼
          ┌──────────────────┐              ┌──────────────────┐
          │ Analytics Engine │              │ Enrichment / NLP │
          └────────┬─────────┘              └────────┬─────────┘
                   │                                 │
                   │                                 ▼
                   │                        ┌──────────────────┐
                   │                        │ Document Builder │
                   │                        └────────┬─────────┘
                   │                                 │
                   │                                 ▼
                   │                        ┌──────────────────┐
                   │                        │ Embedding Model  │
                   │                        └────────┬─────────┘
                   │                                 │
                   │                                 ▼
                   │                        ┌──────────────────┐
                   │                        │     ChromaDB     │
                   │                        └────────┬─────────┘
                   │                                 │
                   └──────────────┐     ┌────────────┘
                                  ▼     ▼
                            ┌─────────────────┐
                            │ Hybrid Retrieval│
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Context Builder │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │    Groq LLM     │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ FastAPI REST API│
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ React Frontend  │
                            └─────────────────┘
```

---

# Repository Structure

```text
MarketMind-AI/
│
├── ai/
│
├── analytics/
│   ├── market_analytics.py
│   └── skill_analytics.py
│
├── api/
│   ├── main.py
│   ├── schemas.py
│   └── routers/
│
├── collectors/
│
├── config/
│   └── settings.py
│
├── database/
│   ├── connection.py
│   ├── models.py
│   └── repositories/
│
├── datasets/
│   └── evaluation/
│
├── domain/
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/
│       ├── components/
│       └── pages/
│
├── intelligence/
│
├── pipeline/
│   └── enrichment/
│
├── rag/
│
├── services/
│
├── ui/
│
├── utils/
│
├── alembic/
│
├── .env.example
├── .gitignore
├── .dockerignore
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Local Development

## Prerequisites

Install:

- Python
- Node.js / npm
- Git

Docker is optional for local development if the application is run directly through Python and Node.

---

## 1. Clone the Repository

```bash
git clone <repository-url>
cd marketmind-ai
```

---

## 2. Create Python Virtual Environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create:

```text
.env
```

using `.env.example` as the template.

Typical configuration:

```env
APP_NAME=AI Job Market Intelligence Platform
APP_VERSION=1.2.0
APP_ENV=development

DB_HOST=<database-host>
DB_PORT=5432
DB_NAME=<database-name>
DB_USER=<database-user>
DB_PASSWORD=<database-password>

GROQ_API_KEY=<groq-api-key>

LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.1

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

VECTOR_COLLECTION=job_market
VECTOR_STORE_DIR=data/vector_store

RAG_K=5

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

REQUEST_TIMEOUT=30
MAX_AI_RECORDS=100

LOG_LEVEL=INFO
```

Never commit the real `.env` file.

---

# Running Locally

## Terminal 1 — Backend

From the project root:

```powershell
cd "C:\Users\MD SAIF ALI\AI_Job_Market"

.\.venv\Scripts\Activate.ps1

uvicorn api.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Keep this terminal running.

---

## Terminal 2 — Frontend

```powershell
cd "C:\Users\MD SAIF ALI\AI_Job_Market\frontend"

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# Dataset Refresh

The project contains a refresh pipeline intended to collect and process newer job-market records.

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1

python -m pipeline.refresh_pipeline
```

Conceptually, the refresh workflow is:

```text
Existing Dataset
      │
      ▼
Collect Current Job Records
      │
      ▼
Transform / Normalize
      │
      ▼
Load / Duplicate Handling
      │
      ▼
Enrichment
      │
      ▼
Database Update
      │
      ▼
Vector Index Synchronization
```

The refresh pipeline should be run before starting the backend when an updated local dataset is desired.

> **Note:** Verify the refresh entry point and persistence behavior against the current `pipeline/refresh_pipeline.py` implementation before using it in automated production scheduling.

---

# Typical Local Startup Workflow

When starting the project after restarting the computer and refreshing the dataset is desired:

### Terminal 1

```powershell
cd "C:\Users\MD SAIF ALI\AI_Job_Market"

.\.venv\Scripts\Activate.ps1

python -m pipeline.refresh_pipeline

uvicorn api.main:app --reload
```

Wait for the refresh pipeline to finish before starting Uvicorn.

### Terminal 2

```powershell
cd "C:\Users\MD SAIF ALI\AI_Job_Market\frontend"

npm run dev
```

Then open:

```text
http://localhost:5173
```

If no dataset refresh is required, skip:

```powershell
python -m pipeline.refresh_pipeline
```

---

# Docker

The backend includes a Dockerfile for containerized deployment.

Build:

```bash
docker build -t marketmind-ai .
```

Run:

```bash
docker run --env-file .env -p 8000:8000 marketmind-ai
```

The API will then be available at:

```text
http://localhost:8000
```

---

# Cloud Deployment

The application architecture supports independent deployment of the frontend, backend, and database.

```text
                    Internet
                       │
                       ▼
              ┌─────────────────┐
              │ React Frontend  │
              │     Render      │
              └────────┬────────┘
                       │
                       │ HTTPS
                       ▼
              ┌─────────────────┐
              │ FastAPI Backend │
              │     Render      │
              └────────┬────────┘
                       │
                       │ PostgreSQL
                       ▼
              ┌─────────────────┐
              │      Neon       │
              │   PostgreSQL    │
              └─────────────────┘
```

The cloud deployment is independent of the local development machine. Once deployed, the frontend, backend, and database do not require the developer's laptop to remain running.

---

# Deployment Status

The core cloud stack has been deployed using:

- Render Static Site — React frontend
- Render Web Service — FastAPI backend
- Neon — PostgreSQL database
- GitHub — source control and deployment source

The structured analytics and job-exploration functionality operate through the deployed FastAPI/PostgreSQL stack.

### Current Production Limitation

The current low-memory backend instance has demonstrated memory pressure when the local ML/RAG runtime is initialized.

The RAG stack includes memory-intensive dependencies such as:

```text
PyTorch
Transformers
Sentence Transformers
ChromaDB
LangChain
```

The current deployment therefore requires further production optimization or additional compute resources for reliable AI/RAG inference.

This is a deployment-resource limitation rather than a limitation of the local development architecture.

---

# Security

Sensitive configuration is provided through environment variables.

The repository excludes files such as:

```text
.env
.env.local
.venv/
frontend/node_modules/
data/vector_store/
data/runtime/
```

Secrets such as database credentials and Groq API keys must never be committed to source control.

For deployment, configure secrets directly through the hosting provider's environment-variable management system.

---

# Design Principles

MarketMind AI follows several architectural principles:

### Separation of Concerns

Collection, transformation, persistence, analytics, retrieval, LLM inference, API routing, and frontend rendering are implemented as separate layers.

### Modular Data Sources

New collectors can be incorporated without redesigning the analytics or intelligence layers.

### Structured + Semantic Intelligence

PostgreSQL provides deterministic structured analytics while vector retrieval provides semantic context.

### Evidence-Grounded Generation

The LLM is intended to synthesize retrieved job-market evidence rather than independently invent market statistics.

### Incremental Evolution

The architecture supports future expansion of data sources, enrichment models, retrieval strategies, evaluation pipelines, and deployment infrastructure.

---

# Future Improvements

Potential extensions include:

- production-optimized embedding infrastructure,
- managed vector database deployment,
- scheduled dataset refresh,
- asynchronous ingestion workers,
- background enrichment queues,
- embedding/model service separation,
- caching of common analytics queries,
- additional job sources,
- time-series hiring trend analysis,
- skill-demand forecasting,
- salary intelligence,
- geographical demand heatmaps,
- personalized skill-gap analysis,
- job recommendation models,
- monitoring and observability,
- CI/CD testing,
- and automated RAG evaluation.

---

# Disclaimer

MarketMind AI is a job-market intelligence and research project.

Job availability, requirements, locations, and other information originate from external job sources and may change over time. Generated AI responses should be interpreted in the context of the underlying collected dataset.

---

## Author

**Md Saif Ali**

MarketMind AI — AI-Powered Job Market Intelligence Platform
