# Phase 2.5: Action Items & Next Steps

## 🎯 Immediate Actions (Next 5 Minutes)

### Step 1: Verify All Services Running ✅

```bash
# Terminal 1: Check Express backend
cd backend
npm start
# Expected: "listening on port 5000"

# Terminal 2: Check FastAPI backend
cd agent
python main.py
# Expected: "Uvicorn running on http://0.0.0.0:8000"
#          "✓ All services initialized successfully"

# Terminal 3: Start Next.js frontend
cd frontend
npm run dev
# Expected: "▲ Next.js 16.2.1 ready in X.XXs"
#          "Local: http://localhost:3000"
```

### Step 2: Test Basic Connectivity

```bash
# In new terminal, verify services respond:
curl http://localhost:3000          # Frontend
curl http://localhost:5000/api/rooms  # Express
curl http://localhost:8000/health    # FastAPI

# Should all return without timeout errors
```

### Step 3: Quick UI Check (2 minutes)

1. Open browser: http://localhost:3000
2. Login with:
   - Email: `user@test.com`
   - Password: `password123`
3. In header, verify:
   - ✅ "💬 Chat" link appears
   - ✅ "My Bookings" link appears
4. Click "💬 Chat"
5. If chat page loads with blue header → **Step 4**

---

## 🧪 Phase 2.5 Smoke Test (10 Minutes)

### Run through all 5 key scenarios:

#### Scenario 1: Chat Loads ✅
```
Action: Navigate to /chat
Expected: 
  - Blue header "Aurevia Booking Assistant"
  - Green dot "Connected"
  - Input field with placeholder
  - Empty message area
Result: ✅ PASS / ❌ FAIL
```

#### Scenario 2: Send Message ✅
```
Action: Type "Hello" and send
Expected:
  - Your message appears blue on right
  - AI responds with greeting
  - Typing indicator appears (3 dots)
Result: ✅ PASS / ❌ FAIL
```

#### Scenario 3: Room Search ✅
```
Action: Type "I want to book a room for April 5-10"
Expected:
  - AI shows available rooms
  - Shows names and prices
  - Shows tool usage indicator
Result: ✅ PASS / ❌ FAIL
```

#### Scenario 4: Admin Knowledge Base ✅
```
Action: 
  1. Logout
  2. Login as admin (admin@test.com / adminpassword)
  3. Click "📚 Knowledge Base"
Expected:
  - Page loads at /admin/knowledge
  - Shows upload area
  - Shows documents table
  - See "Knowledge Base Management" title
Result: ✅ PASS / ❌ FAIL
```

#### Scenario 5: Upload Document ✅
```
Action:
  1. Create test file: hotel_info.txt
  2. Add content:
     "SUITE AMENITIES: WiFi, AC, Jacuzzi, Mini bar"
  3. Drag file to upload area
Expected:
  - Upload progress bar appears
  - File appears in table
  - Status shows "✓ Stored"
Result: ✅ PASS / ❌ FAIL
```

**If all 5 pass: Phase 2.5 is working! 🎉**

---

## 📋 Complete Testing Workflow (30 Minutes)

If smoke test passed, run full tests:

### Part A: User Chat Flow (10 min)

1. **Setup:** Login as user
2. **Test:**
   ```
   User: "Show me deluxe rooms"
   Expected: AI returns deluxe rooms filtered
   
   User: "Book the deluxe room for April 5-10"
   Expected: AI asks to confirm
   
   User: "Yes"
   Expected: Booking created, confirmation shown
   ```
3. **Verify:** Check booking appears in My Bookings

### Part B: Knowledge Base Flow (10 min)

1. **Setup:** Login as admin, go to /admin/knowledge
2. **Upload:** Create `faq.txt`:
   ```
   Q: What time is checkout?
   A: Checkout is at 11 AM
   
   Q: Is WiFi free?
   A: Yes, complimentary WiFi
   ```
3. **Test:** In chat, ask:
   ```
   User: "When is checkout?"
   Expected: AI says "Checkout is at 11 AM" (from document)
   
   User: "Is WiFi included?"
   Expected: AI says "Yes, complimentary WiFi"
   ```

### Part C: Error Handling (5 min)

