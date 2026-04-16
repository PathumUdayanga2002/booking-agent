# Reschedule Flow with Booking ID Integration

## Current State

User can reschedule by:
- Providing new dates
- System finds booking by existing booking reference

## Next Enhancement: Reschedule by Booking ID

Enable users to reschedule by providing their booking ID (e.g., "Reschedule BKG-PATHUM-69D61FE")

---

## Implementation Steps

### Step 1: Update Reschedule Tool Description

**File**: `agent/agents/tools.py`

**Current**:
```python
reschedule_booking_description = "Reschedule an existing booking to new dates"
```

**Updated**:
```python
reschedule_booking_description = """Reschedule an existing booking to new dates.
You can identify the booking by:
1. Booking ID (format: BKG-PATHUM-69D61FE, e.g., 'reschedule BKG-PATHUM-69D61FE')
2. Guest's room details (if booking ID not provided)

Once booking is identified, ask for new check-in and check-out dates."""
```

### Step 2: Update Python Express Client

**File**: `agent/services/express_api.py`

Add method to lookup booking by ID:

```python
async def get_booking_by_id(self, booking_id: str) -> Dict:
    """Look up booking by booking ID (human-readable reference).
    
    Args:
        booking_id: Booking ID in format BKG-PATHUM-69D61FE
        
    Returns:
        Booking details if found
    """
    try:
        response = await self.client.get(
            f"/bookings/by-id/{booking_id}",
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            booking = result.get("data", {})
            logger.info(f"✓ Found booking {booking_id}: {booking.get('roomName')}")
            return booking
        else:
            logger.warning(f"✗ Booking not found: {booking_id}")
            return None
            
    except Exception as e:
        logger.error(f"✗ Error looking up booking: {e}")
        return None
```

### Step 3: Create Express Endpoint for Booking Lookup

**File**: `backend/src/controllers/bookingController.js`

Add new function:

```javascript
/**
 * Get booking by booking ID (human-readable reference)
 * GET /api/bookings/by-id/:bookingId
 */
async getBookingByBookingId(req, res) {
  try {
    const { bookingId } = req.params;

    // Find booking by bookingId
    const booking = await Booking.findOne({ bookingId })
      .populate('roomId')
      .exec();

    if (!booking) {
      return res.status(404).json({
        success: false,
        message: `Booking not found: ${bookingId}`
      });
    }

    // Don't expose if belongs to different user
    if (booking.guestEmail !== req.user.email && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        message: "Unauthorized to access this booking"
      });
    }

    res.json({
      success: true,
      data: {
        id: booking._id,
        bookingId: booking.bookingId,
        roomName: booking.roomId?.name,
        checkIn: booking.checkIn,
        checkOut: booking.checkOut,
        guests: booking.guests,
        totalAmount: booking.totalAmount
      }
    });
  } catch (error) {
    logger.error(`✗ Error retrieving booking by ID: ${error.message}`);
    res.status(500).json({
      success: false,
      message: "Failed to retrieve booking",
      error: error.message
    });
  }
}
```

### Step 4: Add Route to Booking Routes

**File**: `backend/src/routes/bookingRoutes.js`

Add before the `/:id` route (order matters!):

```javascript
// Route to get booking by booking ID MUST come before /:id wildcard
router.get("/by-id/:bookingId", authenticate, bookingController.getBookingByBookingId);
```

### Step 5: Update Agent Reschedule Tool

**File**: `agent/agents/tools.py`

Add new parameter to reschedule tool:

```python
class RescheduleBookingInput(BaseModel):
    """Input for rescheduling a booking."""
    booking_id: Optional[str] = None  # NEW: Booking ID (BKG-PATHUM-69D61FE)
    booking_reference: Optional[str] = None  # Keep old reference (fallback)
    check_in: Optional[str] = None  # New check-in date (YYYY-MM-DD)
    check_out: Optional[str] = None  # New check-out date (YYYY-MM-DD)
    reason: Optional[str] = None  # Reason for reschedule
```

### Step 6: Update System Prompt

**File**: `agent/agents/booking_agent.py`

Add to `_get_system_prompt()`:

```
When user mentions rescheduling with a booking ID:
1. Ask for confirmation: "Reschedule booking BKG-PATHUM-69D61FE?"
2. Look up booking using reschedule_booking tool with booking_id parameter
3. Show current dates: "Current: Check-in June 12, Check-out June 15"
4. Ask for new dates: "What new dates would you prefer?"
5. Proceed with reschedule

Example conversation:
User: "I need to reschedule my booking BKG-PATHUM-69D61FE"
Agent: "I found your booking for 3 guests. Current dates: June 12-15.
        What new dates would you prefer?"
User: "June 20-25 instead"
Agent: [Reschedule and confirm]
```

