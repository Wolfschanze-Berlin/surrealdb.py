# ChatGPT FastAPI Integration

A FastAPI application with OpenAI ChatGPT integration and SurrealDB for conversation persistence.

## Features

- 🤖 OpenAI ChatGPT integration
- 💾 Conversation and message persistence with SurrealDB
- 📚 Swagger/OpenAPI documentation
- 🔄 Real-time chat with conversation history
- 🐳 Docker support with multi-stage builds
- ⚡ FastAPI with async/await support
- 🔧 Environment-based configuration

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- SurrealDB (included in Docker setup)

### Installation

1. Clone the repository and navigate to the chat-gpt sample:
```bash
cd samples/chat-gpt
```

2. Copy the environment file and configure:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running with Docker (Recommended)

1. Set your OpenAI API key in environment:
```bash
export OPENAI_API_KEY=your-api-key-here
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the API:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- SurrealDB: http://localhost:8001

### Running Locally

1. Start SurrealDB:
```bash
# Using Docker
docker run -d --name surrealdb -p 8001:8000 surrealdb/surrealdb:latest start --log trace --user root --pass root memory

# Or install SurrealDB locally and run:
surreal start --log trace --user root --pass root memory
```

2. Start the FastAPI application:
```bash
python main.py
```

## API Endpoints

### Chat Endpoints

- `POST /chat/simple` - Simple chat without history
- `POST /chat/completion` - Chat with conversation history (in-memory)
- `POST /chat/history` - Chat with persistent conversation history
- `GET /chat/models` - Get available models information
- `GET /chat/status` - Get service status

### Conversation Management

- `POST /chat/conversations` - Create a new conversation
- `GET /chat/conversations/{conversation_id}` - Get conversation with messages
- `GET /chat/conversations/user/{user_id}` - Get user's conversations
- `PUT /chat/conversations/{conversation_id}` - Update conversation
- `DELETE /chat/conversations/{conversation_id}` - Delete conversation

### Message Management

- `GET /chat/messages/{message_id}` - Get a specific message

## Usage Examples

### Simple Chat

```bash
curl -X POST "http://localhost:8000/chat/simple" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

### Chat with Persistent History

```bash
# Start a new conversation
curl -X POST "http://localhost:8000/chat/history" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with Python programming",
    "user_id": "user123"
  }'

# Continue the conversation
curl -X POST "http://localhost:8000/chat/history" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain list comprehensions?",
    "conversation_id": "conversations:uuid-here",
    "user_id": "user123"
  }'
```

### Create a Conversation

```bash
curl -X POST "http://localhost:8000/chat/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Programming Help",
    "user_id": "user123"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `OPENAI_MAX_TOKENS` | Maximum tokens per response | `1000` |
| `OPENAI_TEMPERATURE` | Sampling temperature | `0.7` |
| `SURREALDB_URL` | SurrealDB connection URL | `ws://localhost:8001/rpc` |
| `SURREALDB_NAMESPACE` | SurrealDB namespace | `chatgpt` |
| `SURREALDB_DATABASE` | SurrealDB database | `conversations` |
| `SURREALDB_USERNAME` | SurrealDB username | `root` |
| `SURREALDB_PASSWORD` | SurrealDB password | `root` |
| `APP_NAME` | Application name | `ChatGPT FastAPI Integration` |
| `DEBUG` | Debug mode | `false` |
| `PORT` | Server port | `8000` |

## Database Schema

### Conversations Table

```sql
DEFINE TABLE conversations SCHEMAFULL;
DEFINE FIELD title ON TABLE conversations TYPE string;
DEFINE FIELD user_id ON TABLE conversations TYPE option<string>;
DEFINE FIELD created_at ON TABLE conversations TYPE datetime DEFAULT time::now();
DEFINE FIELD updated_at ON TABLE conversations TYPE datetime DEFAULT time::now();
DEFINE FIELD is_active ON TABLE conversations TYPE bool DEFAULT true;
```

### Messages Table

```sql
DEFINE TABLE messages SCHEMAFULL;
DEFINE FIELD conversation_id ON TABLE messages TYPE record<conversations>;
DEFINE FIELD role ON TABLE messages TYPE string ASSERT $value IN ['user', 'assistant', 'system'];
DEFINE FIELD content ON TABLE messages TYPE string;
DEFINE FIELD tokens_used ON TABLE messages TYPE option<int>;
DEFINE FIELD model ON TABLE messages TYPE option<string>;
DEFINE FIELD created_at ON TABLE messages TYPE datetime DEFAULT time::now();
```

## Development

### Project Structure

```
samples/chat-gpt/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── database.py          # Database connection and initialization
├── models.py            # Pydantic models
├── crud.py              # Database CRUD operations
├── chat_service.py      # OpenAI integration service
├── routers/
│   ├── __init__.py
│   └── chat.py          # Chat API routes
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── Dockerfile           # Multi-stage Docker build
├── docker-compose.yml   # Development environment
├── .env.example         # Environment variables template
└── README.md           # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

## Docker

### Building the Image

```bash
docker build -t chatgpt-fastapi .
```

### Running with Docker

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-api-key \
  -e SURREALDB_URL=ws://host.docker.internal:8001/rpc \
  chatgpt-fastapi
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the SurrealDB Python SDK examples and follows the same license terms.

## Support

For issues and questions:
- Check the [SurrealDB Python SDK documentation](https://github.com/surrealdb/surrealdb.py)
- Open an issue in the main repository
- Join the SurrealDB community Discord