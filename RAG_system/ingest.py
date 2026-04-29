"""
Main Ingestion Script
Orchestrates PDF extraction, chunking, embedding, and storage
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from src.pdf_extractor import extract_pdf
from src.chunker import prepare_chunks, filter_long_texts
from src.embedder import initialize_embedder, initialize_vectordb, generate_embeddings, store_embeddings

load_dotenv()

# Configuration
PDF_FOLDER = "data"
VECTOR_DB = "vectordb"
COLLECTION_NAME = "fmr_reports"
JINA_API_KEY = os.getenv("JINA_API_KEY")


def ingest_all_pdfs():
    """Main ingestion pipeline"""
    print("\n" + "="*60)
    print("🚀 FMR PDF Ingestion Pipeline")
    print("="*60)
    
    # Find PDFs
    pdf_files = list(Path(PDF_FOLDER).glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDFs found in {PDF_FOLDER}")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDF(s)")
    
    # Initialize embedder
    print("\n🔧 Initializing Jina AI embeddings...")
    embed_model = initialize_embedder(JINA_API_KEY)
    print("   ✅ Embedder ready")
    
    # Initialize vector database
    print(f"\n💾 Initializing ChromaDB...")
    client, collection = initialize_vectordb(VECTOR_DB, COLLECTION_NAME, reset=True)
    print(f"   ✅ Collection '{COLLECTION_NAME}' ready")
    
    # Extract from all PDFs
    all_items = []
    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {pdf_path.name}")
        items = extract_pdf(str(pdf_path))
        
        # Add source filename to each item
        for item in items:
            item["source"] = pdf_path.name
        
        all_items.extend(items)
        print(f"   Extracted: {len(items)} chunks")
    
    print(f"\n📊 Total extracted: {len(all_items)} chunks")
    
    # Prepare chunks
    print("\n🔄 Preparing chunks...")
    texts, metadatas, ids = prepare_chunks(all_items)
    
    # Add source to metadata
    for i, item in enumerate(all_items):
        metadatas[i]["source"] = item["source"]
    
    # Filter long texts
    print("   Filtering long texts...")
    texts, metadatas, ids = filter_long_texts(texts, metadatas, ids)
    print(f"   After filtering: {len(texts)} chunks")
    
    # Generate embeddings
    print(f"\n🔄 Generating embeddings (batch size: 50, with retry logic)...")
    try:
        embeddings = generate_embeddings(
            embed_model, 
            texts, 
            show_progress=True,
            batch_size=50,  # Smaller batches for stability
            max_retries=3   # Retry failed batches
        )
    except Exception as e:
        print(f"\n❌ Embedding generation failed: {str(e)}")
        print("\n💡 Suggestions:")
        print("   1. Check your internet connection")
        print("   2. Verify JINA_API_KEY is valid")
        print("   3. Try again in a few minutes (API may be rate-limited)")
        return
    
    # Store in database
    print(f"\n💾 Storing in ChromaDB...")
    store_embeddings(collection, embeddings, texts, metadatas, ids)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Ingestion Complete!")
    print(f"{'='*60}")
    print(f"\n📊 Statistics:")
    print(f"   Total chunks: {len(texts)}")
    print(f"   Fund details: {sum(1 for m in metadatas if m['item_type']=='fund_detail')}")
    print(f"   Holdings lists: {sum(1 for m in metadatas if m['item_type']=='holdings_list')}")
    print(f"   Tables: {sum(1 for m in metadatas if m['item_type']=='table')}")
    print(f"   Text chunks: {sum(1 for m in metadatas if m['item_type']=='text')}")
    print(f"\n🎯 Next: streamlit run chatbot.py")


if __name__ == "__main__":
    ingest_all_pdfs()
