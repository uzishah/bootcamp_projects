# RAG System - Financial Document Q&A Chatbot

## Project Overview
This is a Retrieval-Augmented Generation (RAG) system built for querying financial documents, specifically Fund Manager Reports (FMR). It uses MongoDB for vector storage, Jina AI for embeddings, and Groq for LLM inference.

## Architecture

```
User Query → Embedder → Vector Search (MongoDB) → Context Retrieval → LLM (Groq) → Response
```

## Features

- ✅ PDF document ingestion and processing
- ✅ Semantic chunking for better context preservation
- ✅ Vector embeddings using Jina AI
- ✅ MongoDB Atlas vector search
- ✅ Groq LLM for fast inference
- ✅ ChromaDB local vector storage option
- ✅ Interactive chatbot interface

## Tech Stack

- **Embeddings**: Jina AI (jina-embeddings-v3)
- **Vector Store**: MongoDB Atlas / ChromaDB
- **LLM**: Groq (llama-3.3-70b-versatile)
- **PDF Processing**: PyMuPDF
- **Framework**: Python 3.11+

## Project Structure

```
RAG_system/
├── chatbot.py                  # Main chatbot interface
├── ingest.py                   # Document ingestion script
├── requirements.txt            # Python dependencies
├── CODE_EXPLANATION.md         # Detailed code documentation
├── data/
│   ├── FMR-April-2025.pdf     # Sample financial document
│   └── README.md              # Data directory info
├── src/
│   ├── chunker.py             # Text chunking logic
│   ├── embedder.py            # Embedding generation
│   ├── pdf_extractor.py       # PDF text extraction
│   └── query_engine.py        # Query processing
├── vectordb/                   # ChromaDB storage
└── .env                        # Environment variables (not in git)
```

## Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier works)
- Groq API key (free tier available)
- Jina AI API key (free tier available)

## Installation

### 1. Clone and Setup
```bash
cd RAG_system
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
GROQ_API_KEY=your_groq_api_key
JINA_API_KEY=your_jina_api_key
JINA_URL=https://api.jina.ai/v1/embeddings
```

### 3. Ingest Documents
```bash
python ingest.py
```

### 4. Run Chatbot
```bash
python chatbot.py
```

## How It Works

### 1. Document Ingestion (`ingest.py`)
- Extracts text from PDF files
- Splits text into semantic chunks (500 tokens, 50 overlap)
- Generates embeddings using Jina AI
- Stores in MongoDB Atlas with vector index

### 2. Query Processing (`chatbot.py`)
- User enters a question
- Question is embedded using same Jina model
- Vector search retrieves top 3 relevant chunks
- Context + question sent to Groq LLM
- LLM generates answer based on context

### 3. Chunking Strategy (`src/chunker.py`)
- Semantic chunking preserves context
- 500 token chunks with 50 token overlap
- Maintains document structure

### 4. Embedding (`src/embedder.py`)
- Uses Jina AI embeddings-v3
- 1024-dimensional vectors
- Optimized for semantic search

## MongoDB Vector Search Setup

### Create Vector Index
```javascript
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

### Collection Structure
```json
{
  "_id": "ObjectId",
  "text": "chunk content",
  "embedding": [0.123, 0.456, ...],
  "metadata": {
    "source": "document.pdf",
    "chunk_id": 1
  }
}
```

## Usage Examples

### Example 1: Basic Query
```
You: What are the top holdings in the fund?
Bot: Based on the FMR report, the top holdings are:
1. Company A - 15.2%
2. Company B - 12.8%
3. Company C - 10.5%
```

### Example 2: Specific Information
```
You: What is the fund's performance in Q1 2025?
Bot: According to the report, the fund achieved a return of 8.5% in Q1 2025...
```

## API Keys Setup

### Groq API Key
1. Visit https://console.groq.com
2. Sign up for free account
3. Generate API key
4. Add to `.env` file

### Jina AI API Key
1. Visit https://jina.ai
2. Sign up for free account
3. Generate API key
4. Add to `.env` file

### MongoDB Atlas
1. Create free cluster at https://cloud.mongodb.com
2. Create database user
3. Whitelist IP (0.0.0.0/0 for development)
4. Get connection string
5. Add to `.env` file

## Performance Optimization

- **Embedding Cache**: Reuses embeddings for repeated queries
- **Batch Processing**: Processes multiple chunks efficiently
- **Vector Index**: MongoDB vector search for fast retrieval
- **Groq LLM**: Fast inference (< 1 second response time)

## Limitations

- Context window: Limited to top 3 chunks
- PDF-only support (no Word, Excel, etc.)
- English language optimized
- Requires internet connection for API calls

## Future Enhancements

- [ ] Add support for multiple document formats
- [ ] Implement conversation history
- [ ] Add source citation in responses
- [ ] Create web interface (Streamlit/Gradio)
- [ ] Add document management system
- [ ] Implement user authentication
- [ ] Add multi-language support

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Check connection string in `.env`
   - Verify IP whitelist in MongoDB Atlas
   - Ensure network connectivity

2. **API Key Errors**
   - Verify API keys are correct
   - Check API rate limits
   - Ensure keys have proper permissions

3. **No Results Found**
   - Verify documents are ingested
   - Check vector index is created
   - Try rephrasing query

## Cost Estimation

- **Groq**: Free tier (30 requests/minute)
- **Jina AI**: Free tier (1M tokens/month)
- **MongoDB Atlas**: Free tier (512MB storage)

**Total Cost**: $0 for development/testing

## Security Notes

⚠️ **Important**:
- Never commit `.env` file to version control
- Use environment variables for all credentials
- Implement rate limiting for production
- Sanitize user inputs

## References

- [Groq Documentation](https://console.groq.com/docs)
- [Jina AI Documentation](https://jina.ai/docs)
- [MongoDB Vector Search](https://www.mongodb.com/docs/atlas/atlas-vector-search/)

---

**Last Updated**: 2026
**Version**: 1.0
