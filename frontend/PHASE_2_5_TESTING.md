# Phase 2.5 Testing Guide

Complete end-to-end testing for frontend chat and knowledge base integration.

## Prerequisites

✅ Backend services running:
```bash
# Terminal 1: Express backend
cd backend
npm start
# Should see: "Server running on port 5000"

# Terminal 2: FastAPI agent backend
cd agent
python main.py
# Should see: "✓ All services initialized successfully"
# Then: "Uvicorn running on http://0.0.0.0:8000"
```

✅ Frontend running:
```bash
# Terminal 3: Next.js frontend
cd frontend
npm run dev
# Should see: "▲ Next.js 16.2.1"
# Navigate to: http://localhost:3000
```

## Test Case 1: User Authentication & Chat Access

**Steps:**
1. Navigate to http://localhost:3000
2. Click "Login"
3. Use test credentials:
   - Email: user@test.com
   - Password: password123
4. After login, verify:
   - ✅ "💬 Chat" link appears in header
   - ✅ "My Bookings" link present
   - ✅ User name displayed (top-right)

**Expected Result:** Logged in successfully, can see personal links

---

## Test Case 2: Chat Page Navigation

**Steps:**
1. Click "💬 Chat" in header
2. Verify page loads at http://localhost:3000/chat
3. Check UI elements:
   - ✅ Chat header with "Aurevia Booking Assistant"
   - ✅ Connection status (green dot = connected)
   - ✅ Message area (empty initially)
   - ✅ Input field with placeholder text
   - ✅ Send button

**Expected Result:** Chat page fully loaded with all UI elements

---

## Test Case 3: WebSocket Connection

**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab → filter "WS"
3. Check current chat page
4. Verify in console: `WebSocket connected`
5. Look for WS connection to `ws://localhost:8000/chat/ws/{userId}`

**Expected Result:** WebSocket connection established, status = "Connected" (green)

---

## Test Case 4: Simple Chat Message

**Steps:**
1. In chat, type: `"Hello"`
2. Click Send (or press Enter)
3. Verify:
   - ✅ Message appears on right (blue bubble)
   - ✅ Message has timestamp
   - ✅ Typing indicator appears (3 bouncing dots)
   - ✅ Agent responds with greeting

**Sample Response:**
```
"Hello! 👋 I'm Aurevia, your booking assistant. 
How can I help you find the perfect room today?"
```

**Expected Result:** Bidirectional message exchange working

---

## Test Case 5: Room Search via Chat

**Steps:**
1. In chat, clear and type:
   ```
   "I want to book a room for April 5-10 for 2 people"
   ```
2. Press Send
3. Verify:
   - ✅ Typing indicator appears
   - ✅ Agent calls `search_rooms_by_requirements` (check tool usage)
   - ✅ Agent responds with 2-3 available rooms
   - ✅ Shows room names + prices
   - ✅ Response includes dates confirmation

**Sample Response:**
```
"Great! I found these rooms available for April 5-10:

1. Deluxe Room - $150/night (Total: $900 for 6 nights)
2. Suite - $200/night (Total: $1,200 for 6 nights)
3. Standard Room - $100/night (Total: $600 for 6 nights)

Which one would you like to book?"
```

**Expected Result:** AI searches rooms and displays options

---

## Test Case 6: Full Booking Flow

**Steps:**
1. Continue chat from Test 5
2. Type: `"I want the Suite"`
3. Agent should ask for confirmation
4. Type: `"Yes, confirm booking"`
5. Verify:
   - ✅ Agent calls `create_booking` tool
   - ✅ Response confirms booking created
   - ✅ Provides booking reference number
   - ✅ Suggests checking email for confirmation

**Sample Response:**
```
"Perfect! I've created your booking:

📋 Booking Reference: BOOK-123456
🏠 Room: Suite
📅 Check-in: April 5, 2026
📅 Check-out: April 10, 2026
👥 Guests: 2 people
💰 Total: $1,200
✉️ Confirmation has been sent to your email

You can view this booking in 'My Bookings' anytime!"
```

**Expected Result:** Complete end-to-end booking via chat

---

## Test Case 7: Check Booking in My Bookings

**Steps:**
1. After booking, click "My Bookings" in header
2. Verify:
   - ✅ Your new booking appears in table
   - ✅ Correct dates (April 5-10)
   - ✅ Correct room (Suite)
   - ✅ Status = "confirmed"
   - ✅ Reschedule button available

