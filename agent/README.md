# 🤖 Hotel Booking AI Agent - FastAPI Backend

**Phase 2: LangChain Agent, WebSocket Chat & Document Management**

Hotel booking agent backend powered by FastAPI, LangChain, Groq LLM, and Qdrant vector database with real-time conversational AI.

## 📁 Project Structure

```
agent/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Environment variables (create from example)
├── .gitignore                   # Git ignore patterns
│
├── config/                      # Configuration module
│   ├── __init__.py
│   ├── settings.py              # Settings from environment variables
│   ├── mongodb.py              # MongoDB async connection
│   ├── qdrant.py               # Qdrant async client
│   └── groq.py                 # Groq LLM client
│
├── services/                    # External service clients
│   ├── __init__.py
│   ├── mongo_db.py             # MongoDB connection
│   ├── qdrant_client.py        # Qdrant vector DB client
│   ├── groq_client.py          # Groq LLM client
│   ├── embeddings_client.py    # HuggingFace embeddings
│   ├── express_api.py          # Express backend REST client [NEW]
│   └── vector_store.py         # Qdrant vector operations [NEW]
│
├── schemas/                     # Pydantic models
│   ├── __init__.py
│   └── models.py               # Request/response schemas
│
├── routers/                     # API endpoints
│   ├── __init__.py
│   ├── health.py               # Health check
│   ├── chat.py                 # WebSocket chat [UPDATED]
│   └── documents.py            # Document upload [UPDATED]
│
├── agents/                      # LangChain agents [PHASE 2]
│   ├── __init__.py
│   ├── tools.py                # Tool definitions [NEW]
│   └── booking_agent.py        # LangChain agent with Groq [NEW]
│
├── middleware/                  # Custom middleware
│   └── __init__.py
│
├── models/                      # Data models
│   └── __init__.py
│
└── utils/                       # Utility functions
    ├── __init__.py
    └── logger.py               # Logging configuration
```

## 🚀 Phase 2: Features

### ✨ New Features
1. **LangChain Agent** - Multi-turn conversation with memory
2. **Groq Function Calling** - 8 booking automation tools
3. **WebSocket Chat** - Real-time bidirectional communication
4. **Document Management** - PDF upload and knowledge base
5. **Vector Search** - RAG with Qdrant embeddings
6. **MongoDB Chat History** - Persistent conversation storage
7. **Tool Execution** - Automated booking operations

### 🛠 Supported Tools

1. **search_rooms** - Find available rooms by dates and guests
2. **create_booking** - Book a room for user
3. **get_user_bookings** - Retrieve user's booking history
4. **cancel_booking** - Cancel an existing booking
5. **reschedule_booking** - Change booking dates
6. **get_booking_status** - Check booking status
7. **search_knowledge_base** - Query hotel info and policies
8. **get_available_dates** - Check room availability calendar

## 📋 Setup Instructions

### Step 1: Copy .env file
```bash
cp .env.example .env
```

### Step 2: Edit .env with credentials
```env
# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_ENV=development

# Groq API (get from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key

# MongoDB
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true
MONGO_DB_NAME=hotel_booking

# Qdrant (your VPS instance)
QDRANT_URL=http://your-vps-ip:6333

# Express Backend
EXPRESS_HOST=localhost
EXPRESS_PORT=5000

# JWT (get from Express backend .env)
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run FastAPI server
```bash
python main.py
```

Server runs at: `http://localhost:8000`

## 🌐 API Endpoints

### Health Check
- **GET** `/health` - Service health status

### WebSocket Chat [NEW]
- **WS** `/chat/ws/{user_id}?token={jwt_token}` - Real-time chat connection
  - Query params: `user_id` (from JWT), `token` (JWT auth token)
  - Message format: `{"message": "user input"}`
  - Response types: `connection`, `message`, `status`, `error`

### Chat History [NEW]
- **GET** `/chat/history/{user_id}?token={jwt_token}` - Get conversation history
- **POST** `/chat/clear/{user_id}?token={jwt_token}` - Clear conversation

### Document Management [NEW]
- **POST** `/admin/documents/upload?token={jwt_token}` - Upload PDF
  - Form data: `file` (PDF), `doc_type` (query param)
  - Admin auth required
  
- **GET** `/admin/documents/knowledge-base?token={jwt_token}` - Knowledge base stats
- **DELETE** `/admin/documents/clear-knowledge-base?token={jwt_token}` - Clear KB
- **POST** `/admin/documents/init-vector-store?token={jwt_token}` - Initialize collections

## 💬 WebSocket Chat Example

