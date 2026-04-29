"""
Query Engine Module
Handles RAG query processing with reranking
"""

import chromadb
from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.llms.groq import Groq
from sentence_transformers import CrossEncoder


class QueryEngine:
    """RAG Query Engine with reranking"""
    
    def __init__(self, jina_api_key: str, groq_api_key: str, db_path: str, collection_name: str):
        """Initialize query engine"""
        self.embed_model = JinaEmbedding(
            api_key=jina_api_key,
            model="jina-embeddings-v2-base-en"
        )
        
        self.llm = Groq(
            model="llama-3.1-8b-instant",
            api_key=groq_api_key,
            temperature=0,
            max_tokens=512
        )
        
        settings = chromadb.Settings(anonymized_telemetry=False, allow_reset=True)
        self.client = chromadb.PersistentClient(path=db_path, settings=settings)
        self.collection = self.client.get_collection(collection_name)
        
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    def search(self, question: str, n_results: int = 15):
        """Search for relevant documents"""
        query_embedding = self.embed_model.get_text_embedding(question)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        docs = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        return docs, metadatas
    
    def rerank_results(self, question: str, docs: list, metadatas: list):
        """Rerank results using CrossEncoder"""
        # Separate tables and prose
        table_items = [(doc, meta, idx) for idx, (doc, meta) in enumerate(zip(docs, metadatas)) 
                       if meta.get("item_type") in ["table", "table_row", "holdings_list"]]
        prose_items = [(doc, meta, idx) for idx, (doc, meta) in enumerate(zip(docs, metadatas)) 
                       if meta.get("item_type") not in ["table", "table_row", "holdings_list"]]
        
        # Rerank tables
        reranked_tables = []
        if table_items:
            table_texts = [doc for doc, _, _ in table_items]
            table_scores = self.reranker.predict([(question, text) for text in table_texts])
            reranked_tables = sorted(
                zip(table_scores, table_items), 
                key=lambda x: float(x[0]),
                reverse=True
            )
        
        # Rerank prose
        reranked_prose = []
        if prose_items:
            prose_texts = [doc for doc, _, _ in prose_items]
            prose_scores = self.reranker.predict([(question, text) for text in prose_texts])
            reranked_prose = sorted(
                zip(prose_scores, prose_items), 
                key=lambda x: float(x[0]),
                reverse=True
            )
        
        # Combine: Top 2 tables + Top 3 prose
        final_items = []
        
        for item in reranked_tables[:2]:
            if len(item) == 2:
                score, (doc, meta, _) = item
                final_items.append((doc, meta, float(score)))
        
        for item in reranked_prose[:3]:
            if len(item) == 2:
                score, (doc, meta, _) = item
                final_items.append((doc, meta, float(score)))
        
        if len(reranked_tables) == 0:
            for item in reranked_prose[3:5]:
                if len(item) == 2:
                    score, (doc, meta, _) = item
                    final_items.append((doc, meta, float(score)))
        
        # Sort by score
        final_items.sort(key=lambda x: float(x[2]), reverse=True)
        
        # Deduplicate
        seen = set()
        unique_items = []
        for doc, meta, score in final_items:
            if doc not in seen:
                seen.add(doc)
                unique_items.append((doc, meta))
                if len(unique_items) >= 4:
                    break
        
        # Sort by page number
        def get_page_number(item):
            try:
                page = item[1].get("page", 0)
                return int(page) if page else 0
            except (ValueError, TypeError, AttributeError):
                return 0
        
        unique_items.sort(key=get_page_number)
        
        return [doc for doc, _ in unique_items], [meta for _, meta in unique_items]
    
    def generate_answer(self, question: str, docs: list, metadatas: list, chat_history: list = None):
        """Generate answer using LLM"""
        # Build context
        context_parts = []
        for doc, meta in zip(docs, metadatas):
            max_len = 1200 if meta.get("item_type") in ["table", "table_row", "holdings_list"] else 600
            truncated_doc = doc[:max_len] + "..." if len(doc) > max_len else doc
            context_parts.append(f"[Page {meta.get('page','?')}]\n{truncated_doc}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build conversation history
        history_context = ""
        if chat_history and len(chat_history) > 0:
            recent_history = chat_history[-3:]
            history_lines = []
            for q, a in recent_history:
                history_lines.append(f"User: {q}\nAssistant: {a}")
            history_context = "\n\nPrevious Conversation:\n" + "\n".join(history_lines) + "\n"
        
        # Generate prompt
        prompt = f"""You are a professional financial assistant for Al Meezan Investment Management, specializing in mutual fund reports.

Instructions:
- Answer ONLY using the provided context below
- Use exact numbers, NAV values, and percentages as written
- For tabular data, format as markdown tables
- If the answer is not found in the context, respond: "I couldn't find this information in the available FMR reports."
- Always cite page numbers using the format [Page X]
- If the user uses pronouns (it, this, that) or refers to previous topics, use the conversation history to understand the reference

{history_context}
Context from FMR Reports:
{context}

User Question: {question}

Professional Answer:"""
        
        response = self.llm.complete(prompt)
        
        return str(response.text)
    
    def query(self, question: str, chat_history: list = None):
        """
        Complete query pipeline
        Returns: (answer, sources)
        """
        # Search
        docs, metadatas = self.search(question)
        
        if not docs:
            return "I couldn't find any relevant information in the FMR reports. Please try rephrasing your question or ask about a different topic.", []
        
        # Rerank
        docs, metadatas = self.rerank_results(question, docs, metadatas)
        
        # Generate answer
        answer = self.generate_answer(question, docs, metadatas, chat_history)
        
        # Extract sources
        sources = []
        for meta in metadatas:
            sources.append({
                "page": meta.get("page", "?"),
                "type": meta.get("item_type", "text")
            })
        
        return answer, sources
