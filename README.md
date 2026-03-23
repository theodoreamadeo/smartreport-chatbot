# SmartReport Chatbot

A powerful Telegram chatbot with intelligent knowledge base management and conversation tracking. This bot leverages vector databases and PDF knowledge bases to provide context-aware responses to Telegram users.

## Features

- **LLM Integration**: Uses OpenAI's API to generate intelligent responses
- **PDF Knowledge Base**: Automatically manages and processes PDF documents for knowledge retrieval
- **Vector Database**: ChromaDB-powered vector storage for semantic search and retrieval-augmented generation (RAG)
- **Telegram Integration**: Full webhook support for receiving and responding to Telegram messages
- **Excel Logging**: Tracks all conversations and interactions in Excel format
- **FastAPI Backend**: Modern, fast, and scalable Python web framework
- **Command Handler**: Flexible command routing system with multiple interaction modes
- **Secure Configuration**: Environment-based configuration through `.env` file

## Prerequisites

- Python 3.8+
- Telegram Bot Token (from [BotFather](https://t.me/botfather))
- OpenAI API Key (from [OpenAI Platform](https://platform.openai.com/))

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smartreport-chatbot.git
cd smartreport-chatbot
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or
source .venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
SUPERVISOR_CHAT_ID=your_supervisor_chat_id_here
```

## Configuration

The application uses Pydantic Settings for configuration management. Key settings:

- **TELEGRAM_TOKEN**: Your Telegram bot token from BotFather
- **OPENAI_API_KEY**: Your OpenAI API key for model access
- **SUPERVISOR_CHAT_ID**: Chat ID of the supervisor for notifications (optional)

Settings are loaded from the `.env` file in the project root.

## Running the Application

### Development Mode
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The application will start at `http://localhost:8000` and expose the following endpoints:

- **POST** `/telegram/webhook` - Handles incoming Telegram updates
- **GET** `/health/` - Health check endpoint

## Setting Up Telegram Webhook

### Local Development (with ngrok)

1. Install ngrok: https://ngrok.com/
2. Start ngrok tunnel:
   ```bash
   ngrok http 8000
   ```
3. Make a POST request to set the webhook:
   ```bash
   curl -X POST http://localhost:8000/telegram/set-webhook \
     -H "Content-Type: application/json" \
     -d '{"url":"https://your-ngrok-url.ngrok.io/telegram/webhook"}'
   ```

### Production Deployment

Replace the ngrok URL with your actual server URL that's accessible from the internet.

## Project Structure

```
smartreport-chatbot/
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # Project license
├── .env                   # Environment variables (create this)
├── app/                   # Main application package
│   ├── api/
│   │   ├── health.py      # Health check endpoints
│   │   └── webhook.py     # Telegram webhook handler
│   ├── core/
│   │   └── config.py      # Configuration management
│   ├── models/
│   │   └── telegram_update.py  # Telegram update data models
│   ├── services/
│   │   ├── telegram_client.py  # Telegram API client
│   │   ├── openai_client.py    # OpenAI integration
│   │   ├── command_handler.py  # Command routing and handling
│   │   ├── pdf_knowledge_management.py  # PDF document processing
│   │   ├── vector_db.py        # ChromaDB vector database
│   │   ├── excel_logging.py    # Conversation logging
│   │   └── __pycache__/
│   ├── utils/
│   │   └── logging.py     # Logging utilities
│   ├── logs/              # Application logs
│   └── __pycache__/
├── chroma_db/             # ChromaDB storage
├── logs/                  # Additional logs
└── src/                   # PDF documents for knowledge base
```

## Usage

### Sending Messages to the Bot

Once the webhook is configured, send a message to your Telegram bot. The bot will:

1. Receive your message via the webhook
2. Query the knowledge base for relevant information
3. Generate a response using OpenAI
4. Send the response back to you on Telegram

### Managing the Knowledge Base

Place PDF files in the `src/` directory. The application will:
- Automatically process PDF files on startup
- Extract text and create embeddings
- Store them in the ChromaDB vector database
- Use them for context-aware responses

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **openai** - OpenAI API client
- **pydantic** - Data validation
- **chromadb** - Vector database
- **openpyxl** - Excel file handling
- **pandas** - Data processing
- **python-dotenv** - Environment variable management
- **httpx** - Async HTTP client

See `requirements.txt` for the complete list.

## Logging

The application maintains two types of logs:

1. **Application Logs**: Located in `logs/` directory
2. **Conversation Logs**: Stored in Excel format via `excel_logging.py`

All interactions with users are tracked and can be reviewed for analysis and debugging.
