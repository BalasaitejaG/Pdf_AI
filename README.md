# PDF AI Assistant 🤖📚

A powerful PDF Question & Answer application that combines the capabilities of Google's Gemini AI with an intuitive Streamlit interface. Upload any PDF and get instant, intelligent answers to your questions about the document content!

![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit Version](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Key Features

### Core Functionality
- 📄 **Smart PDF Processing**: Upload and analyze any PDF document
- 🧠 **AI-Powered Q&A**: Get contextual answers using Google's Gemini AI
- 💬 **Natural Language Understanding**: Ask questions in plain English
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices

### User-Friendly Features
- 🎁 **Free Trial System**: Start with 5 free questions using our API key
- 🔑 **Custom API Key Support**: Use your own Gemini API key for unlimited access
- 🍪 **Session Persistence**: Trial usage tracked across browser sessions
- 🌙 **Dark Mode**: Easy on the eyes with dark theme support
- ⚡ **Fast Processing**: Quick document parsing and response generation

## 🚀 Getting Started

### System Requirements
- Python 3.8 or newer
- 4GB RAM (minimum)
- Internet connection for AI functionality

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/BalasaitejaG/Pdf_AI.git
   cd pdf-ai
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # For Windows:
   venv\Scripts\activate
   # For macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Add your Google Gemini API key to the .env file
   # Create a .env file in the root directory of the project if it doesn't exist.
   # Add the following line to the .env file, replacing "your_gemini_api_key_here" with your actual API key:
   # GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Running the Application

1. **Start the App**
   ```bash
   streamlit run app.py
   ```

2. **Access the Interface**
   - Open your browser
   - Go to `http://localhost:8501`
   - The URL will also appear in your terminal

## 📖 Detailed Usage Guide

### Trial Mode
- **Free Access**: Start with 5 complimentary questions
- **No Registration**: Just upload your PDF and start asking
- **Persistent Counter**: Trial usage tracked across sessions
- **Upgrade Option**: Switch to unlimited access with your API key

### Using Your Own API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Generate your Gemini API key
3. Enter it in the app's sidebar
4. Enjoy unlimited questions and faster processing

### Best Practices for Questions
- Be specific and clear in your questions
- Reference specific sections or topics from the PDF
- Ask one thing at a time for best results
- Rephrase if you don't get a satisfactory answer

## 🛠️ Technical Architecture

### Core Components
- **Frontend**: Streamlit v1.29.0
- **PDF Processing**: PyPDF2 v3.0.1
- **AI Engine**: Google Gemini AI v0.3.1
- **State Management**: 
  - Streamlit session state
  - Browser cookies (extra-streamlit-components v0.1.60)
- **Configuration**: python-dotenv v1.0.0

### File Structure
```
pdf-ai/
├── app.py              # Main application logic
├── .env               # Environment configuration
├── .env.example       # Environment template
├── requirements.txt   # Project dependencies
├── README.md         # Documentation
└── .streamlit/       # Streamlit configuration
    ├── config.toml   # UI settings
    └── secrets.toml  # Secure credentials
```

## 🔒 Security Features

### API Key Protection
- Environment variable storage
- Optional user-provided keys
- Secure key validation
- No key storage in code

### Trial System Security
- Cookie-based tracking
- Tamper-resistant design
- Rate limiting protection
- Secure state management

## ⚠️ Known Limitations

### PDF Processing
- Large PDFs may take longer to process
- Some complex PDF formats might not parse perfectly
- Scanned PDFs require good text quality

### API Constraints
- Trial mode limited to 5 questions
- API rate limits may apply
- Response time varies with PDF size
- Internet connection required

## 🔍 Troubleshooting Guide

### Common Issues and Solutions

1. **Slow Processing**
   - Reduce PDF file size
   - Check internet connection
   - Clear browser cache
   - Restart the application

2. **API Key Issues**
   - Verify key is correctly copied
   - Check for leading/trailing spaces
   - Ensure key has required permissions
   - Monitor usage quotas

3. **PDF Problems**
   - Ensure PDF is text-searchable
   - Try re-saving the PDF
   - Check file isn't corrupted
   - Verify file permissions

## 🎯 Future Roadmap

### Planned Features
- [ ] Multi-language support
- [ ] Document summarization
- [ ] Batch question processing
- [ ] PDF annotation tools
- [ ] Advanced search capabilities
- [ ] User authentication
- [ ] Usage analytics
- [ ] Cloud storage integration

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (if available)
5. Submit a pull request


## 🙏 Acknowledgments

- Google Gemini AI team for the powerful AI model
- Streamlit team for the excellent web framework
- PyPDF2 developers for PDF processing capabilities
- Open source community for various tools and libraries

## 📞 Support & Contact

- Create an issue for bug reports
- Star the repository if you find it useful
- Fork for your own modifications
- Contact: [Your Contact Information]

---

Made with ❤️ by --Balasaiteja--

*Last Updated: January 2024*