**Expected Result:** Booking persisted to database and visible

---

## Test Case 8: Admin Authentication

**Steps:**
1. Logout (current user)
2. Login with admin account:
   - Email: admin@test.com
   - Password: adminpassword
3. Verify in header:
   - ✅ "Admin" link appears
   - ✅ "📚 Knowledge Base" link appears

**Expected Result:** Admin user has special links

---

## Test Case 9: Knowledge Base Admin Page

**Steps:**
1. Click "📚 Knowledge Base" in header
2. Verify page loads at http://localhost:3000/admin/knowledge
3. Check UI elements:
   - ✅ Page title: "Knowledge Base Management"
   - ✅ Description text
   - ✅ Drag-and-drop upload area
   - ✅ Upload info (supports PDF, TXT, max 10MB)
   - ✅ Documents table (likely empty first time)

**Expected Result:** Knowledge base manager page loaded

---

## Test Case 10: Document Upload via Drag-Drop

**Prepare:**
1. Create a test file: `hotel_info.txt`:
```
AUREVIA HOTEL - ROOM DESCRIPTIONS

STANDARD ROOM
- Size: 25 sqm
- Bed: Queen size
- Amenities: WiFi, AC, TV, Private bathroom
- Price: $100/night
- Capacity: 2 people

DELUXE ROOM
- Size: 40 sqm
- Bed: King size or Twin beds
- Amenities: WiFi, AC, TV, Mini bar, Balcony
- Price: $150/night
- Capacity: 2-3 people

SUITE
- Size: 60 sqm
- Bed: King size
- Amenities: WiFi, AC, TV, Mini bar, Jacuzzi, Lounge
- Price: $200/night
- Capacity: 2-4 people

CANCELLATION POLICY
- Free cancellation up to 48 hours before check-in
- 1 night charge for cancellations 24-48 hours before
- Full charge for cancellations less than 24 hours before

CHECKOUT TIME
- Standard checkout: 11:00 AM
- Late checkout (2 PM): +$50
- Late checkout (5 PM): +$100
```

**Steps:**
1. Drag `hotel_info.txt` to upload area
2. Verify:
   - ✅ Upload progress bar appears
   - ✅ Progress increases to 100%
   - ✅ Success message: "Document uploaded successfully"
   - ✅ Document appears in table

**Expected Result:** Document uploaded and visible

---

## Test Case 11: Document Processing Verification

**Steps:**
1. In documents table, check the uploaded document:
   - ✅ Filename: `hotel_info.txt`
   - ✅ Type: `TXT`
   - ✅ Chunks: Should be 5-10 (depending on chunking)
   - ✅ Status: `✓ Stored` (green)
   - ✅ Upload time shown

**Expected Result:** Document processed and stored in vector DB

---

## Test Case 12: Knowledge Search in Chat

**Setup:** Uploaded document from Test 10

**Steps:**
1. Go back to Chat (/chat)
2. Login as regular user (or stay logged in if you are)
3. Type questions referencing the uploaded document:
   ```
   "What amenities does the suite have?"
   ```
4. Verify:
   - ✅ Typing indicator appears
   - ✅ Agent calls `search_knowledge_base` tool
   - ✅ Response includes information from document:
     ```
     "The Suite includes these amenities:
     - WiFi
     - AC
     - TV
     - Mini bar
     - Jacuzzi
     - Lounge area"
     ```

**Test Additional Questions:**
- "What's your cancellation policy?"
- "What time is checkout?"
- "What's included in the Deluxe room?"

**Expected Result:** Agent retrieves info from knowledge base

---

## Test Case 13: Document Update

**Steps:**
1. Update `hotel_info.txt` with new information
2. Go to Knowledge Base (/admin/knowledge)
3. Upload the same file again
4. Verify:
   - ✅ New document appears in table (separate entry)
   - ✅ Both documents show as "Stored"
5. Ask in chat: "What's new?" (if you added new info)
6. Verify: Agent includes updated info

**Expected Result:** Can replace/update knowledge base

---

## Test Case 14: Document Deletion

