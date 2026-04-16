# Phase 2.5 Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Client Layer)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Next.js Frontend (Port 3000)                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │  │
│  │  │  /chat     │  │/admin/kn..│  │  /my-bookings   │   │  │
│  │  │  ChatBox   │  │Knowledge   │  │  (existing)     │   │  │
│  │  │  Component │  │ Manager    │  │                 │   │  │
│  │  └────────────┘  └────────────┘  └─────────────────┘   │  │
│  │         ↓              ↓                 ↓               │  │
│  │    [WebSocket]   [REST POST]      [REST GET/PUT]       │  │
│  │         ↓              ↓                 ↓               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ↓                  ↓                    ↓
         │                  │                    │
    WS /chat/ws        POST /upload      GET/PUT /bookings
         │ (JWT)           │ (JWT)              │ (JWT)
         │                 │                    │
    ┌────────────────────────────────────────────────┐
    │        Network / Web Layer (HTTP/WS)          │
    └────────────────────────────────────────────────┘
         ↓                  ↓                    ↓
         │                  │                    │
    ┌─────────────────────────────────────────────────────────────┐
    │              Backend Services Layer                         │
    │                                                             │
    │  ┌──────────────────────┐   ┌───────────────────────────┐ │
    │  │ FastAPI Agent        │   │ Express Backend           │ │
    │  │ (Port 8000)          │   │ (Port 5000)               │ │
    │  │                      │   │                           │ │
    │  │ ┌────────────────┐   │   │ ┌─────────────────────┐  │ │
    │  │ │ LangChain      │   │   │ │ Booking API         │  │ │
    │  │ │ Agent          │   │   │ │ - createBooking     │  │ │
    │  │ │                │   │   │ │ - rescheduleBooking │  │ │
    │  │ │ Groq LLM       │   │   │ │ - cancelBooking     │  │ │
    │  │ │ Function       │   │   │ │ - listBookings      │  │ │
    │  │ │ Calling        │   │   │ │                     │  │ │
    │  │ └────────────────┘   │   │ └─────────────────────┘  │ │
    │  │                      │   │                           │ │
    │  │ ┌────────────────┐   │   │ ┌─────────────────────┐  │ │
    │  │ │ Tools (8 total)    │   │ │ Room API            │  │ │
    │  │ │ 1. search_rooms    │   │ │ - listRooms         │  │ │
    │  │ │ 2. create_booking  │   │ │ - getRoomDetails    │  │ │
    │  │ │ 3. cancel_booking  │   │ │ - getAvailability   │  │ │
    │  │ │ 4. reschedule      │   │ │                     │  │ │
    │  │ │ 5. get_bookings    │   │ │ Email Service       │  │ │
    │  │ │ 6. get_status      │   │ │ - sendConfirmation  │  │ │
    │  │ │ 7. search_kb       │   │ │ (optional, graceful)│  │ │
    │  │ │ 8. get_dates       │   │ │                     │  │ │
    │  │ └────────────────┘   │   │ └─────────────────────┘  │ │
    │  │                      │   │                           │ │
    │  │ ┌────────────────┐   │   │                           │ │
    │  │ │ Document       │   │   │                           │ │
    │  │ │ Processor      │   │   │                           │ │
    │  │ │ - Extract text │   │   │                           │ │
    │  │ │ - Chunk (1000) │   │   │                           │ │
    │  │ │ - Embed (HF)   │   │   │                           │ │
    │  │ │ - Store (QD)   │   │   │                           │ │
    │  │ └────────────────┘   │   │                           │ │
    │  │                      │   │                           │ │
    │  │ ┌────────────────┐   │   │                           │ │
    │  │ │ REST Client    │   │   │                           │ │
    │  │ │ - Call Express │───────→ (HTTP calls back)         │ │
    │  │ │ - Pass JWT     │   │   │                           │ │
    │  │ └────────────────┘   │   │                           │ │
    │  └──────────────────────┘   └───────────────────────────┘ │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
         ↓                    ↓                   ↓
         │                    │                   │
    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
    │ MongoDB     │    │ Qdrant       │    │ Groq API     │
    │ (localhost) │    │ (localhost)  │    │ (external)   │
    │             │    │              │    │              │
    │ Collections │    │ Collections  │    │ Server       │
    │ - rooms     │    │ - documents  │    │              │
    │ - bookings  │    │ - vectors    │    │ LLM Model    │
    │ - users     │    │   (384-dim)  │    │ mixtral-8x7b │
    │ - conversat.│    │              │    │              │
    │ - hotel_kb  │    │ Similarity   │    │ Function     │
    │             │    │ search       │    │ calling      │
    └─────────────┘    └──────────────┘    └──────────────┘
