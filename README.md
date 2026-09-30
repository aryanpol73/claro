# Claro

Claro is a retrieval-augmented generation (RAG) app for asking questions about academic PDF documents. Upload PDFs, retrieve relevant passages, and get answers generated from their content.

## Features

- Upload and view PDF documents
- Ask questions about uploaded documents
- Retrieve relevant text passages with answers
- Use Google Gemini for embeddings and answer generation
- Store and search document vectors with Pinecone

## Tech Stack

- Frontend: React and Vite
- Backend: FastAPI and Python
- AI: Google Gemini
- Vector database: Pinecone

## Requirements

- Python 3.12 or newer
- Node.js and npm
- Google AI API key
- Pinecone API key
- LangSmith API key

## Setup

### 1. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
```

Keep this file private. Do not commit API keys to Git.

### 2. Install backend dependencies

Run these commands from the project root:

```powershell
py -3.12 -m pip install -e .
py -3.12 backend/create_pinecone_index.py
```

The index script creates the `academic-files-rag` Pinecone index if it does not already exist.

### 3. Install frontend dependencies

```powershell
cd frontend
npm install
```

## Run the App

Start the backend from the project root:

```powershell
py -3.12 -m uvicorn backend.main:app --reload
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm run dev
```

Open the local URL printed by Vite, usually http://localhost:5173.

The FastAPI documentation is available at http://localhost:8000/docs.

## API Endpoints

- `GET /` - Check that the backend is running
- `POST /upload` - Upload a PDF
- `GET /files` - List uploaded files
- `GET /files/{filename}` - View or download an uploaded file
- `POST /ask` - Ask a question about the indexed documents

Uploads are limited to PDF files up to 50 MB. Uploaded files and local credentials should not be committed to the repository.
