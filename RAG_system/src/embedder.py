"""
Embedding Module
Handles embedding generation and vector database operations
"""

import chromadb
from llama_index.embeddings.jinaai import JinaEmbedding
import time
from tqdm import tqdm


def initialize_embedder(api_key: str, model: str = "jina-embeddings-v2-base-en"):
    """Initialize Jina AI embedding model"""
    return JinaEmbedding(api_key=api_key, model=model)


def initialize_vectordb(db_path: str, collection_name: str, reset: bool = True):
    """
    Initialize ChromaDB and create/get collection
    
    Args:
        db_path: Path to vector database
        collection_name: Name of collection
        reset: If True, delete existing collection
    
    Returns:
        (client, collection)
    """
    settings = chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
    client = chromadb.PersistentClient(path=db_path, settings=settings)
    
    if reset:
        try:
            client.delete_collection(collection_name)
        except:
            pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "FMR reports with smart chunking"}
    )
    
    return client, collection


def generate_embeddings(embed_model, texts: list, show_progress: bool = True, batch_size: int = 50, max_retries: int = 3):
    """
    Generate embeddings for texts with retry logic and batching
    
    Args:
        embed_model: Embedding model
        texts: List of texts to embed
        show_progress: Show progress bar
        batch_size: Number of texts per batch (smaller = more stable)
        max_retries: Maximum retry attempts per batch
    
    Returns:
        List of embeddings
    """
    all_embeddings = []
    
    # Process in smaller batches to avoid connection issues
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    if show_progress:
        pbar = tqdm(total=len(texts), desc="Generating embeddings")
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        # Retry logic for each batch
        for attempt in range(max_retries):
            try:
                # Generate embeddings for this batch
                batch_embeddings = embed_model.get_text_embedding_batch(batch, show_progress=False)
                all_embeddings.extend(batch_embeddings)
                
                if show_progress:
                    pbar.update(len(batch))
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(texts):
                    time.sleep(0.5)
                
                break  # Success, move to next batch
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    print(f"\n⚠️  Batch {batch_num}/{total_batches} failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ Batch {batch_num}/{total_batches} failed after {max_retries} attempts: {str(e)}")
                    if show_progress:
                        pbar.close()
                    raise Exception(f"Failed to generate embeddings for batch {batch_num} after {max_retries} attempts: {str(e)}")
    
    if show_progress:
        pbar.close()
    
    return all_embeddings


def store_embeddings(collection, embeddings: list, texts: list, metadatas: list, ids: list):
    """Store embeddings in ChromaDB"""
    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