```

## Data Flow: Chat Message

```
User Types: "Book me a room"
        ↓
[ChatBox.tsx] Sends via WebSocket
        ↓
FastAPI /chat/ws receives (with JWT validation)
        ↓
[booking_agent.py] Processes with LangChain
        ↓
Agent selects tool: search_rooms_by_requirements()
        ↓
[express_api.py] Calls Express backend
        ↓
Express /api/rooms retrieves from MongoDB
        ↓
Express returns room list (JSON)
        ↓
[express_api.py] Converts to tool output
        ↓
[booking_agent.py] Formats natural language response
        ↓
FastAPI sends via WebSocket
        ↓
[ChatBox.tsx] Receives and displays
        ↓
User sees: "Found 3 rooms: Standard ($100/night)..."
```

## Data Flow: Document Upload

```
Admin clicks upload in /admin/knowledge/page.tsx
        ↓
[Pages/KnowledgeBase] Validates file (type, size)
        ↓
POST /api/admin/documents/upload with FormData
        ↓
FastAPI [documents.py] receives (JWT admin check)
        ↓
[document_processor.py] Extract text from PDF/TXT
        ↓
[document_processor.py] Chunk text (1000 tokens, 100 overlap)
        ↓
[document_processor.py] Embed with HuggingFace
        ↓
[vector_store.py] Store vectors in Qdrant
        ↓
MongoDB save document metadata
        ↓
API returns { id, chunks, status: "stored" }
        ↓
Frontend shows document in table with "✓ Stored"
        ↓
If admin asks in chat: "Info from doc?"
        ↓
search_knowledge_base() tool retrieves from Qdrant
```

## Data Flow: Full Booking via Chat

```
User → "/chat"
        ↓
[ChatBox] WebSocket connects with JWT
        ↓
User: "Book me suite April 5-10, 2 guests"
        ↓
Agent receives input + conversation history
        ↓
Agent decides tool: search_rooms_by_requirements()
        ↓
Tool calls Express: GET /api/rooms?check_in=...&check_out=...
        ↓
Express returns: [{ name: "Suite", price: 200, available: true }]
        ↓
Agent responds: "Found suite for $1200 total. Book it?"
        ↓
User: "Yes, book it"
        ↓
Agent decides tool: create_booking()
        ↓
Tool calls Express: POST /api/bookings
  Body: {
    roomId: "suite_id",
    checkIn: "2026-04-05",
    checkOut: "2026-04-10",
    guestName: "John",
    guestEmail: "john@email.com",
    guests: 2
  }
        ↓
Express: Check availability, create in MongoDB
        ↓
Express: Send email (optional, non-blocking)
        ↓
Express returns: { bookingId: "BOOK-123", status: "confirmed" }
        ↓
Agent: "Booking confirmed! Reference: BOOK-123"
        ↓
MongoDB saves conversation
        ↓
User navigates to /my-bookings
        ↓
Sees booking confirmed in table
```

## Component Hierarchy

```
pages/
├── chat/
│   └── page.tsx
│       └── ChatBox
│           ├── WebSocket Management
│           ├── Message Display
│           ├── Input Field
│           └── Status Indicator
│
└── admin/
    └── knowledge/
        └── page.tsx
            ├── File Upload Area
            ├── Progress Bar
            ├── Documents Table
            │   ├── Status Badges
            │   ├── Delete Buttons
            │   └── Metadata Display
            └── Info Boxes
