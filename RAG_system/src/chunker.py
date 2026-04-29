"""
Chunking Module
Prepares extracted items for embedding
"""


def prepare_chunks(items: list) -> tuple:
    """
    Prepare chunks for embedding
    Returns: (texts, metadatas, ids)
    """
    all_texts = []
    all_metadatas = []
    all_ids = []
    doc_id = 0
    
    for item in items:
        all_texts.append(item["text"])
        all_metadatas.append({
            "page": item["page"],
            "item_type": item["type"],
            "fund_name": item.get("fund_name", "")
        })
        all_ids.append(f"doc_{doc_id}")
        doc_id += 1
    
    return all_texts, all_metadatas, all_ids


def filter_long_texts(texts: list, metadatas: list, ids: list, max_length: int = 2000) -> tuple:
    """
    Filter out very long texts and split them
    Returns: (filtered_texts, filtered_metadatas, filtered_ids)
    """
    filtered_texts = []
    filtered_metas = []
    filtered_ids = []
    
    for text, meta, id in zip(texts, metadatas, ids):
        if len(text) <= max_length:
            filtered_texts.append(text)
            filtered_metas.append(meta)
            filtered_ids.append(id)
        else:
            # Split very long text
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length-200)]
            for idx, chunk in enumerate(chunks):
                filtered_texts.append(chunk)
                filtered_metas.append(meta)
                filtered_ids.append(f"{id}_part{idx}")
    
    return filtered_texts, filtered_metas, filtered_ids
