# PDF Question & Answer Assistant

An intelligent PDF document analysis tool that allows you to ask questions about your PDF documents and get AI-powered answers.

## Features

- PDF Document Upload
- Natural Language Question Answering
- AI-Powered Analysis
- Smart Content Search

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
   - Create a `.env` file in the project root
   - Add your API key in the following format:
```
GOOGLE_API_KEY=your_api_key
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open the provided URL in your browser
3. Upload a PDF document
4. Ask questions about the document content

## Requirements

- Python 3.9+
- Required packages listed in `requirements.txt`
- Valid API key for the AI service