1. **Test WebSocket Disconnect:**
   - Open DevTools → Network → Offline
   - Try to send message
   - Expected: "Connection error" message shown
   - Turn online
   - Expected: Auto-reconnects, "Connected" returns

2. **Test Admin-Only Access:**
   - Logout, login as regular user
   - Try to access: `localhost:3000/admin/knowledge`
   - Expected: Redirected or 403 error

3. **Test File Validation:**
   - Try uploading .jpg file
   - Expected: Error "Only PDF and TXT files"

---

## 🔧 Troubleshooting Decision Tree

```
Issue: Chat page shows "Connecting..."
├─ Check: Is FastAPI running?
│  └─ No: Run `python main.py` in agent folder
├─ Check: Is port 8000 accessible?
│  └─ Run: netstat -an | grep 8000
├─ Check: NEXT_PUBLIC_AGENT_WS_URL
│  └─ Should be: ws://localhost:8000/chat/ws
└─ Check: Browser console for errors

Issue: "please log in to use chat"
├─ You're not logged in
└─ Go to /login first

Issue: Upload fails
├─ Check: File > 10MB?
│  └─ Reduce file size
├─ Check: .pdf or .txt?
│  └─ Use PDF or TXT only
├─ Check: Admin user?
│  └─ Admin-only feature
└─ Check: JWT token valid?
    └─ Login again

Issue: AI doesn't respond
├─ Check: WebSocket connected (green dot)?
├─ Check: FastAPI logs for errors
├─ Check: GROQ_API_KEY valid?
└─ Check: Groq quota exceeded?
```

---

## 📊 Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Chat connect | <200ms | WebSocket handshake |
| Send message | <500ms | Network latency |
| AI response | 2-10s | Depends on Groq API |
| Upload file | <30s | 1-10MB files |
| Document process | 2-5s | Per page |
| Knowledge search | <100ms | Qdrant vector DB |

**If slower: Check internet connection, Groq rate limits**

---

## 🐛 Debug Commands

### Browser Console (F12)

```javascript
// Check local auth
localStorage.getItem('auth_token')

// Check WebSocket status
// Network tab → filter "WS" → look for ws://localhost:8000

// Check API responses
// Network tab → look for xhr requests
```

### Backend Logs

```bash
# FastAPI logs (should show):
# "User {userId} connected"
# "Message received: ..."
# "Using tool: search_rooms"

# Express logs (should show):
# POST /api/bookings
# GET /api/rooms?...
```

### Database Inspection

```bash
# MongoDB - Check conversations saved
mongo hotel_booking
db.conversations.findOne()
db.hotel_knowledge.findOne()

# Qdrant - Check vectors stored
curl http://localhost:6333/health
```

---

## 🚨 Red Flags (Stop Here if You See These)

❌ **Red Flag 1:** Chat shows "Please log in" after login
- Check: localStorage has auth_token
- Fix: Clear cookies, login again

❌ **Red Flag 2:** WebSocket "Connecting..." forever
- Check: FastAPI running? `ps aux | grep python`
- Check: Port 8000 open? `lsof -i :8000`
- Fix: Restart FastAPI

❌ **Red Flag 3:** Upload button disabled after selecting file
- Check: Are you logged in as admin?
- Check: Browser console for errors
- Fix: Clear browser cache, reload

❌ **Red Flag 4:** AI responds "I'm not able to help with that"
- Check: Is Express backend running?
- Check: Can FastAPI see Express? Check agent logs
- Fix: Restart both backends

❌ **Red Flag 5:** "CORS error" in console
- Check: Is frontend running on :3000?
- Check: Are agents URLs in NEXT_PUBLIC_ env?
- Fix: Check .env.local configuration

---

## ✨ Success Checklist

When Phase 2.5 is working, check all:

