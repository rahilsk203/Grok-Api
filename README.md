# Grok API

A free, unofficial API wrapper for Grok AI that allows access without requiring official API keys or user authentication.

## Features

- **Fast Rate Limit Bypass**: Enhanced rate limiting with fast retry mechanisms to minimize delays
- **Proxy Support**: Full proxy support for bypassing restrictions
- **Conversation Persistence**: Maintain conversation history and context
- **Multiple Model Support**: Supports grok-3-auto, grok-3-fast, grok-4, and grok-4-mini-thinking-tahoe
- **Robust Error Handling**: Comprehensive error handling and retry mechanisms

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/Grok-Api.git
cd Grok-Api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

Start the API server:
```bash
python api_server.py
```

The server will start on `http://localhost:6969`

### API Endpoints

- `GET /` - Health check
- `POST /ask` - Send messages to Grok

### API Examples

**Basic request:**
```bash
curl -X POST http://localhost:6970/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "grok-3-fast"
  }'
```

**With proxy:**
```bash
curl -X POST http://localhost:6970/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "grok-3-fast",
    "proxy": "http://proxy-server:port"
  }'
```

**With proxy authentication:**
```bash
curl -X POST http://localhost:6969/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "grok-3-fast",
    "proxy": "http://username:password@proxy-server:port"
  }'
```

**Continue conversation:**
```bash
curl -X POST http://localhost:6969/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Follow-up question",
    "model": "grok-3-fast",
    "extra_data": {
      // ... conversation data from previous response
    }
  }'
```

## API Request Format

The API supports multiple input formats:

1. **Simple format:**
```json
{
  "message": "Your message here",
  "model": "grok-3-fast",
  "proxy": "optional proxy"
}
```

2. **Google-style format:**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Your message here"
        }
      ]
    }
  ],
  "model": "grok-3-fast",
  "proxy": "optional proxy"
}
```

## Response Format

The API returns responses in the following format:

```json
{
  "status": "success",
  "response": "Full response text",
  "stream_response": ["token1", "token2", "..."],
  "extra_data": {
    // Conversation data for continuing the conversation
  }
}
```

## Configuration

- **Port**: The server runs on port 6969 by default
- **Host**: By default, it binds to 0.0.0.0 (accessible from other machines)
- **Threading**: Enabled for concurrent requests

## Rate Limiting

The API includes sophisticated rate limiting bypass mechanisms:
- Fast retry strategy with minimal delays
- Exponential backoff for sustained rate limits
- Anti-bot detection bypass
- Session rotation on failures

## Deployment

For production deployment, you can use:

**Using Uvicorn with multiple workers:**
```bash
uvicorn api_server:app --host 0.0.0.0 --port 6969 --workers 10
```

**Using Gunicorn:**
```bash
gunicorn api_server:app -w 10 -b 0.0.0.0:6969
```

## Dependencies

- Python 3.10+
- Flask
- curl_cffi
- coincurve
- beautifulsoup4
- colorama

## Troubleshooting

- If you encounter rate limiting, try using a proxy
- For anti-bot detection issues, the system will automatically attempt to bypass
- Check the logs for detailed error information

## Disclaimer

This is an unofficial API wrapper. Use responsibly and in compliance with xAI's terms of service.