# PDF Question Answering System

This application allows users to upload PDF documents and ask questions about their content. The system uses Google's Gemini AI to understand and answer questions based on the PDF content.

## Features
- PDF document upload
- Text extraction from PDFs
- Interactive question-answering interface using Gemini AI
- User-friendly web interface using Streamlit

## Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Google API key:
   - Go to https://makersuite.google.com/app/apikey
   - Create a new API key (it's free!)

3. Create a `.env` file and add your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage
1. Upload a PDF document using the file uploader
2. Wait for the document to be processed
3. Type your question in the text input
4. Get instant answers based on the PDF content using Gemini AI

## Note
The application uses Google's Gemini AI which offers free API access with generous limits.
