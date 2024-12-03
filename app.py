import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
import streamlit as st
import atexit

# Must be the first Streamlit command
st.set_page_config(page_title="PDF Question & Answer", layout="wide")

# Load environment variables
load_dotenv()

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


def clean_old_timestamps():
    """Remove timestamps older than 1 hour"""
    current_time = time.time()
    st.session_state.request_timestamps = [
        ts for ts in st.session_state.request_timestamps
        if current_time - ts < 3600
    ]


def can_make_request():
    """Check if we can make a new request based on rate limits"""
    clean_old_timestamps()
    # Limit to 60 requests per hour
    return len(st.session_state.request_timestamps) < 60


def get_cache_key(prompt):
    """Generate a cache key for a prompt"""
    return hash(prompt)


def get_ai_response(prompt, max_retries=3):
    cache_key = get_cache_key(prompt)

    # Check cache first
    if cache_key in st.session_state.response_cache:
        return st.session_state.response_cache[cache_key]

    # Check rate limits
    if not can_make_request():
        wait_time = 3600 - \
            (time.time() - st.session_state.request_timestamps[0])
        raise Exception(f"Rate limit reached. Please wait {
                        int(wait_time/60)} minutes before trying again.")

    for attempt in range(max_retries):
        try:
            # Add timestamp for rate limiting
            st.session_state.request_timestamps.append(time.time())

            response = model.generate_content(prompt)
            result = response.text

            # Cache the response
            st.session_state.response_cache[cache_key] = result
            return result

        except Exception as e:
            error_message = str(e).lower()
            if "resource_exhausted" in error_message:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    st.warning(f"Rate limit hit. Retrying in {
                               wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)  # Exponential backoff
                    continue
                else:
                    st.error(
                        "⚠️ Rate limit exceeded. Please try again in a few minutes.")
                    raise Exception(
                        "Maximum retry attempts reached. Please wait a few minutes before trying again.")
            raise e


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def format_response(answer):
    """Format the AI response with better styling"""
    return f"""
        <div class="response">
            <div class="response-header">
                <svg class="ai-icon" viewBox="0 0 24 24" width="24" height="24">
                    <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,6A6,6 0 0,1 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6M12,8A4,4 0 0,0 8,12A4,4 0 0,0 12,16A4,4 0 0,0 16,12A4,4 0 0,0 12,8Z"/>
                </svg>
                <span>AI Assistant</span>
            </div>
            <div class="response-content">
                {answer}
            </div>
        </div>
    """


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
        label="Upload PDF Document",  # Added proper label
        type="pdf", 
        label_visibility="collapsed",  # Hide label but keep it accessible
        help="Drag and drop a PDF file or click to browse"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = None

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
                        st.markdown(format_response(answer), unsafe_allow_html=True)
                    except Exception as e:
                        st.error("Error: Please try again later")

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