### Client-side (JavaScript/TypeScript)
```javascript
const userId = "user_id_from_jwt";
const token = "jwt_token";

const socket = new WebSocket(
  `ws://localhost:8000/chat/ws/${userId}?token=${token}`
);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "connection") {
    console.log("Connected:", data.message);
  } else if (data.type === "message") {
    console.log("Agent:", data.content);
  } else if (data.type === "status") {
    console.log("Status:", data.message);
  } else if (data.type === "error") {
    console.error("Error:", data.message);
  }
};

// Send message
socket.send(JSON.stringify({ message: "I want to book a room" }));
```

## 📤 Document Upload Example

```bash
curl -X POST "http://localhost:8000/admin/documents/upload?token=YOUR_TOKEN&doc_type=knowledge" \
  -H "accept: application/json" \
  -F "file=@hotel_policies.pdf"
```

## 🔄 Conversation Flow

```
User Message
    ↓
WebSocket → FastAPI Chat Router
    ↓
LangChain Agent (Multi-turn Memory)
    ↓
Groq LLM (mixtral-8x7b-32768)
    ↓
Tool Calling Decision
    ├─ search_rooms → Express API
    ├─ create_booking → Express API
    ├─ search_knowledge_base → Qdrant Search
    └─ ... other tools
    ↓
Groq Response Generation
    ↓
WebSocket Response → User
```

## 🧠 Agent Capabilities

The agent can:
1. Search available rooms based on dates and preferences
2. Create new bookings on behalf of users (if confirmed)
3. List user's existing bookings
4. Cancel or reschedule bookings
5. Answer questions about hotel policies and amenities
6. Provide room availability information
7. Maintain conversation history for context
8. Handle errors gracefully with helpful suggestions

## 📊 Vector Database

- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Dimensions**: 384-dim vectors
- **Distance Metric**: Cosine similarity
- **Collections**:
  - `hotel_knowledge` - Hotel info and policies
  - `conversations` - Conversation embeddings

## 🔐 Authentication

All endpoints require JWT token validation:
- Issued by Express backend
- Verified in FastAPI with JWT_SECRET_KEY
- 7-day expiration (from Express)
- User ID validated against token payload

## 📝 Configuration

Edit `config/settings.py` or .env for:
- `CHUNK_SIZE` - Document chunk size (1000 tokens)
- `CHUNK_OVERLAP` - Chunk overlap (200 tokens)
- `WEBSOCKET_HEARTBEAT_INTERVAL` - Keep-alive interval (30 seconds)

## 🧪 Testing

### 1. Check health
```bash
curl http://localhost:8000/health
```

### 2. Get docs
```
http://localhost:8000/docs
```

### 3. Test WebSocket (use WebSocket client)
```
ws://localhost:8000/chat/ws/{user_id}?token={jwt_token}
```

## 🐛 Debugging

Enable verbose logging:
```bash
# In .env
LOG_LEVEL=DEBUG
```

Check logs for:
- Service initialization
- WebSocket connections
- Tool executions
- Vector search results
- API call responses

## 🔄 Integration Points

### With Express Backend
- **REST Calls**: search_rooms, create_booking, cancel_booking, etc.
- **Authentication**: JWT token validation
- **Database**: Shared `hotel_booking` MongoDB database

### With Next.js Frontend
- **WebSocket**: `/chat/ws/{user_id}?token={token}`
- **Real-time**: Bidirectional messages
- **History**: GET `/chat/history/{user_id}?token={token}`

## 📚 LangChain Integration

- **Memory**: ConversationBufferMemory with MongoDB backend
- **LLM**: Groq mixtral-8x7b-32768 with function calling
- **Tools**: Custom tool definitions with Groq format
- **Parser**: Automatic tool call parsing and execution

## 🚨 Error Handling

Agent handles:
- Invalid dates (past dates, checkout before checkin)
- Insufficient guests
- Booking conflicts with existing reservations
- API failures with retry logic
- Invalid user authentication

## 🎯 Next Steps (Phase 3)

- [ ] Advanced RAG with multi-document support
- [ ] Streaming responses for long-running operations
- [ ] Analytics and conversation metrics
- [ ] Admin dashboard for knowledge base management
- [ ] Multi-language support
- [ ] Voice chat integration

## 📞 Support

Check `/docs` endpoint for interactive API documentation with all schema details.


Environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `FASTAPI_PORT` | 8000 | FastAPI server port |
| `GROQ_API_KEY` | - | Groq API key (required) |
| `MONGO_URI` | mongodb://localhost:27017 | MongoDB URI |
| `QDRANT_URL` | http://localhost:6333 | Qdrant URL |
| `EMBEDDINGS_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | HuggingFace model |
| `LOG_LEVEL` | INFO | Logging level |

## 🚀 Next Phases

- **Phase 2**: LangChain agent with 8 booking tools
- **Phase 3**: Vector RAG with document upload
- **Phase 4**: Frontend integration (chat widget)
