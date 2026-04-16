# Phase 2.5: Frontend Integration Guide

## Overview
Frontend integration for AI booking agent chat and admin knowledge base management.

## New Features

### 1. 💬 ChatBox Component (`components/ChatBox.tsx`)
Real-time WebSocket chat interface for booking assistance.

**Features:**
- Real-time message streaming via WebSocket
- Automatic reconnection on disconnect
- Typing indicator while agent processes
- Message timestamps
- Tool usage display
- Connection status indicator

**Usage:**
```tsx
import ChatBox from "@/components/ChatBox";

export default function ChatPage() {
  return <ChatBox />;
}
```

### 2. 🛒 Chat Page (`app/chat/page.tsx`)
Dedicated full-screen chat interface accessible at `/chat`.

**Features:**
- Full-page chat experience
- Authentication required
- Auto-redirect to login if not authenticated

**Access:** User menu → "💬 Chat"

### 3. 📚 Knowledge Base Manager (`app/admin/knowledge/page.tsx`)
Admin interface for uploading and managing training documents.

**Features:**
- Drag-and-drop file upload
- PDF and TXT support (max 10MB)
- Document list with chunk count and status
- Delete documents
- Upload progress tracking
- Validation and error handling

**Access:** Admin menu → "📚 Knowledge Base"

## API Integration

### Document Upload
```
POST /api/admin/documents/upload
Headers: Authorization: Bearer {token}
Body: FormData with file
```

### List Documents
```
GET /api/admin/documents/list
Headers: Authorization: Bearer {token}
```

### Delete Document
```
DELETE /api/admin/documents/{docId}
Headers: Authorization: Bearer {token}
```

### WebSocket Chat
```
WS ws://localhost:8000/chat/ws/{userId}?token={jwtToken}

Message format:
{
  "message": "I want to book a room"
}

Response format:
{
  "role": "agent",
  "content": "Sure! Let me help you...",
  "timestamp": "2026-04-03T...",
  "tool_usage": {
    "toolName": "search_rooms_by_requirements",
    "input": {...},
    "output": {...}
  }
}
```

## Environment Variables

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000/api
NEXT_PUBLIC_AGENT_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_AGENT_WS_URL=ws://localhost:8000/chat/ws
```

## Testing Steps

### 1. Start Frontend
```bash
cd frontend
npm run dev
```

### 2. Login as User
- Navigate to http://localhost:3000/login
- Login with test account
- Verify auth token in localStorage

### 3. Test Chat
- Go to http://localhost:3000/chat
- Send message: "I want to book a room for April 5-10"
- Verify agent responds with room options
- Try full flow: Select room → Input dates → Create booking

### 4. Test Admin Knowledge Upload
- Login as admin user
- Go to http://localhost:3000/admin/knowledge
- Upload PDF/TXT file with room info or FAQ
- Verify document appears in list with "Stored" status
- Edit your PDF and upload again to update knowledge

### 5. Test Knowledge Search
- After uploading documents, ask in chat:
  - "What amenities does the suite have?"
  - "What's your cancellation policy?"
  - Questions that reference your uploaded documents

## Component Architecture

```
Pages/
├── pages/chat → Full-screen chat
├── pages/admin/knowledge → Knowledge management
└── pages/my-bookings → (existing) with chat link

Components/
├── ChatBox
│   ├── WebSocket connection
│   ├── Message display
│   ├── Input field
│   └── Status indicators
├── Header (updated)
│   └── Chat & Knowledge links
└── (other existing components)

Services/
├── api.ts (updated)
│   ├── uploadDocument()
│   ├── listDocuments()
│   ├── deleteDocument()
│   └── AGENT_WS_URL
└── (other existing services)

Types/
├── types.ts (updated)
│   ├── ChatMessage
│   └── Document
└── (other existing types)
```

## Error Handling

### WebSocket Disconnection
- Auto-reconnect after 3 seconds
- Show connection status to user
- Disable input when disconnected
- Graceful message on error

### Document Upload
- File type validation (PDF, TXT only)
- File size validation (max 10MB)
- Upload progress display
- User-friendly error messages

### API Errors
- 401: Redirect to login
- 403: Forbidden (admin-only access)
- 429: Rate limit message
- 5xx: Server error message

## User Flows

### Booking Flow via Chat
1. User goes to /chat
2. Sends: "I want to book a room for April 5-10"
3. Agent calls `search_rooms_by_requirements`
4. Shows available rooms with prices
5. User selects: "The suite"
6. Agent calls `create_booking`
7. Booking confirmed, appears in My Bookings

### Knowledge Upload Flow
1. Admin goes to /admin/knowledge
2. Drags PDF with FAQ onto upload area
3. System processes (chunking, embedding)
4. Document appears in list with "Stored" status
5. AI agent now answers from this document

## Next Steps

- [ ] Add floating chat widget to all pages
- [ ] Add typing speed simulation for human-like responses
- [ ] Add message reactions/feedback (👍👎)
- [ ] Add booking preview in chat before confirmation
- [ ] Add conversation history export
- [ ] Add multi-language support
- [ ] Add voice input/output (future phase)

## Troubleshooting

**"Please log in to use the chat"**
- Solution: Login at /login first

**"Connection error - Attempting to reconnect"**
- Check: Is FastAPI running on port 8000?
- Check: Is JWT_SECRET_KEY same in both backends?

**WebSocket stays "Connecting..."**
- Check: NEXT_PUBLIC_AGENT_WS_URL is correct
- Check: Token is valid
- Browser console for detailed errors

**File upload "Failed to upload"**
- Check: JWT token valid (not expired)
- Check: File size < 10MB
- Check: File is PDF or TXT

**Admin routes show "Redirecting"**
- Check: User role is "admin"
- Check: Login session active

## Code Examples

### Full Conversation
```typescript
// User flow example
1. Chat input: "I need a room for April 5-10"
2. Agent calls tools:
   - search_rooms_by_requirements(...)
   - get_available_dates(...)
3. Shows 3 available rooms
4. User selects: "suite"
5. Agent calls:
   - create_booking(room_id="suite", dates, user_info)
6. Booking created
7. Response: "Booking confirmed! Check your email."
```

### Admin Upload Workflow
```typescript
// Admin creates hotel FAQ document
1. Create hotel_faq.txt:
   "Q: What time is checkout?
    A: Checkout is at 11 AM"
2. Upload via Knowledge Base UI
3. System chunks & embeds text
4. User asks in chat: "When is checkout?"
5. Agent searches knowledge base
6. Returns: "Checkout is at 11 AM" (from FAQ)
```

## Performance Considerations

- WebSocket auto-reconnects (3s delay)
- Messages limited by Groq rate limits (~30/min free tier)
- Document chunks stored in Qdrant (384-dim vectors)
- Chat history stored in MongoDB
- Static components pre-rendered by Next.js

## Security

- ✅ JWT validation on WebSocket
- ✅ Admin-only knowledge upload (RBAC)
- ✅ Document upload sandbox (server-side validation)
- ✅ CORS configured for localhost
- ✅ Token refresh on page reload

## Support

For issues:
1. Check browser console for errors
2. Check network tab for failed requests
3. Verify backend services running
4. Check .env.local configuration
