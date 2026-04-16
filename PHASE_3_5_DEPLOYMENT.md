# Phase 3.5 Implementation Guide

## Quick Start: Deploying Conversation History & Booking ID Features

### Prerequisites
- MongoDB is running and connected
- Express backend (port 5000) is running
- Python agent (port 8000) is running
- Frontend (port 3000) is running

---

## Implementation Steps

### Step 1: MongoDB Setup (1 minute)

The MongoDB collections will be automatically created on first use. However, to optimize queries, create these indexes:

```javascript
// Connect to MongoDB and run in mongo shell:
use hotel_booking

// Index for fast conversation lookup
db.conversations.createIndex({ userId: 1 })
db.conversations.createIndex({ userId: 1, createdAt: -1 })

// Index for fast booking ID lookup
db.bookings.createIndex({ bookingId: 1 })

// Verify indexes created
db.conversations.getIndexes()
db.bookings.getIndexes()
```

### Step 2: Express Backend Setup (5 minutes)

**Status**: ✅ Already done in code

Files created:
- ✅ `backend/src/models/Conversation.js`
- ✅ `backend/src/services/conversationService.js`
- ✅ `backend/src/routers/conversationRoutes.js`
- ✅ `backend/src/validators/conversationSchemas.js`
- ✅ `backend/src/utils/bookingIdGenerator.js`

Routes mounted:
- ✅ `backend/src/routes/index.js` - Added conversation routes

**Action**: No additional setup needed - just restart Express server

```bash
cd backend
npm install  # If new packages needed
npm start
```

### Step 3: Python Agent Setup (5 minutes)

**Status**: ✅ Already done in code

Files created:
- ✅ `agent/services/conversation_storage.py`

Files updated:
- ✅ `agent/agents/booking_agent.py` - Added storage integration

**Action**: Verify Python dependencies and restart agent

```bash
cd agent
pip install httpx  # If not already installed

# Verify imports work
python -c "from services.conversation_storage import get_storage_service; print('✓ OK')"

# Restart agent
python main.py
```

### Step 4: Verify Backend Configuration (1 minute)

Check that Express backend URL is correctly configured in Python:

```bash
# In agent/.env (or environment), verify EXPRESS_BACKEND_URL:
EXPRESS_BACKEND_URL=http://localhost:5000

# If not set, Express will be at: http://localhost:5000
```

### Step 5: Test Booking ID Generation (5 minutes)

1. **Start all services**: Express (5000), Python agent (8000), Frontend (3000)

2. **Create a test booking**:
   - Open http://localhost:3000/chat
   - Chat: "Book me a room for tomorrow"
   - Complete the booking flow

3. **Verify in MongoDB**:
   ```javascript
   use hotel_booking
   db.bookings.findOne({ }, { bookingId: 1, guestEmail: 1 })
   
   // Expected output:
   // { _id: ObjectId(...), bookingId: "BKG-TESTUSER-ABC1234", guestEmail: "test@..." }
   ```

4. **Verify in Email**:
   - Check email received
   - Should show: "Your Booking ID: BKG-TESTUSER-ABC1234"

### Step 6: Test Conversation History (5 minutes)

1. **Open the chat**: http://localhost:3000/chat

2. **Start a conversation**:
   - Message 1: "Hi, I need to book a room"
   - Message 2: "For 3 guests"
   - Message 3: "Next weekend"

3. **Verify in MongoDB**:
   ```javascript
   use hotel_booking
   db.conversations.find({ userId: <your_user_id> }, { role: 1, content: 1 }).pretty()
   
   // Should show messages alternating user/assistant
   ```

4. **Close browser completely** (log out or close tab)

5. **Reopen chat**: http://localhost:3000/chat (may need to log in again)

6. **Verify agent remembers**:
   - Agent should show previous conversation context
   - Message should reference: "I see you were booking a room for 3 guests next weekend..."

---

## Testing Checklist

### Booking ID Tests
- [ ] New booking gets bookingId in format `BKG-{PREFIX}-{ID}`
- [ ] bookingId is unique per booking
- [ ] Email shows booking ID prominently
- [ ] Reschedule email also shows booking ID
- [ ] MongoDB query by bookingId returns correct booking

### Conversation History Tests
- [ ] User messages saved to MongoDB with role="user"
- [ ] Agent messages saved to MongoDB with role="assistant"
- [ ] History loads on agent initialization
- [ ] Conversation persists across login/logout
- [ ] Limit parameter works (get last N messages)
- [ ] Delete conversation history works (clearing old data)

### Error Handling Tests
- [ ] If backend unreachable, chat still works (non-blocking)
- [ ] If MongoDB fails, chat still works
- [ ] Missing bookingId field doesn't crash booking
- [ ] Empty conversation history loads gracefully

---

## Troubleshooting

### Issue: "bookingId is undefined" in emails

