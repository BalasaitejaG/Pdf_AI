import streamlit as st
import PyPDF2
import os
from dotenv import load_dotenv
import google.generativeai as genai
import tempfile

# Load environment variables
load_dotenv()

# Configure Gemini AI
try:
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error(f"Error initializing Gemini AI: {str(e)}")
    model = None

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def main():
    st.set_page_config(page_title="PDF Question & Answer", layout="wide")
    
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

        # Query interface
        query = st.text_input("Ask any question about the PDF:", 
                            placeholder="What would you like to know about the document?")
        
        if query and model:
            with st.spinner("Finding answer..."):
                try:
                    prompt = f"""Based on the following document content, please answer the question.
                    If you can't find the specific information in the document, say so.
                    
Document content:
{st.session_state.pdf_text}

Question: {query}

Answer:"""
                    
                    response = model.generate_content(prompt)
                    st.write("### Answer:")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"Error getting response from Gemini AI: {str(e)}")
                    st.info("Please check your API key or try again later.")

if __name__ == "__main__":
    main()