**Steps:**
1. Go to Knowledge Base (/admin/knowledge)
2. Click "Delete" next to a document
3. Confirm deletion in browser dialog
4. Verify:
   - ✅ Document disappears from table
   - ✅ Success message shown
   - ✅ Document no longer searchable (ask again in chat)

**Expected Result:** Document and its chunks removed

---

## Test Case 15: Error Handling - WebSocket Disconnect

**Steps:**
1. In Chat page, open DevTools Network tab
2. Throttle connection: "Offline" mode
3. Try to send a message
4. Verify:
   - ✅ Input disabled
   - ✅ Status shows "Connecting..." (red)
   - ✅ Error message: "Connection error - Attempting to reconnect"
4. Go back to "Online"
5. Verify:
   - ✅ Auto-reconnect happens
   - ✅ Status returns to "Connected" (green)
   - ✅ Can send messages again

**Expected Result:** Graceful offline handling with reconnect

---

## Test Case 16: Error Handling - Invalid File Upload

**Steps:**
1. Go to Knowledge Base (/admin/knowledge)
2. Try to upload:
   - File A: `.jpg` image (wrong type)
   - Verify: Error "Only PDF and TXT files are supported"
   - File B: Large file > 10MB
   - Verify: Error "File size must be less than 10MB"

**Expected Result:** Validation works, friendly errors

---

## Test Case 17: Error Handling - Non-Admin Access

**Steps:**
1. Login as regular user
2. Try to access: http://localhost:3000/admin/knowledge
3. Verify:
   - ✅ Redirected to home page
   - ✅ See message "no admin" or 403 forbidden

**Expected Result:** RBAC working, non-admins blocked

---

## Test Case 18: Multiple Users in Chat

**Setup:** Two browser windows/tabs or private windows

**Steps:**
1. Window 1: Login as user1, go to chat, send message
2. Window 2: Login as different user2, go to chat
3. Verify:
   - ✅ Each user has separate conversation
   - ✅ user1's messages don't appear in user2's chat
   - ✅ user2 can send messages independently

**Expected Result:** Per-user chat sessions working

---

## Test Case 19: Chat Message Persistence

**Steps:**
1. In chat, send several messages
2. Refresh page (F5)
3. Verify:
   - ✅ WebSocket reconnects automatically
   - ✅ Previous messages load in chat (from MongoDB)
   - ✅ New messages work

**Expected Result:** Conversation history persisted

---

## Test Case 20: Chat with Tool Usage Display

**Steps:**
1. Send booking message: "Book me a room please"
2. In chat message bubble, look for tool indication
3. Verify:
   - ✅ Message shows: "🔧 Used: search_rooms_by_requirements"
   - ✅ Expands to show tool input/output (if visible)

**Expected Result:** Tool usage tracking visible

---

## Performance Tests

### Test 21: Rapid Messages
- Send 10 messages in quick succession
- Expected: All handled correctly (respect rate limits)
- Timeout: Messages should arrive within 30s each

### Test 22: Large Conversation
- Chat for 30+ messages
- Expected: No UI lag, messages still append correctly

### Test 23: Large Document Upload
- Upload 5MB+ PDF
- Expected: Progress bar shows, upload completes in <30s

---

## Debugging Tips

If tests fail, check:

**For WebSocket issues:**
```bash
# Terminal: Check backend logs
cd agent
# Look for: "User {userId} connected"
# Look for: "Message received: {content}"
```

**For upload issues:**
```bash
# Terminal: Check agent backend
# Look for: "Processing file: {filename}"
# Look for: "Stored {chunks} chunks"
```

**Browser Console (F12):**
- Click Network tab
- Filter by "WS" for WebSocket messages
- Filter by "admin/documents" for upload requests

**Check MongoDB:**
```bash
# See conversations collection
mongo hotel_booking
db.conversations.find()

# See documents collection
db.hotel_knowledge.find()
```

---

## Success Criteria - Phase 2.5 Complete ✅

All tests should pass:
- ✅ Chat page loads and connects
- ✅ Messages send/receive bidirectionally
- ✅ Full booking flow works
- ✅ Knowledge base upload works
- ✅ Knowledge base searches work
- ✅ Admin RBAC enforced
- ✅ Error handling graceful
- ✅ Multi-user sessions isolated
- ✅ Conversation history persists
- ✅ Tool usage visible

**When all pass: Phase 2.5 is PRODUCTION READY** 🚀
