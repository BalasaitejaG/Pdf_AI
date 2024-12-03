import streamlit as st
# Must be the first Streamlit command
st.set_page_config(page_title="PDF Question & Answer", layout="wide")

import PyPDF2
import os
from dotenv import load_dotenv
import google.generativeai as genai
import tempfile
import time

# Load environment variables - works for both local and Vercel
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    st.error("❌ API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Configure Gemini AI
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.sidebar.error("❌ API Key error. Please check your API key")
    st.error(f"Error: {str(e)}")
    st.stop()

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_ai_response(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_message = str(e).lower()
            if "resource_exhausted" in error_message:
                if attempt < max_retries - 1:
                    st.warning(f"Rate limit hit. Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception("Rate limit exceeded. Please try again later.")
            raise e

def main():
    st.title("📚 PDF Question & Answer")
    st.write("Upload a PDF and ask questions about its content!")

    # Initialize session state
    if 'pdf_text' not in st.session_state:
        st.session_state.pdf_text = None
    if 'pdf_name' not in st.session_state:
        st.session_state.pdf_name = None

    # File upload
    pdf_file = st.file_uploader("Upload your PDF", type="pdf")
    
    if pdf_file is not None:
        # Check if we need to process a new PDF
        if st.session_state.pdf_name != pdf_file.name:
            with st.spinner("Processing PDF..."):
                try:
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(pdf_file.getvalue())
                        tmp_file_path = tmp_file.name

                    # Extract text
                    st.session_state.pdf_text = extract_text_from_pdf(tmp_file_path)
                    st.session_state.pdf_name = pdf_file.name
                    
                    # Clean up
                    os.unlink(tmp_file_path)
                    
                    st.success("PDF processed successfully!")
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
                    st.session_state.pdf_text = None
                    st.session_state.pdf_name = None

        # Query interface
        if st.session_state.pdf_text:
            query = st.text_input("Ask any question about the PDF:", 
                                placeholder="What would you like to know about the document?")
            
            if query:
                with st.spinner("Finding answer..."):
                    try:
                        prompt = f"""Based on the following document content, please answer the question.
                        If you can't find the specific information in the document, say so.
                        
Document content:
{st.session_state.pdf_text}

Question: {query}

Answer:"""
                        
                        answer = get_ai_response(prompt)
                        st.write("### Answer:")
                        st.write(answer)
                        
                    except Exception as e:
                        st.error(str(e))
                        if "rate limit" in str(e).lower():
                            st.info("The service is currently busy. Please try again in a few minutes.")

if __name__ == "__main__":
    main()
