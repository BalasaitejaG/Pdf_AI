import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
import streamlit as st
# Must be the first Streamlit command
st.set_page_config(page_title="PDF Question & Answer", layout="wide")


# Load environment variables - works for both local and Vercel
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    st.error(
        "❌ API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Configure Gemini AI
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.sidebar.error("❌ API Key error. Please check your API key")
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
                background: var(--light-gray);
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid var(--primary);
                margin-top: 1rem;
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
    pdf_file = st.file_uploader("", 
        type="pdf", 
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
                        st.markdown(f'<div class="response">{answer}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error("Error: Please try again later")

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