---

## User Experience Flow

### Before (Current)
```
User: "I want to reschedule my booking"
Agent: "What are your room details?"
User: "I forgot... can you look it up?"
```

### After (With Booking ID)
```
User: "I want to reschedule BKG-PATHUM-69D61FE"
Agent: "Perfect! I found your booking for 3 guests.
        Current dates: June 12-15, 2024.
        What new dates would you prefer?"
User: "June 20-25"
Agent: "✓ Rescheduled! Your booking is confirmed for June 20-25.
        Confirmation email sent to pathum@example.com"
```

---

## Testing Scenarios

### Test 1: Reschedule by Booking ID
```
1. Get a booking ID from previous booking (e.g., BKG-PATHUM-69D61FE)
2. Open chat and say: "Reschedule BKG-PATHUM-69D61FE"
3. Verify agent finds booking
4. Provide new dates
5. Check reschedule email has new booking ID
```

### Test 2: Invalid Booking ID
```
1. Say: "Reschedule BKG-INVALID-123456"
2. Agent should respond: "I couldn't find that booking ID.
   Could you provide your email or booking details?"
```

### Test 3: Multiple Bookings
```
1. Create 2 bookings under same email
2. Say: "Reschedule BKG-PATHUM-69D61FE"
3. Agent should find correct one (not other booking)
```

### Test 4: Fallback (No ID)
```
1. Say: "Reschedule my last booking"
2. Agent: "I need your booking ID or email to identify your booking"
```

---

## Implementation Checklist

- [ ] Update `tools.py` with `booking_id` parameter
- [ ] Update `express_api.py` with booking lookup method
- [ ] Create Express endpoint `GET /bookings/by-id/:bookingId`
- [ ] Add route to `bookingRoutes.js` (before `/:id`)
- [ ] Update system prompt with booking ID handling
- [ ] Test lookup with valid booking ID
- [ ] Test lookup with invalid booking ID
- [ ] Test email verification (reschedule email shows booking ID)
- [ ] Manual end-to-end test with real booking IDs

---

## Security Considerations

### Authorization
```javascript
// IMPORTANT: Only allow user to reschedule their own booking
if (booking.guestEmail !== req.user.email && req.user.role !== 'admin') {
  return res.status(403).json({ message: "Unauthorized" });
}
```

### Validation
- Booking ID format: `BKG-[A-Z0-9]+-[A-Z0-9]+`
- New dates must be in future
- New dates must respect hotel policies

---

## Database Query Performance

The lookup query:
```javascript
db.bookings.findOne({ bookingId: "BKG-PATHUM-69D61FE" })
```

**Performance**:
- With index: ~1ms
- Without index: ~50-100ms (full collection scan)

**Action**: Ensure index exists
```javascript
db.bookings.createIndex({ bookingId: 1 })
```

---

## Error Messages

**User-Friendly**:
- "I couldn't find booking BKG-PATHUM-69D61FE. Please check the ID."
- "Your booking is for June 12-15. What new dates work for you?"
- "I can only reschedule if you have availability for those dates."

**System Errors** (logged, not shown to user):
- HTTP 404: Booking not in database
- HTTP 403: User trying to reschedule someone else's booking
- HTTP 500: Database error

---

## Future Enhancements

1. **SMS Notification**: Send booking ID and reschedule confirmation via SMS
2. **Booking Link**: Generate unique link: `hotel.com/reschedule/BKG-PATHUM-69D61FE`
3. **Cancelation Support**: "Cancel booking BKG-PATHUM-69D61FE"
4. **Modification Support**: "Modify booking BKG-PATHUM-69D61FE (add guest)"
5. **Group Bookings**: Multiple booking IDs: "Reschedule BKG-A, BKG-B, BKG-C together"

---

## Integration with Email

**Enhancement**: In reschedule email, make booking ID clickable:

```html
<p>
  Booking ID: 
  <a href="http://hotel.com/reschedule/BKG-PATHUM-69D61FE">
    BKG-PATHUM-69D61FE
  </a>
</p>
<!-- When clicked, opens reschedule form with booking pre-filled -->
```

---

## Summary

This enhancement allows users to:
1. ✅ Reference bookings by memorable ID (BKG-PATHUM-69D61FE)
2. ✅ Reschedule by providing booking ID only
3. ✅ No need to remember room details or booking dates
4. ✅ Quick, seamless reschedule experience

**Estimated Implementation Time**: 30-45 minutes

---

**Next Phase**: Implement and test reschedule by booking ID
