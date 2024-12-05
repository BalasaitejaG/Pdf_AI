import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
import streamlit as st
import atexit
import sqlite3
from datetime import datetime
from pathlib import Path

# Must be the first Streamlit command
st.set_page_config(page_title="PDF Question & Answer", layout="wide")

# Load environment variables
load_dotenv()

# Database setup
DATA_DIR = Path(__file__).parent / "data"  # Use relative path
DB_PATH = DATA_DIR / "usage.db"

def init_database():
    """Initialize the SQLite database"""
    try:
        # Create data directory if it doesn't exist
        DATA_DIR.mkdir(exist_ok=True)
        
        # Use memory database if we can't write to disk
        db_path = ":memory:" if not os.access(DATA_DIR, os.W_OK) else DB_PATH
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_usage
                    (user_id TEXT PRIMARY KEY,
                     request_count INTEGER DEFAULT 0,
                     first_request TIMESTAMP)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.warning("⚠️ Running in demo mode - trial usage won't persist between sessions")
        global DB_PATH
        DB_PATH = ":memory:"  # Fall back to in-memory database

# Initialize database on startup
init_database()

# Initialize genai with cleanup
def cleanup_genai():
    try:
        genai.reset_session()
    except:
        pass

# Register cleanup function
atexit.register(cleanup_genai)

# Get API key and configure Gemini
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    st.error("❌ API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Error: {str(e)}")
    st.stop()

# Cache for storing AI responses
if 'response_cache' not in st.session_state:
    st.session_state.response_cache = {}

# Request tracking
if 'request_timestamps' not in st.session_state:
    st.session_state.request_timestamps = []

# User's API key
if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = None

def get_user_identifier():
    """Get a unique identifier for the user"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(int(time.time() * 1000))  # Use timestamp as ID
    return st.session_state.user_id

def check_trial_usage():
    """Check if user has exceeded trial usage"""
    if st.session_state.user_api_key:  # If user has their own API key, no need to check trial
        return True
        
    user_id = get_user_identifier()
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT request_count FROM user_usage WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if result is None:
        c.execute("INSERT INTO user_usage (user_id, request_count, first_request) VALUES (?, 0, ?)",
                 (user_id, datetime.now()))
        conn.commit()
        result = (0,)
    
    conn.close()
    return result[0] < 5

def increment_trial_usage():
    """Increment the trial usage count for the current user"""
    if not st.session_state.user_api_key:  # Only track if using trial
        user_id = get_user_identifier()
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO user_usage (user_id, request_count, first_request)
                     VALUES (?, 1, ?)
                     ON CONFLICT(user_id) DO UPDATE SET
                     request_count = request_count + 1""",
                 (user_id, datetime.now()))
        
        conn.commit()
        conn.close()

def get_remaining_trial_requests():
    """Get remaining trial requests for current user"""
    if st.session_state.user_api_key:
        return 0
        
    user_id = get_user_identifier()
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT request_count FROM user_usage WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    conn.close()
    
    if result is None:
        return 5
    
    return max(0, 5 - result[0])

def get_cache_key(prompt):
    """Generate a cache key for a prompt"""
    return hash(prompt)

def get_ai_response(prompt, max_retries=3):
    cache_key = get_cache_key(prompt)

    # Check cache first
    if cache_key in st.session_state.response_cache:
        return st.session_state.response_cache[cache_key]

    # Check trial usage if using default API key
    if not st.session_state.user_api_key and not check_trial_usage():
        raise Exception("Trial limit reached (5 requests). Please enter your own API key to continue using the application.")

    try:
        # Configure API key
        current_api_key = st.session_state.user_api_key or api_key
        genai.configure(api_key=current_api_key)
        
        # Make the API call
        response = model.generate_content(prompt)
        result = response.text

        # Increment trial count if using default API key
        if not st.session_state.user_api_key:
            increment_trial_usage()

        # Cache the response
        st.session_state.response_cache[cache_key] = result
        return result

    except Exception as e:
        if "resource_exhausted" in str(e).lower():
            st.error("⚠️ API rate limit reached. Please try again in a few minutes.")
            raise Exception("Please wait a few minutes before trying again.")
        raise e

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_db_connection():
    """Get a database connection"""
    try:
        return sqlite3.connect(DB_PATH if DB_PATH != ":memory:" else ":memory:")
    except Exception:
        return sqlite3.connect(":memory:")