- [ ] Chat page loads at /localhost:3000/chat
- [ ] WebSocket connection shows green "Connected"
- [ ] Can send messages (blue bubble appears)
- [ ] AI responds (gray bubble appears)
- [ ] Typing indicator shows while AI processing
- [ ] Knowledge Base page loads at /localhost:3000/admin/knowledge
- [ ] Can upload PDF/TXT files
- [ ] Uploaded docs show in table with "✓ Stored"
- [ ] Can delete documents
- [ ] AI answers from knowledge base
- [ ] Bookings persist in My Bookings
- [ ] Admin RBAC enforced (non-admins can't access KB)
- [ ] Error messages are user-friendly
- [ ] WebSocket auto-reconnects on disconnect
- [ ] No errors in browser console

**If all checked: Phase 2.5 ✅ COMPLETE**

---

## 📅 Optional: Load Testing (Advanced)

If you want to test at scale:

```bash
# Use Apache Bench to test Express backend
ab -n 100 -c 10 http://localhost:5000/api/rooms

# Use WebSocket stress test (node script)
# Connect 10 users, each sending 50 messages
# Expected: System handles gracefully

# Document upload stress
# Upload 20 large PDFs simultaneously
# Expected: Queue processes them
```

---

## 🎯 Next Steps After Testing

**If all tests pass:**
1. ✅ Phase 2.5 is production ready
2. ✅ Can deploy frontend to Vercel
3. ✅ Can deploy backends to VPS/Cloud
4. ✅ Ready for Phase 3 (Analytics) or launch

**If some tests fail:**
1. Use troubleshooting tree above
2. Check backend logs
3. Review PHASE_2_5_INTEGRATION.md
4. Review error handling section

**If everything works:**
1. 🎉 Your AI booking platform is live!
2. Users can book via chat
3. Admins can train AI with documents
4. Knowledge base fully functional

---

## 📞 Quick Command Reference

```bash
# Start everything in sequence
cd frontend && npm run dev  # In Terminal 3
cd backend && npm start     # In Terminal 1
cd agent && python main.py  # In Terminal 2

# Test everything is up
curl http://localhost:3000
curl http://localhost:5000/api/rooms
curl http://localhost:8000/health

# View logs
# Terminal 1: Express logs
# Terminal 2: FastAPI logs
# Terminal 3: Next.js logs
# Browser: DevTools (F12) for frontend logs

# Quick check - all green?
# ✅ http://localhost:3000 loads
# ✅ http://localhost:5000 responds
# ✅ http://localhost:8000 responds
# ✅ Chat page shows connected
→ PHASE 2.5 READY! 🚀
```

---

## ⏱️ Timeline

**Ideally:**
- 5 min: Verify services running
- 10 min: Smoke test 5 scenarios
- 15 min: Run full test workflow
- 5 min: Troubleshoot (if needed)
- **Total: 35-40 minutes**

**Actual may vary based on:**
- Network speed
- Groq API latency
- Internet connection
- System resources

---

## 🎓 Educational Value

**What you learned:**
- ✅ WebSocket real-time communication
- ✅ File upload with drag-drop
- ✅ React hooks and state management
- ✅ TypeScript in production
- ✅ Error recovery & resilience
- ✅ RBAC (Role-Based Access Control)
- ✅ Microservices integration
- ✅ Vector databases for search

**You can now:**
- Build chat applications
- Integrate WebSockets anywhere
- Implement knowledge bases
- Handle file uploads
- Design error recovery
- Apply TypeScript rigorously
- Build multi-tier architectures

---

## 📞 Support

**If stuck:**
1. Check `QUICK_REFERENCE.md`
2. See `PHASE_2_5_TESTING.md` section "Troubleshooting"
3. Review logs in all 3 terminals
4. Check `ARCHITECTURE_DIAGRAM.md` for flows
5. Review `PHASE_2_5_INTEGRATION.md`

**Common Fixes:**
- "Connecting...": Restart FastAPI on port 8000
- Upload fails: Check if you're admin
- No response: Check Groq API key
- CORS error: Check .env.local has NEXT_PUBLIC_

---

## 🏁 Final Notes

### What Should Happen

User clicks "💬 Chat"
  ↓
WebSocket connects (green dot)
  ↓
User types: "Book me a room"
  ↓
AI responds with options in <10 seconds
  ↓
User selects room
  ↓
Booking confirmed
  ↓
Appears in My Bookings
  ↓
Email confirmation sent

### If This Works

Your system is **PRODUCTION READY** 🚀

---

**Phase 2.5 Testing Checklist: Complete ✨**

Ready to deploy? See deployment section in README_PHASE_2_5.md

**Good luck! 🎉**
