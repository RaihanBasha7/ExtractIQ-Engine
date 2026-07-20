# 🚀 ExtractIQ Engine Deployment Guide

## Overview

ExtractIQ Engine is deployed as a modern full-stack web application
using **Render** for the FastAPI backend and **Vercel** for the React
frontend. This setup provides a simple, reliable, and scalable
deployment pipeline suitable for hackathon projects and production-ready
MVPs.

------------------------------------------------------------------------

# Deployment Architecture

``` text
                User
                  │
                  ▼
          Vercel Frontend
      (React + Vite + Tailwind)
                  │
          HTTPS API Requests
                  │
                  ▼
          Render Backend
      (FastAPI + Python 3.13)
                  │
                  ▼
        Featherless AI API
         (GLM-5.2 Model)
                  │
                  ▼
           SQLite Database
                  │
                  ▼
      Metrics & Analytics API
```

------------------------------------------------------------------------

# Backend Deployment

## Platform

**Render**

The backend is deployed as a Python Web Service running FastAPI with
Uvicorn.

### Responsibilities

-   Host REST API
-   Process extraction requests
-   Connect to Featherless AI
-   Validate responses
-   Execute the Model-Driven Repair Loop
-   Store extraction history
-   Serve metrics endpoints

------------------------------------------------------------------------

## Build Command

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Start Command

``` bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

------------------------------------------------------------------------

# Frontend Deployment

## Platform

**Vercel**

The frontend is deployed as a static React application built with Vite.

### Responsibilities

-   User interface
-   Ticket upload
-   JSON visualization
-   Analytics dashboard
-   History viewer
-   Health monitoring

------------------------------------------------------------------------

## Build Command

``` bash
npm install
npm run build
```

------------------------------------------------------------------------

## Output Directory

``` text
dist/
```

------------------------------------------------------------------------

# Environment Variables

## Backend (.env)

``` env
FEATHERLESS_API_KEY=your_featherless_api_key
MODEL_NAME=zai-org/GLM-5.2
DATABASE_URL=sqlite:///data/extractions.db
MAX_REPAIR_ATTEMPTS=3
LOG_LEVEL=INFO
```

### Variable Description

  Variable              Purpose
  --------------------- -----------------------------------
  FEATHERLESS_API_KEY   Authentication for Featherless AI
  MODEL_NAME            LLM model used for extraction
  DATABASE_URL          SQLite database connection
  MAX_REPAIR_ATTEMPTS   Maximum repair loop retries
  LOG_LEVEL             Logging configuration

------------------------------------------------------------------------

## Frontend (.env)

``` env
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

### Variable Description

  Variable            Purpose
  ------------------- ------------------------------------------
  VITE_API_BASE_URL   Base URL of the deployed FastAPI backend

------------------------------------------------------------------------

# API URLs

## Local Development

``` text
Frontend
http://localhost:5173

Backend
http://localhost:8000

Swagger UI
http://localhost:8000/docs

OpenAPI
http://localhost:8000/openapi.json
```

------------------------------------------------------------------------

## Production

``` text
Frontend
https://your-project.vercel.app

Backend
https://your-render-service.onrender.com

Swagger UI
https://your-render-service.onrender.com/docs

OpenAPI
https://your-render-service.onrender.com/openapi.json
```

------------------------------------------------------------------------

# Deployment Workflow

``` text
Developer

│

├── Push Code to GitHub
│
▼
GitHub Repository
│
├──────────────┐
│              │
▼              ▼
Render       Vercel
│              │
▼              ▼
Backend      Frontend
│              │
└──────► Live Application ◄──────┘
```

------------------------------------------------------------------------

# Deployment Checklist

## Backend

-   Python version configured
-   Dependencies installed
-   Environment variables added
-   Start command configured
-   API accessible
-   Swagger documentation available

------------------------------------------------------------------------

## Frontend

-   Build successful
-   API URL configured
-   Static assets generated
-   Environment variables added
-   Connected to backend

------------------------------------------------------------------------

# Health Verification

Verify the deployment using the following endpoints:

``` text
GET /health
```

Expected Response

``` json
{
  "status": "healthy"
}
```

------------------------------------------------------------------------

``` text
GET /version
```

Expected Response

``` json
{
  "version": "1.0.0",
  "model": "GLM-5.2"
}
```

------------------------------------------------------------------------

# Security Best Practices

-   Never commit `.env` files.
-   Store API keys securely in Render and Vercel environment settings.
-   Use HTTPS for all production traffic.
-   Restrict CORS to trusted frontend domains.
-   Rotate API keys periodically.

------------------------------------------------------------------------

# Future Production Deployment

Current MVP

-   Render
-   Vercel
-   SQLite
-   Single LLM provider

Future Enhancements

-   Docker containers
-   PostgreSQL
-   Redis
-   Celery workers
-   LiteLLM gateway
-   Multi-provider failover
-   Kubernetes
-   CI/CD pipelines
-   Cloud monitoring
-   Horizontal scaling

------------------------------------------------------------------------

# Deployment Summary

  Component       Platform          Purpose
  --------------- ----------------- ----------------------
  Frontend        Vercel            React user interface
  Backend         Render            FastAPI application
  AI Provider     Featherless AI    LLM inference
  Database        SQLite            Persistent storage
  Documentation   FastAPI Swagger   Interactive API docs
  Monitoring      Metrics API       System analytics
