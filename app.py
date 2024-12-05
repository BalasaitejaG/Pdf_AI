import time
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
import streamlit as st
import atexit
import extra_streamlit_components as stx

# Must be the first Streamlit command
st.set_page_config(page_title="PDF Question & Answer 📚", layout="wide")

# Load environment variables
load_dotenv()

# Add cookie manager for persistent trial count
def get_cookie_manager():
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="unique_cookie_manager")
    return st.session_state.cookie_manager

# Initialize session state with persistent trial count
if 'trial_count' not in st.session_state:
    cookie_manager = get_cookie_manager()
    saved_count = cookie_manager.get('trial_count')
    st.session_state.trial_count = int(saved_count) if saved_count else 0

if 'user_api_key' not in st.session_state:
    st.session_state.user_api_key = None

if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
    
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = None

# Add after load_dotenv()
default_api_key = os.getenv('GOOGLE_API_KEY')
if not default_api_key:
    st.error("⚠️ No default API key found. Please add your API key in the sidebar.")

def validate_api_key(api_key):
    """Validate API key"""
    if not api_key or len(api_key.strip()) < 10:
        return False
    return True

def get_ai_response(prompt):
    """Get response from Gemini AI"""
    # Check trial limit and API key availability
    if not st.session_state.user_api_key and not default_api_key:
        raise Exception("❌ Please add your API key to continue.")
    if not st.session_state.user_api_key and st.session_state.trial_count >= 5:
        raise Exception("❌ Trial limit reached! Please add your own API key to continue.")
    
    try:
        # Configure API
        api_key = st.session_state.user_api_key or os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Increment trial count if using default API and save to cookie
        if not st.session_state.user_api_key:
            st.session_state.trial_count += 1
            cookie_manager = get_cookie_manager()
            cookie_manager.set('trial_count', str(st.session_state.trial_count))
            
        return response.text
    except Exception as e:
        raise Exception(f"❌ Error: {str(e)}")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF"""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def main():
    # Header with emojis
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 2rem;'>
            📚 PDF AI Assistant 🤖
        </h1>
        <p style='text-align: center; font-size: 1.2em; margin-bottom: 3rem;'>
            Upload your PDF and let AI answer your questions! ✨
        </p>
    """, unsafe_allow_html=True)

    # Sidebar for API key
    with st.sidebar:
        st.markdown("### 🔑 API Key Settings")
        user_api_key = st.text_input(
            "Enter your API key",
            type="password",
            help="Get your API key from Google AI Studio"
        )

        if user_api_key:
            if validate_api_key(user_api_key):
                st.session_state.user_api_key = user_api_key
                st.success("✨ API key added successfully!")
            else:
                st.error("❌ Invalid API key format")
                st.session_state.user_api_key = None

        # Show trial usage
        if not st.session_state.user_api_key:
            remaining = max(0, 5 - st.session_state.trial_count)
            st.markdown(f"### 🎁 Trial Status")
            st.markdown(f"Remaining questions: **{remaining}/5**")
            
            if remaining <= 0:
                st.warning("⚠️ Trial limit reached!")
                st.markdown("""
                    **Get your free API key:**
                    1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey) 🔗
                    2. Create your API key ✨
                    3. Paste it above 📋
                """)
        else:
            st.success("🚀 Using your personal API key")

    # Main content
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        uploaded_file = st.file_uploader(
            "📄 Upload your PDF document",
            type="pdf",
            help="Drag and drop or click to upload"
        )

    if uploaded_file:
        try:
            if st.session_state.pdf_name != uploaded_file.name:
                with st.spinner("🔍 Reading PDF..."):
                    pdf_text = extract_text_from_pdf(uploaded_file)
                    st.session_state.pdf_text = pdf_text
                    st.session_state.pdf_name = uploaded_file.name
                st.success("✅ PDF processed successfully!")

            # Question input
            if not st.session_state.user_api_key and st.session_state.trial_count >= 5:
                st.warning("⚠️ Trial limit reached! Please add your API key to continue.")
            else:
                question = st.text_input(
                    "🤔 Ask a question about your PDF:",
                    placeholder="Example: What is the main topic of this document?"
                )

                if question:
                    try:
                        with st.spinner("🧠 Thinking..."):
                            prompt = f"""Based on this PDF text, please answer the question.
                            
                            Text: {st.session_state.pdf_text[:2000]}
                            
                            Question: {question}
                            
                            Answer:"""
                            
                            answer = get_ai_response(prompt)
                            
                            st.markdown("### 💡 Answer")
                            st.markdown(f">{answer}")
                            
                            # Show remaining trials
                            if not st.session_state.user_api_key:
                                remaining = max(0, 5 - st.session_state.trial_count)
                                st.info(f"ℹ️ {remaining} questions remaining in trial mode")
                                
                    except Exception as e:
                        st.error(str(e))
                        
        except Exception as e:
            st.error("❌ Error processing PDF. Please make sure it's a valid PDF file.")

if __name__ == "__main__":
    main()
