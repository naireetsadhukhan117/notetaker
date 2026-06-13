# NoteTaker – NotebookLM Clone Backend

A production-ready REST API backend for processing multimedia documents (videos, PDFs, audio) and generating AI-powered study notes and quizzes using semantic search and retrieval-augmented generation.

## Features

- **Video Processing**: Extracts keyframes with motion detection and deduplication
- **Multimodal Embeddings**: Uses Gemini Embedding 2 (3,072 dimensions) for cross-modal retrieval
- **Vector Search**: ChromaDB-powered semantic search with confidence thresholding
- **RAG Generation**: Groq/OpenRouter-based study notes and quiz generation
- **Database**: SQLite backend with proper schema and foreign keys
- **Fast API**: Production-ready REST endpoints with CORS support

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google AI Studio key for embeddings | ✓ |
| `GROQ_API_KEY` | Groq API key for text generation | ✓ |
| `LLM_PROVIDER` | `groq` or `openrouter` | ✓ |

### Run the Server

```bash
# Development with auto-reload
uvicorn server:app --host 127.0.0.1 --port 8000 --reload

# Production
uvicorn server:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Upload & Process

**POST** `/api/ingest`
- Accepts video, PDF, audio, or text files
- Returns: `{"source_id": "uuid", "chunks": integer}`

### Generate Content

**POST** `/api/generate`
- Payload: `{"query": "string", "mode": "notes" | "quiz"}`
- Returns: `{"result": "markdown_string"}`

### Static Files

**GET** `/assets/{filename}`
- Serves extracted keyframe images

## Project Structure

```
backend/
├── server.py                   # FastAPI application
├── models/entities.py          # Data models
├── db/
│   ├── repositories.py         # SQLite access layer
│   └── vector_store.py         # ChromaDB wrapper
├── pipeline/
│   ├── video_processor.py      # Video frame extraction
│   ├── image_deduplicator.py   # Frame clustering & selection
│   ├── embedding_manager.py    # Gemini embeddings
│   ├── generation_engine.py    # RAG text generation
│   └── orchestrator.py         # Pipeline coordinator
├── tests/test_pipeline.py      # Unit tests
├── requirements.txt
└── .gitignore
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test class
python -m pytest tests/test_pipeline.py::TestVideoProcessor -v

# Run with coverage
python -m pytest tests/ --cov
```

## Architecture

1. **Ingestion** → Detects file type, routes to appropriate processor
2. **Processing** → Extracts chunks (video frames, PDF pages, audio transcripts, text)
3. **Deduplication** → Removes visually similar images via perceptual hashing
4. **Embedding** → Generates 3,072-dim vectors using Gemini Embedding 2
5. **Storage** → Indexes vectors in ChromaDB, metadata in SQLite
6. **Retrieval** → Semantic search with confidence filtering
7. **Generation** → RAG with Groq/OpenRouter LLMs

## Database Schema

- **sources**: Uploaded media files
- **chunks**: Extracted text segments with timestamps
- **visual_aids**: Keyframe images with quality metrics

## Troubleshooting

**"API key missing"**
- Verify `.env` file exists and is properly formatted
- Check environment variables: `echo $GEMINI_API_KEY`

**"ChromaDB connection failed"**
- Ensure `./chroma_db` directory has write permissions
- Check disk space

**"PDF parsing failed"**
- Verify file is not corrupted
- Try with a different PDF

## Production Notes

- Set `allow_origins` in CORS middleware to specific frontend domain
- Use environment secrets manager for API keys (not .env in production)
- Enable WAL mode for SQLite concurrent access
- Monitor API rate limits on embedding/generation services
- Set up proper error logging and monitoring