def main():
    # Update the styling section
    st.markdown("""
        <style>
            :root {
                --primary: #2196F3;
                --background: #FFFFFF;
                --text: #FFFFFF;
                --gray: #CCCCCC;
                --light-gray: #F5F5F5;
            }

            .header {
                text-align: center;
                background: #1E1E1E;
                margin: -6rem -20rem 2rem -20rem;
                padding: 6rem 0;
            }
            
            .header h1 {
                color: var(--text);
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            
            .header p {
                color: var(--gray);
                font-size: 1.1rem;
            }

            /* Center layout */
            .main-content {
                max-width: 800px;
                margin: 0 auto;
                padding: 0 1rem;
            }

            /* Upload area */
            .upload-container {
                padding: 1rem;
                margin: 2rem auto;
                max-width: 500px;
            }
            
            .stFileUploader > div > div {
                padding: 2.5rem 1rem;
                border: 2px dashed #ccc;
                border-radius: 8px;
                background: #fafafa;
                cursor: pointer;
                text-align: center;
            }
            
            .stFileUploader > div > div:hover {
                border-color: #2196F3;
                background: #f5f5f5;
            }

            /* Response area */
            .response {
                background: rgba(33, 150, 243, 0.05);
                border-radius: 12px;
                border: 1px solid rgba(33, 150, 243, 0.2);
                margin-top: 1.5rem;
                overflow: hidden;
            }

            .response-header {
                background: rgba(33, 150, 243, 0.1);
                padding: 12px 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                border-bottom: 1px solid rgba(33, 150, 243, 0.2);
            }

            .response-header .ai-icon {
                color: #2196F3;
            }

            .response-header span {
                color: #F5F5F5;
                font-weight: 500;
            }

            .response-content {
                padding: 25px;
                color: #F5F5F5;
                font-size: 1.05rem;
                line-height: 1.7;
            }

            /* Highlight important parts */
            .response-content strong {
                color: #2196F3;
                font-weight: 500;
            }

            /* Style lists in response */
            .response-content ul, .response-content ol {
                margin: 1rem 0;
                padding-left: 1.5rem;
            }

            .response-content li {
                margin: 0.5rem 0;
            }

            /* Style for the question input */
            .stTextInput input {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 8px;
                padding: 12px 16px;
            }

            .stTextInput input:focus {
                border-color: var(--primary);
                box-shadow: 0 0 0 1px var(--primary);
            }

            .stTextInput input::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="header">
            <h1>PDF Q&A</h1>
            <p>Get instant answers from your documents</p>
        </div>
    """, unsafe_allow_html=True)

    # Wrap content in centered container
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Upload area
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    pdf_file = st.file_uploader(
        label="Upload PDF Document",  
        type="pdf", 
        label_visibility="collapsed",  
        help="Drag and drop a PDF file or click to browse"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = None

    # Add API key input field in sidebar
    with st.sidebar:
        st.markdown("### API Key Settings")
        user_api_key = st.text_input("Enter your API key (optional)", type="password")
        if user_api_key:
            st.session_state.user_api_key = user_api_key
            
        # Show trial usage if using default API key
        if not st.session_state.user_api_key:
            remaining_requests = get_remaining_trial_requests()
            st.markdown(f"Trial requests remaining: **{remaining_requests}**")
            st.markdown("*You can make 5 requests with our API key. After that, please use your own API key.*")
            
            # Show user ID for debugging (you can remove this later)
            st.markdown("---")
            st.markdown(f"Your User ID: `{get_user_identifier()}`")
            
            if remaining_requests == 0:
                st.error("⚠️ Trial limit reached. Please enter your API key above to continue.")
                st.markdown("""
                To get your own API key:
                1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
                2. Create a new API key
                3. Enter it above to continue using the application
                """)
        else:
            st.success("Using your API key ✓")

    if pdf_file is not None:
        if st.session_state.pdf_name != pdf_file.name:
            with st.spinner("Processing PDF..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(pdf_file.getvalue())
                        tmp_file_path = tmp_file.name

                    st.session_state.pdf_text = extract_text_from_pdf(tmp_file_path)
                    st.session_state.pdf_name = pdf_file.name
                    os.unlink(tmp_file_path)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.pdf_text = None
                    st.session_state.pdf_name = None

        if st.session_state.pdf_text:
            query = st.text_input("Ask a question", placeholder="What would you like to know?")
            
            if query:
                with st.spinner("Thinking..."):
                    try:
                        prompt = f"""Based on the following document content, please answer the question.
                        If you can't find the specific information in the document, say so.

                        Document content:
                        {st.session_state.pdf_text}

                        Question: {query}

                        Answer:"""

                        answer = get_ai_response(prompt)
                        st.markdown(f"<div class='response'><div class='response-content'>{answer}</div></div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error("Error: Please try again later")

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
