import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
import streamlit as st
import atexit
from datetime import datetime
import json

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

# Initialize session state
if 'response_cache' not in st.session_state:
    st.session_state.response_cache = {}

if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = None

if 'trial_count' not in st.session_state:
    st.session_state.trial_count = 0

def get_cache_key(prompt):
    """Generate a cache key for a prompt"""
    return hash(prompt)

def check_trial_usage():
    """Check if user has exceeded trial usage"""
    if st.session_state.user_api_key:  # If user has their own API key, no need to check trial
        return True
    return st.session_state.trial_count < 5

def increment_trial_usage():
    """Increment the trial usage count"""
    if not st.session_state.user_api_key:  # Only track if using trial
        st.session_state.trial_count += 1

def get_remaining_trial_requests():
    """Get remaining trial requests"""
    if st.session_state.user_api_key:
        return 0
    return max(0, 5 - st.session_state.trial_count)

def get_ai_response(prompt, max_retries=3):
    """Get AI response with better error handling"""
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
        error_msg = str(e).lower()
        if "resource_exhausted" in error_msg or "rate limit" in error_msg:
            wait_time = "a few minutes"
            if "about an hour" in error_msg:
                wait_time = "about an hour"
            raise Exception(f"⚠️ API rate limit reached. Please try again in {wait_time}. Consider using your own API key to avoid rate limits.")
        elif "invalid_argument" in error_msg:
            raise Exception("⚠️ The request was invalid. Please try with a shorter text or different question.")
        elif "permission_denied" in error_msg:
            raise Exception("⚠️ Invalid API key. Please check your API key and try again.")
        else:
            raise Exception(f"⚠️ An error occurred: {str(e)}")

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
            /* Main theme colors */
            :root {
                --primary-color: #2196F3;
                --background-dark: #1E1E1E;
                --text-light: #FFFFFF;
                --text-gray: #CCCCCC;
                --border-color: #333333;
            }

            /* Global styles */
            .stApp {
                background-color: var(--background-dark);
                color: var(--text-light);
            }

            /* Header styles */
            .header {
                text-align: center;
                padding: 2rem;
                background: #2C2C2C;
                border-radius: 10px;
                margin-bottom: 2rem;
                border: 1px solid var(--border-color);
            }

            .header h1 {
                color: var(--text-light);
                margin-bottom: 0.5rem;
            }

            .header p {
                color: var(--text-gray);
            }

            /* Upload container styles */
            .upload-container {
                border: 2px dashed #444;
                border-radius: 10px;
                padding: 2rem;
                text-align: center;
                margin: 2rem 0;
                background: #2C2C2C;
            }

            /* Input field styles */
            .stTextInput > div > div > input {
                background-color: #2C2C2C !important;
                color: var(--text-light) !important;
                border: 1px solid #444 !important;
            }

            .stTextInput > div > div > input:focus {
                border-color: var(--primary-color) !important;
                box-shadow: 0 0 0 1px var(--primary-color) !important;
            }

            .stTextInput > div > div > input::placeholder {
                color: #666 !important;
            }

            /* Response styles */
            .response {
                background: #2C2C2C;
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
                border: 1px solid var(--border-color);
            }

            .response-content {
                color: var(--text-light);
                white-space: pre-wrap;
            }

            /* File uploader styles */
            .stFileUploader > div {
                background-color: #2C2C2C !important;
                border: 1px solid #444 !important;
            }

            /* Button styles */
            .stButton > button {
                background-color: var(--primary-color) !important;
                color: var(--text-light) !important;
                border: none !important;
            }

            .stButton > button:hover {
                background-color: #1976D2 !important;
            }

            /* Sidebar styles */
            .css-1d391kg {
                background-color: #252525 !important;
            }

            .sidebar .sidebar-content {
                background-color: #252525;
            }

            /* Progress bar */
            .stProgress > div > div > div > div {
                background-color: var(--primary-color);
            }

            /* Spinner */
            .stSpinner > div > div > div {
                border-top-color: var(--primary-color) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="header">
            <h1>PDF AI Assistant</h1>
            <p>Upload your PDF and ask questions about its content</p>
        </div>
    """, unsafe_allow_html=True)

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

    # Store PDF text in session state
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
        
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = None

    # Upload area
    st.markdown('<div class="upload-container">', unsafe_allow_html=True)
    pdf_file = st.file_uploader(
        label="Upload PDF Document",
        type="pdf",
        label_visibility="collapsed",
        help="Drag and drop a PDF file or click to browse"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if pdf_file is not None:
        if st.session_state.pdf_name != pdf_file.name:
            with st.spinner("Processing PDF..."):
                try:
                    # Extract text from PDF
                    pdf_text = extract_text_from_pdf(pdf_file)
                    st.session_state.pdf_text = pdf_text
                    st.session_state.pdf_name = pdf_file.name
                except Exception as e:
                    st.error("❌ Error processing PDF. Please make sure it's a valid PDF file.")
                    st.session_state.pdf_text = None
                    st.session_state.pdf_name = None
                    return

        # Question input
        user_question = st.text_input(
            "Ask a question about the PDF:",
            placeholder="Example: What is the main topic of this document?"
        )

        if user_question:
            try:
                with st.spinner("🤔 Analyzing..."):
                    # Create prompt
                    prompt = f"""Based on the following text from a PDF document, please answer the question.
                        
                    Text: {st.session_state.pdf_text[:2000]}
                    
                    Question: {user_question}
                    
                    Answer:"""

                    answer = get_ai_response(prompt)
                    st.markdown(f"""
                        <div class='response'>
                            <div class='response-content'>
                                <strong>Q:</strong> {user_question}<br><br>
                                <strong>A:</strong> {answer}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(str(e))
                if "rate limit" in str(e).lower():
                    st.info("💡 Tip: Use your own API key in the sidebar to avoid rate limits!")

if __name__ == "__main__":
    main()
