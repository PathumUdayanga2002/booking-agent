# Phase 3.5: Conversation History Persistence & Booking ID Implementation

## Overview
Implemented two major features:
1. **Human-Readable Booking IDs**: Format `BKG-{EMAIL_PREFIX}-{MONGO_ID_PREFIX}` (e.g., BKG-PATHUM-69D61FE)
2. **Persistent Conversation History**: Chat history saved to MongoDB and restored across sessions

---

## 1. Booking ID System

### What Changed

#### Backend Changes

**1. Booking Model** (`backend/src/models/Booking.js`)
```javascript
bookingId: { type: String, unique: true, sparse: true, index: true }
```
- Added field to store human-readable booking ID
- Indexed for fast lookups when users provide ID for reschedule

**2. Booking ID Generator** (`backend/src/utils/bookingIdGenerator.js`) - NEW FILE
```javascript
generateBookingId(guestEmail, mongoId)
// Format: BKG-{emailName.substring(0,10)}-{mongoId.substring(0,7).toUpperCase()}
// Example: BKG-PATHUM-69D61FE
```
- Extracts email prefix (first 10 chars of part before @)
- Uses MongoDB ObjectId prefix (first 7 chars, uppercase)
- Generates unique, memorable booking reference

**3. Booking Controller** (`backend/src/controllers/bookingController.js`)
```javascript
const bookingId = generateBookingId(guestEmail, booking._id);
booking.bookingId = bookingId;
await booking.save();
```
- After creating booking, generates and saves bookingId
- Bookings now have human-readable ID immediately

**4. Email Templates** (`backend/src/utils/emailService.js`)
- Added booking ID section to confirmation email (gold background, centered)
- Added booking ID section to reschedule email
- Format: `<p style="font-family: 'Courier New', monospace;">${booking.bookingId}</p>`
- Instructions: "Save this ID for future reference and support inquiries"

### User Flow
```
User Books Room → Backend Creates Booking → generateBookingId() → bookingId Saved → Email Sent with ID
Example: "Your Booking ID: BKG-PATHUM-69D61FE"
```

---

## 2. Persistent Conversation History

### Database Schema

**MongoDB Model** (`backend/src/models/Conversation.js`) - NEW FILE
```javascript
{
  userId: String,           // From JWT token
  role: "user" | "assistant",
  content: String,           // Message text
  metadata: Object,          // Optional metadata (tool calls, etc.)
  createdAt: Timestamp,
  updatedAt: Timestamp
}

// Indexes:
// - Single index on userId for fast lookup
// - Compound index on (userId, createdAt) for ordered retrieval
```

### Backend Services

**1. Conversation Service** (`backend/src/services/conversationService.js`) - NEW FILE
```javascript
async saveMessage(userId, role, content, metadata)
async getConversationHistory(userId, limit=50)
async clearConversationHistory(userId)
async getRecentConversations(limit=100)  // Admin only
```

**2. Express Routes** (`backend/src/routers/conversationRoutes.js`) - NEW FILE
```
POST   /api/conversations/save                // Save message
GET    /api/conversations/history/:userId     // Get user's history
DELETE /api/conversations/history/:userId     // Clear user's history
GET    /api/conversations/admin/recent        // Admin: recent conversations
```

**3. Validation Schemas** (`backend/src/validators/conversationSchemas.js`) - NEW FILE
```javascript
saveConversationSchema - Validates: userId, role, content, metadata
conversationHistoryQuerySchema - Validates: userId, limit (1-500)
```

### Python Agent Services

**1. Conversation Storage Service** (`agent/services/conversation_storage.py`) - NEW FILE
```python
class ConversationStorageService:
    async save_message(user_id, role, content, metadata)
    async get_history(user_id, limit=50)
    async clear_history(user_id)
```
- HTTP client for communication with Express backend
- Non-blocking: Failures don't crash chat
- Uses `httpx` async HTTP library

### Python Agent Updates

**1. Booking Agent** (`agent/agents/booking_agent.py`)

**Updated `__init__`**:
```python
self.storage_service = get_storage_service()
```

**Updated `initialize`**:
```python
# Load previous conversation history
history_messages = await self.storage_service.get_history(user_id, limit=50)
# Reconstruct in-memory conversation_history for Groq context
```

**Updated `process_message`**:
```python
# Save user message
await self.storage_service.save_message(user_id, "user", message)
# Get response
response = await self._get_agent_response()
# Save assistant response
await self.storage_service.save_message(user_id, "assistant", response)
```

### User Flow

```
User Connects (WebSocket)
↓
Agent Initialize()
↓
Load previous 50 messages from MongoDB
↓
Set conversation_history in memory
↓
Send welcome message
↓
User Types Message
↓
Save message to MongoDB (user)
↓
Groq generates response (with context of loaded history)
↓
Save response to MongoDB (assistant)
↓
User Logs Out & Logs Back In Later
↓
WebSocket reconnects
↓
Agent Initialize() loads previous history AGAIN
↓
Agent remembers previous conversations!
```

