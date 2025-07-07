# Anton AI Assistant

A sophisticated AI assistant application built with Python, featuring PySide6 GUI, Google's Gemini AI integration, voice recognition, and file management capabilities.

## Features

- **AI Chat Interface**: Modern chat interface powered by Google Gemini AI
- **Voice Recognition**: Real-time speech-to-text using Vosk models
- **Text-to-Speech**: Natural voice responses using pyttsx3
- **File Management**: Create, read, update, and delete files through voice or text commands
- **Web Search Integration**: Smart web search capabilities using Google Custom Search API
- **Modern UI**: Clean, responsive interface built with PySide6

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Microphone (for voice features)
- Internet connection (for AI and search features)

### Installation

1. **Clone or download the project**
2. **Set up environment variables**:
   Create a `.env` file in the project root with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   SEARCH_ENGINE_ID=your_search_engine_id_here
   CUSTOM_SEARCH_KEY=your_custom_search_key_here
   ```

3. **Install dependencies**:
   The project uses a virtual environment with all dependencies already installed.

### Running the Application

#### Option 1: Using the run script (Recommended)
- **Windows**: Double-click `run_anton.bat`
- **PowerShell**: Run `.\run_anton.ps1`

#### Option 2: Manual execution
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the application
python app.py
```

## Project Structure

```
PRJ2/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── venv/                 # Virtual environment
├── Anton_Files/          # User-created files directory
├── anton_icons/          # UI icons
├── models/               # Voice recognition models
├── .env                  # Environment variables (create this)
├── run_anton.bat         # Windows batch script
├── run_anton.ps1         # PowerShell script
└── README.md            # This file
```

## API Keys Setup

To use all features, you'll need:

1. **Google Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Google Custom Search API Key**: Get from [Google Developers Console](https://console.developers.google.com/)
3. **Custom Search Engine ID**: Create at [Google Custom Search](https://cse.google.com/)

## Voice Commands

- **File operations**: "create file", "read file", "update file", "delete file"
- **General queries**: Ask any question, Anton will determine if web search is needed
- **Assistant info**: "Who are you?", "What can you do?"

## Troubleshooting

- **Voice recognition issues**: Ensure microphone permissions are granted
- **API errors**: Check your API keys in the `.env` file
- **Dependencies**: Use the provided virtual environment

## Dependencies

- PySide6 - GUI framework
- Google Generative AI - AI integration
- Vosk - Speech recognition
- PyAudio - Audio processing
- pyttsx3 - Text-to-speech
- SpeechRecognition - Speech processing
- python-dotenv - Environment variables

## Development

This project was cleaned up and optimized:
- Removed unnecessary conda environment (saving hundreds of MB)
- Switched to pip and virtual environment
- Updated dependencies to match actual requirements
- Created easy-to-use run scripts