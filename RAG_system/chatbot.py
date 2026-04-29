"""
Al Meezan FMR Chatbot
Professional RAG-based chatbot for financial mutual fund reports
"""

import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

from src.query_engine import QueryEngine

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VECTOR_DB = "vectordb"
COLLECTION_NAME = "fmr_reports"
JINA_API_KEY = os.getenv("JINA_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def load_query_engine():
    """Initialize and cache the query engine"""
    if not JINA_API_KEY or not GROQ_API_KEY:
        raise ValueError("API keys not found. Please check your .env file.")
    
    return QueryEngine(JINA_API_KEY, GROQ_API_KEY, VECTOR_DB, COLLECTION_NAME)


def validate_environment():
    """Validate that all required components are available"""
    errors = []
    
    if not JINA_API_KEY:
        errors.append("JINA_API_KEY not found in environment variables")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY not found in environment variables")
    
    # Check if vectordb exists
    if not os.path.exists(VECTOR_DB):
        errors.append(f"Vector database not found at '{VECTOR_DB}'. Please run ingestion first.")
    
    return errors


def format_sources(sources):
    """Format sources for display"""
    if not sources:
        return "No sources available"
    
    # Group by page
    pages = {}
    for src in sources:
        page = src.get('page', '?')
        src_type = src.get('type', 'text')
        if page not in pages:
            pages[page] = []
        if src_type not in pages[page]:
            pages[page].append(src_type)
    
    # Format output
    formatted = []
    for page, types in sorted(pages.items(), key=lambda x: (str(x[0]) if x[0] != '?' else 'zzz')):
        type_str = ", ".join(types)
        formatted.append(f"**Page {page}** ({type_str})")
    
    return "\n".join(formatted)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Al Meezan FMR Chatbot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    
    .main-header p {
        color: #e0e7ff;
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Info boxes */
    .info-box {
        background-color: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <h1>📊 Al Meezan FMR Chatbot</h1>
    <p>Intelligent Financial Report Assistant powered by RAG Technology</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🔧 System Status")
    
    # Validate environment
    env_errors = validate_environment()
    
    if env_errors:
        st.error("**Configuration Issues:**")
        for error in env_errors:
            st.markdown(f"- {error}")
        
        st.markdown("---")
        st.markdown("**Setup Instructions:**")
        st.code("python ingest.py", language="bash")
    else:
        try:
            query_engine = load_query_engine()
            st.success("✅ System Ready")
            
            with st.expander("📊 Database Info", expanded=False):
                st.markdown(f"""
                - **Collection:** `{COLLECTION_NAME}`
                - **Database:** `{VECTOR_DB}`
                - **Status:** Connected
                """)
        except Exception as e:
            st.error(f"**Initialization Error:**\n{str(e)}")
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📈 Session Stats")
    if "messages" in st.session_state:
        msg_count = len(st.session_state.messages)
        user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
        st.metric("Total Messages", msg_count)
        st.metric("Questions Asked", user_msgs)
    else:
        st.info("No messages yet")
    
    st.markdown("---")
    
    # Actions
    st.markdown("### ⚙️ Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    st.markdown("---")
    
    # About
    with st.expander("ℹ️ About", expanded=False):
        st.markdown("""
        **Technology Stack:**
        - 🤖 LLM: Groq (LLaMA 3.1)
        - 🔍 Embeddings: Jina AI
        - 💾 Vector DB: ChromaDB
        - 🎯 Reranking: CrossEncoder
        
        **Features:**
        - Conversational memory
        - Context-aware responses
        - Source citations
        - Multi-document support
        """)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# Example questions
with st.expander("💡 Example Questions", expanded=True):
    st.markdown("Click any question to try it:")
    
    examples = [
        ("📊 Benchmark", "What is the benchmark of AMMF?"),
        ("📈 Holdings", "Show me the top 10 holdings of Meezan Islamic Fund"),
        ("📅 Launch Date", "When was Al Meezan Mutual Fund launched?"),
        ("💰 Fund Size", "What is the current fund size?"),
        ("📉 NAV", "What is the NAV of AMMF?"),
        ("🎯 Performance", "Show me the performance metrics"),
    ]
    
    cols = st.columns(3)
    for i, (label, question) in enumerate(examples):
        with cols[i % 3]:
            if st.button(f"{label}", key=f"ex_{i}", use_container_width=True):
                st.session_state["prefill"] = question

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome message
if len(st.session_state.messages) == 0:
    st.markdown("""
    <div class="info-box">
        <strong>👋 Welcome!</strong><br>
        Ask me anything about Al Meezan mutual funds. I can help you with:
        <ul>
            <li>Fund performance and benchmarks</li>
            <li>Holdings and asset allocation</li>
            <li>NAV and fund sizes</li>
            <li>Risk metrics and ratings</li>
            <li>Historical data and trends</li>
        </ul>
        <em>Tip: I remember our conversation context, so you can ask follow-up questions!</em>
    </div>
    """, unsafe_allow_html=True)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        
        # Show sources if available
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander("📄 View Sources", expanded=False):
                st.markdown(format_sources(msg["sources"]))

# Chat input
prefill = st.session_state.pop("prefill", None)
question = st.chat_input("Ask me anything about FMR reports...")
question = question or prefill

if question:
    # Validate system is ready
    if env_errors:
        st.error("⚠️ System not ready. Please check the sidebar for configuration issues.")
        st.stop()
    
    # Build chat history
    chat_history = []
    messages = st.session_state.messages[-6:]
    for i in range(0, len(messages)-1, 2):
        if messages[i]["role"] == "user" and messages[i+1]["role"] == "assistant":
            chat_history.append((messages[i]["content"], messages[i+1]["content"]))
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)
    
    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔍 Analyzing your question..."):
            try:
                query_engine = load_query_engine()
                answer, sources = query_engine.query(question, chat_history)
                
                # Display answer
                st.markdown(answer)
                
                # Display sources
                if sources:
                    with st.expander("📄 View Sources", expanded=False):
                        st.markdown(format_sources(sources))
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"""
                <div class="error-box">
                    <strong>❌ Error Processing Query</strong><br>
                    {str(e)}<br><br>
                    <em>Please try rephrasing your question or contact support if the issue persists.</em>
                </div>
                """
                st.markdown(error_msg, unsafe_allow_html=True)
                
                # Save error to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error: {str(e)}",
                    "sources": []
                })

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.caption("💡 **Tip:** I maintain conversation context - ask follow-up questions naturally!")

with col2:
    st.caption(f"🕐 {datetime.now().strftime('%I:%M %p')}")

with col3:
    st.caption("🔒 Secure & Private")