---

## 3. Integration Points

### Express App Setup
**File**: `backend/src/routes/index.js`
```javascript
const conversationRoutes = require("./conversationRoutes");
router.use("/conversations", conversationRoutes);
```

### Environment Configuration
**Python**: Uses `settings.EXPRESS_BACKEND_URL` (default: `http://localhost:5000`)
**Express**: No additional config needed, uses existing MongoDB connection

---

## 4. Database Prerequisites

### MongoDB Collections Needed
1. `bookings` - Existing, now has `bookingId` field added
2. `conversations` - NEW, auto-created on first save() call

### MongoDB Indexes to Create (Optional but Recommended)
```javascript
// In MongoDB shell:
db.conversations.createIndex({ userId: 1 })
db.conversations.createIndex({ userId: 1, createdAt: -1 })
db.bookings.createIndex({ bookingId: 1 })
```

---

## 5. Testing Workflow

### Test 1: Booking ID Generation
```
1. User creates booking via chat
2. Check MongoDB: Should have bookingId field like "BKG-USER-ABC123"
3. Check email: Should display booking ID prominently
```

### Test 2: Conversation Persistence
```
1. User connects and chats: "I want to book a room"
2. User logs out
3. User logs back in
4. Agent should load previous history
5. Agent can reference previous conversation: "You were looking for a room earlier..."
```

### Test 3: Reschedule with Booking ID
```
1. User provides previous booking ID: "I want to reschedule BKG-PATHUM-69D61FE"
2. Agent looks up booking by bookingId
3. Agent proceeds with reschedule using retrieved booking
4. New booking might get new ID: BKG-PATHUM-XYZ789
```

---

## 6. Files Created/Modified

### Created (New Files)
- `backend/src/models/Conversation.js` - MongoDB schema
- `backend/src/services/conversationService.js` - Backend service
- `backend/src/routers/conversationRoutes.js` - Express routes
- `backend/src/validators/conversationSchemas.js` - Zod validation
- `backend/src/utils/bookingIdGenerator.js` - ID generation utility
- `agent/services/conversation_storage.py` - Python HTTP client

### Modified
- `backend/src/models/Booking.js` - Added `bookingId` field
- `backend/src/controllers/bookingController.js` - Generate ID after booking
- `backend/src/utils/emailService.js` - Include booking ID in emails
- `backend/src/routes/index.js` - Mount conversation routes
- `agent/agents/booking_agent.py` - Load/save conversation history
- `agent/services/conversation_storage.py` - Updated settings reference

---

## 7. Error Handling & Safety

### Non-Breaking Design
- Conversation save failures don't crash chat (logged as warning)
- Missing history loads gracefully with empty history (new session)
- Booking ID generation has fallback: If `bookingId` missing, use `_id`

### Security
- Conversation retrieval checks `userId` matches JWT token
- Admin endpoints require admin role
- No CSRF/XSS vulnerabilities in code
- Sensitive data (user emails) handled safely

---

## 8. Future Enhancements

### Possible Next Steps
1. **Conversation Analytics**: Query dashboard showing user interaction patterns
2. **Conversation Export**: Allow users to download chat history as PDF/JSON
3. **Conversation Search**: Full-text search within user's conversation history
4. **Auto-Delete Old Conversations**: TTL index on MongoDB documents (30 days)
5. **Conversation Tagging**: Tag conversations by topic/issue for better tracking
6. **Agent Improvement**: Use conversation patterns to improve system prompt

---

## 9. Deployment Checklist

- [ ] MongoDB collections created (or auto-created on first use)
- [ ] Express app has conversation routes mounted
- [ ] Python agent can reach backend at EXPRESS_BACKEND_URL
- [ ] Email service has new template sections
- [ ] Tests pass for booking ID generation
- [ ] Tests pass for conversation save/load
- [ ] Frontend WebSocket uses correct URL (`/api/chat/ws`)
- [ ] JWT token includes userId field
- [ ] Database backups configured

---

## 10. Quick Reference: Booking ID Format

| Component | Source | Example |
|-----------|--------|---------|
| Prefix | Fixed | `BKG` |
| Email Part | Email before @ (first 10 chars) | `PATHUM` |
| ID Part | MongoDB ObjectId (first 7 chars, uppercase) | `69D61FE` |
| **Final Format** | Combined | **BKG-PATHUM-69D61FE** |

---

## Summary

✅ **Booking ID System**: Customers now receive memorable booking IDs like BKG-PATHUM-69D61FE  
✅ **Email Confirmation**: Booking ID prominently displayed in confirmation and reschedule emails  
✅ **Conversation Persistence**: Chat history automatically saved to MongoDB  
✅ **Session Memory**: When users log back in, agent remembers previous conversations  
✅ **Non-Breaking**: System gracefully handles failures and edge cases  

**Result**: Complete conversation memory + user-friendly booking references across sessions!
