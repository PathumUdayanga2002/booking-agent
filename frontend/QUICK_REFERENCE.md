# Phase 2.5 Quick Reference Card

## 🚀 30-Second Setup

```bash
# Terminal 1
cd backend && npm start

# Terminal 2  
cd agent && python main.py

# Terminal 3
cd frontend && npm run dev

# Browser
http://localhost:3000
```

## 🧪 5-Minute Test

### Test 1: User Chat (2 min)
1. Login at http://localhost:3000/login
2. Click "💬 Chat" button
3. Type: `"I want to book a room for April 5-10"`
4. AI responds with room options ✅

### Test 2: Admin Knowledge (3 min)
1. Logout, login as admin
2. Click "📚 Knowledge Base"
3. Create `hotel_info.txt`:
   ```
   SUITE AMENITIES:
   - WiFi, AC, TV
   - Mini bar, Jacuzzi
   - Lounge area
   ```
4. Drag file to upload area
5. Wait for "Stored" status ✅
6. Go to Chat, ask: "What amenities does the suite have?" ✅

## 📋 Page URLs

| Feature | URL | User |
|---------|-----|------|
| Chat | /chat | Any logged-in |
| Knowledge Base | /admin/knowledge | Admin only |
| My Bookings | /my-bookings | Any logged-in |
| Home | / | All |
| Login | /login | Not logged-in |

## 🎮 Chat Commands to Try

```
"I want to book a room"
→ Shows available rooms

"Show me deluxe rooms"
→ Filters by room type

"What's your cancellation policy?"
→ Searches knowledge base

"Book me the suite"
→ Creates booking

"Check my bookings"
→ Lists user bookings

"Cancel my last booking"
→ Cancels most recent booking
```

## 📤 File Upload Format

**Example hotel_info.txt:**
```
ROOM TYPES & PRICES:
- Standard Room: $100/night
- Deluxe Room: $150/night  
- Suite: $200/night

AMENITIES:
- WiFi included
- AC in all rooms
- Daily housekeeping

POLICIES:
- Check-in: 3 PM
- Check-out: 11 AM
- Cancellation: 48 hours free
```

**Supported:** PDF, TXT (max 10MB)

## 🔍 Verify Everything Works

```bash
# Express backend
curl http://localhost:5000/api/rooms

# FastAPI backend
curl http://localhost:8000/health

# Frontend  
curl http://localhost:3000

# MongoDB
mongo hotel_booking
db.conversations.count()  # Should show chats

# Qdrant (if curious)
curl http://localhost:6333/health
```

## 🐛 Debug Mode

### Check Backend Logs
```bash
# Look for web socket connections
# Terminal 2 output should show:
# "User {userId} connected"
# "Message received: {content}"
```

### Browser Console (F12)
```javascript
// Check WebSocket
console.log("Messages in localStorage:", 
  localStorage.getItem('auth_token'))

// Monitor network
// F12 → Network → Filter "WS" or "admin/documents"
```

### MongoDB Inspection
```bash
mongo hotel_booking
db.conversations.findOne()
db.hotel_knowledge.findOne()
db.knowledge_chunks.find().limit(3)
```

## 🚨 Common Issues

| Issue | Fix |
|-------|-----|
| Chat says "Connecting..." | Is FastAPI running? Check port 8000 |
| Upload fails silently | File > 10MB? Or not PDF/TXT? |
| "Please log in" | Login first at /login |
| Admin links missing | User must have role="admin" |
| Messages don't appear | Browser's localhost cookie settings |
| Slow chat responses | Check Groq API quota in `.env` |

## ✅ Success Indicators

✅ Green checkmark line in chat header = Connected
✅ Message appears as blue bubble on right = User message sent
✅ Message appears as gray bubble on left = AI responded
✅ "Stored" badge in Knowledge Base = Document processed
✅ No red error messages = All systems go

## 📊 Expected Timings

| Action | Time |
|--------|------|
| Chat connect | <200ms |
| Send message | <500ms |
| AI response | 2-10s (depends on Groq) |
| Doc upload | <30s (depends on size) |
| Doc processing | 2-5s per page |
| Knowledge search | <100ms |

## 🎯 Full End-to-End Flow

```
1. User → /chat
2. "I want suite April 5-10"  
3. AI → search_rooms (calls Express)
4. Express → MongoDB (checks availability)
5. Express → Returns 3 rooms
6. AI → "Which room?" (shows options)
7. User → "Suite"
8. AI → create_booking (calls Express)
9. Express → MongoDB (creates record)
10. Express → Returns booking ID
11. AI → "Booking confirmed!" 
12. User → /my-bookings (sees new booking)
```

## 🎓 Code Locations

| Feature | File |
|---------|------|
| Chat UI | `components/ChatBox.tsx` |
| Chat Page | `app/chat/page.tsx` |
| Upload UI | `app/admin/knowledge/page.tsx` |
| API calls | `lib/api.ts` |
| Types | `lib/types.ts` |
| Navigation | `components/Header.tsx` |

## 🔧 Environment Variables

**Must match between backends:**
```
JWT_SECRET_KEY=same-in-both  ← CRITICAL
```

**Front-end (.env.local):**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000/api
NEXT_PUBLIC_AGENT_API_BASE_URL=http://localhost:8000/api  
NEXT_PUBLIC_AGENT_WS_URL=ws://localhost:8000/chat/ws
```

## 📱 Responsive?

✅ ChatBox works on mobile
✅ Knowledge Base manager responsive
✅ Drag-drop works on touch (mostly)
✅ All fonts readable on small screens

## 🎯 Next: What to Test First

**Priority 1 (Critical):**
- [ ] Chat page loads
- [ ] WebSocket connects (green dot)
- [ ] Send/receive messages work

**Priority 2 (Core Features):**
- [ ] Full booking flow works
- [ ] Admin knowledge upload works
- [ ] Knowledge search works in chat

**Priority 3 (Polish):**
- [ ] Error messages are helpful
- [ ] Disconnection auto-reconnects
- [ ] No CORS errors
- [ ] Mobile-friendly

## 📞 Quick Diagnostics

```bash
# Is FastAPI responding?
curl http://localhost:8000/health

# Can Express be reached?
curl http://localhost:5000/api/rooms

# JWT token working?
# Browser console: localStorage.getItem('auth_token')

# Qdrant accessible?
curl -X GET http://localhost:6333/health

# MongoDB connected?
# Check agent backend logs
```

## 🎉 When Everything Works

You'll see:
1. ✅ Chat loads without errors
2. ✅ First message receives AI response
3. ✅ Knowledge documents upload successfully
4. ✅ AI answers from uploaded documents
5. ✅ Bookings persist in My Bookings

**Then Phase 2.5 is COMPLETE! 🚀**

---

## Cheat Sheet: Admin Test Account

```
Email: admin@test.com
Password: adminpassword
Role: admin
Access: All routes + knowledge base
```

## Cheat Sheet: User Test Account

```
Email: user@test.com  
Password: password123
Role: user
Access: Chat + My Bookings + Home
```

---

**Phase 2.5 = Chat UI + Knowledge Base ✨**