```

## Integration Points Matrix

```
                Express     FastAPI     MongoDB    Qdrant    Groq
ChatBox           ↗                       ↓
Chat Page         →           ←           →
Knowledge Mgr                 ↔           ↔           ↔
Document Proc                 →           ↔           ↔
Tools             ↔           ←                               ←
Agent                         ←                               ↔
```

## Authentication Flow

```
1. User logs in (Express backend)
2. Express returns JWT token
3. Token stored in localStorage
4. Frontend includes token in:
   - WebSocket query param: ws://...?token={jwt}
   - HTTP Authorization header: Bearer {jwt}
   - FastAPI validates on every request
5. JWT_SECRET_KEY must match in both backends
```

## Error Handling Flow

```
Chat Error (WebSocket):
  ├─ 401 Unauthorized → Redirect to login
  ├─ Network down → Show "Connecting..." with auto-retry
  ├─ Agent error → Show friendly error message
  └─ Groq rate limit → Queue message

Upload Error:
  ├─ Invalid file type → "Only PDF & TXT"
  ├─ File too large → "Max 10MB"
  ├─ 403 Forbidden → "Admin access required"
  ├─ Server error → "Upload failed, try again"
  └─ Processing failed → Show "Error" status

Booking Error:
  ├─ Dates not available → Agent suggests alternatives
  ├─ Express down → Chat reconnects, shows error
  └─ User not found → Ask for email/phone
```

## Performance Characteristics

```
WebSocket connection:    <200ms
Message send:            <500ms (to FastAPI)
AI response generation:  2-10s  (depends on Groq)
Knowledge search:        50-100ms (Qdrant)
Document embedding:      2-5s per page
                        (HuggingFace/CPU)
Chat history retrieval:  <100ms (MongoDB)
Express API call:        100-500ms
Email send:              1-3s (optional)
```

## Deployment Architecture

```
Production (after Phase 2.5):

┌─────────────────────────────────┐
│    Next.js Frontend             │
│    Vercel (auto-deploy)         │
│    - Port: 80/443               │
│    - Domain: aurevia.hotel      │
│    - Env: AGENT_WS_URL must be  │
│           production server URL │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Express Backend                │
│  Linux VPS or Cloud VM          │
│  - Port: 5000 (private)         │
│  - 443 with reverse proxy (nginx)
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  FastAPI Agent Backend          │
│  Linux VPS or Cloud VM          │
│  - Port: 8000 (private)         │
│  - 443 with reverse proxy (nginx)
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  MongoDB Atlas                  │
│  Cloud service                  │
│  - SSL connection               │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Qdrant                         │
│  VPS deployment                 │
│  - Port: 6333 (private)         │
└─────────────────────────────────┘
```

## Database Schema

```
MongoDB (hotel_booking):
├── rooms
│   ├── _id, name, price, capacity, ...
│
├── bookings
│   ├── _id, userId, roomId, checkIn, checkOut, ...
│
├── users
│   ├── _id, email, passwordHash, role, ...
│
├── conversations (NEW)
│   ├── _id, userId, messages: [{role, content, timestamp}], ...
│
├── hotel_knowledge (NEW)
│   ├── _id, filename, chunks, uploadedAt, status, ...
│
└── knowledge_chunks (NEW)
    ├── _id, docId, content, embedding: [384-dim], metadata, ...

Qdrant:
└── documents (collection)
    ├── vector: [384 dimensions]
    ├── payload: {
    │   ├── id, content, docId, sourceType, uploadedAt
    │   }
```

---

This architecture supports:
- ✅ Real-time chat with AI
- ✅ Knowledge base management
- ✅ Multi-user sessions
- ✅ Scalable backend services
- ✅ Semantic search
- ✅ Full booking automation

**Total integration points: 15+ APIs**
**Total data flows: 12+ major flows**