**Solution**: Restart Express backend
```bash
# Kill existing process and restart
npm start
```

### Issue: Conversations not saving

**Check 1**: Verify backend is running
```bash
curl http://localhost:5000/health
# Should return: { "success": true, "message": "..." }
```

**Check 2**: Check Python logs for HTTP errors
```
Look for: "✗ Error saving message" or "✗ Timeout"
```

**Check 3**: Verify EXPRESS_BACKEND_URL in Python
```
Should be: http://localhost:5000 (must match your setup)
```

### Issue: Agent not loading previous conversations

**Check 1**: Verify conversations in MongoDB
```javascript
db.conversations.count()  // Should be > 0
db.conversations.findOne()  // See what's stored
```

**Check 2**: Check Python logs for "Loaded X previous messages"
```
Should show: ✓ Loaded 5 previous messages for user
```

**Check 3**: Verify userId in JWT token
```
Agent gets userId from JWT. Make sure it matches what's in MongoDB
```

---

## Feature Activation Confirmation

Once deployed, verify these endpoints work:

### Express Endpoints
```bash
# Save message
curl -X POST http://localhost:5000/api/conversations/save \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","role":"user","content":"Hello"}'

# Get history
curl http://localhost:5000/api/conversations/history/test

# Clear history
curl -X DELETE http://localhost:5000/api/conversations/history/test
```

### MongoDB Collections
```javascript
// Check collections exist
show collections
// Should show: conversations, bookings, rooms, users, etc.

// Check data
db.conversations.count()  // Should be > 0 after chats
db.bookings.findOne({ }, { bookingId: 1 })  // Should show bookingId
```

---

## Performance Notes

### Expected System Behavior
- **Booking ID Generation**: < 5ms (local string manipulation)
- **Conversation Save**: 50-100ms (HTTP + MongoDB write)
- **Conversation Load**: 50-100ms (HTTP + MongoDB query for 50 messages)
- **Email Generation**: 100-200ms (template rendering + SMTP send)

### Database Growth
- ~1KB per conversation message (including metadata)
- 100 daily users with 5 daily messages each = ~500KB/day
- 1 year = ~180MB for conversations (acceptable)

### Optimization Tips
1. Set conversation history limit to 30-50 (fewer messages loaded)
2. Create MongoDB compound index: `{ userId: 1, createdAt: -1 }`
3. Archive old conversations after 90 days (optional)
4. Cache recent conversations in memory (advanced)

---

## Monitoring & Logging

### What to Monitor
1. **Booking ID Generation**: Log shows: `✓ Booking created with ID: BKG-...`
2. **Conversation Save**: Log shows: `✓ Message saved for user`
3. **Conversation Load**: Log shows: `✓ Loaded N previous messages for user`

### Logs Location
```
Express: stdout/stderr or log files
Python: stdout/stderr or {VSCODE_TARGET_SESSION_LOG}
```

### Sample Log Output
```
✓ Agent initialized for user: 12345
✓ Loaded 5 previous messages for user: 12345
✓ Message saved for user 12345 (user)
✓ Message saved for user 12345 (assistant)
✓ Booking created with ID: BKG-PATHUM-69D61FE
```

---

## Rollback Plan

If issues occur, here's how to rollback:

### Option 1: Disable Conversation Saving (Keep Booking IDs)
```python
# In agent/agents/booking_agent.py, comment out:
# await self.storage_service.save_message(...)

# Chat will work, but won't persist conversations
# Booking IDs still generated and shown
```

### Option 2: Disable Booking IDs (Keep Conversations)
```javascript
// In backend/src/controllers/bookingController.js, comment out:
// const bookingId = generateBookingId(...);
// booking.bookingId = bookingId;

// Bookings will use just MongoDB _id
// Conversations will still save
```

### Option 3: Disable Both
```
Remove conversation routes from index.js
Stop saving bookingId in bookingController.js
System reverts to previous state
```

---

## Success Criteria

✅ All tests pass:
- Booking receives unique bookingId
- Email displays bookingId
- Conversations save to MongoDB
- Agent loads history on reconnect
- System handles errors gracefully

✅ No breaking changes:
- Existing bookings still work
- Existing chat still works
- No database migrations needed
- No new dependencies required (httpx may need `pip install`)

---

## Next Steps After Implementation

1. **Monitor Production**: Watch logs for first day
2. **Get User Feedback**: Ask users if they see booking IDs and persistence
3. **Optimize Queries**: If slow, add more indexes
4. **Archive Old Data**: Set up automatic cleanup of old conversations
5. **Integrate Reschedule**: Update reschedule flow to accept booking IDs

---

## Support & Questions

For issues, check:
1. MongoDB connection string is correct
2. Express backend is accessible from Python agent
3. JWT token includes userId field
4. MongoDB collections are created (auto-created on first use)
5. All new files are present in correct directories

**End of Implementation Guide**
