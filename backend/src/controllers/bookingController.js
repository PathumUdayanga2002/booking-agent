const Booking = require("../models/Booking");
const Room = require("../models/Room");
const { calculateNights, buildOverlapQuery } = require("../utils/bookingMath");
const { generateBookingId } = require("../utils/bookingIdGenerator");
const { AppError } = require("../utils/errors");
const { sendBookingConfirmationEmail, sendRescheduleConfirmationEmail } = require("../utils/emailService");
const { info, error: logError } = require("../utils/logger");

async function createBooking(req, res) {
  const {
    roomId,
    checkIn,
    checkOut,
    guests,
    guestName,
    guestEmail,
    guestPhone,
  } = req.body;

  const room = await Room.findById(roomId);
  if (!room || !room.isActive) {
    throw new AppError("Room is not available", 404);
  }

  if (guests > room.capacity) {
    throw new AppError("Guest count exceeds room capacity", 400);
  }

  const checkInDate = new Date(checkIn);
  const checkOutDate = new Date(checkOut);
  const nights = calculateNights(checkInDate, checkOutDate);

  if (nights <= 0) {
    throw new AppError("Check-out date must be after check-in date", 400);
  }

  const overlappingBookingsCount = await Booking.countDocuments({
    roomId,
    ...buildOverlapQuery(checkInDate, checkOutDate),
  });

  if (overlappingBookingsCount >= room.totalUnits) {
    throw new AppError("No room unit available for selected dates", 409);
  }

  const totalAmount = nights * room.pricePerNight;

  const booking = await Booking.create({
    userId: req.user._id,
    roomId,
    roomNameSnapshot: room.name,
    checkIn: checkInDate,
    checkOut: checkOutDate,
    nights,
    guests,
    guestName,
    guestEmail: guestEmail.toLowerCase(),
    guestPhone,
    totalAmount,
    status: "confirmed",
  });

  // Generate and update booking ID
  const bookingId = generateBookingId(guestEmail, booking._id);
  booking.bookingId = bookingId;
  await booking.save();
  
  info(`✓ Booking created with ID: ${bookingId}`);

  // Send confirmation email asynchronously (don't wait for it)
  sendBookingConfirmationEmail(booking, room).catch((emailError) => {
    logError("Failed to send confirmation email", { bookingId, error: emailError.message });
  });

  res.status(201).json({
    success: true,
    booking,
    billing: {
      nights,
      pricePerNight: room.pricePerNight,
      totalAmount,
      currency: "USD",
      paymentMode: "pay-at-property",
    },
  });
}

async function listMyBookings(req, res) {
  const bookings = await Booking.find({ userId: req.user._id })
    .sort({ createdAt: -1 })
    .populate("roomId", "name facilities pricePerNight");

  res.json({
    success: true,
    bookings,
  });
}

async function getBookingStatus(req, res) {
  const { bookingId } = req.params;

  // Resolve booking by public booking ID (BKG-*) or MongoDB _id.
  const booking = bookingId.startsWith("BKG-")
    ? await Booking.findOne({ bookingId }).populate("roomId", "name facilities pricePerNight totalUnits")
    : await Booking.findById(bookingId).populate("roomId", "name facilities pricePerNight totalUnits");

  if (!booking) {
    throw new AppError("Booking not found", 404);
  }

  // Ensure user owns this booking (or is admin).
  if (booking.userId.toString() !== req.user._id.toString() && req.user.role !== "admin") {
    throw new AppError("Unauthorized: You can only view your own bookings", 403);
  }

  res.json({
    success: true,
    booking,
  });
}

async function rescheduleBooking(req, res) {
  const { checkIn, checkOut, guests, guestName, guestEmail, guestPhone } = req.body;
  const { bookingId } = req.params;

  // Find booking by public booking ID (BKG-*) or MongoDB _id.
  const booking = bookingId.startsWith("BKG-")
    ? await Booking.findOne({ bookingId }).populate("roomId")
    : await Booking.findById(bookingId).populate("roomId");
  if (!booking) {
    throw new AppError("Booking not found", 404);
  }

  // Ensure user owns this booking
  if (booking.userId.toString() !== req.user._id.toString()) {
    throw new AppError("Unauthorized: You can only reschedule your own bookings", 403);
  }

  // Cannot reschedule cancelled bookings
  if (booking.status === "cancelled") {
    throw new AppError("Cannot reschedule a cancelled booking", 400);
  }

  const checkInDate = new Date(checkIn);
  const checkOutDate = new Date(checkOut);
  const nights = calculateNights(checkInDate, checkOutDate);

  if (nights <= 0) {
    throw new AppError("Check-out date must be after check-in date", 400);
  }

  const updatedGuests = guests ?? booking.guests;
  if (updatedGuests > booking.roomId.capacity) {
    throw new AppError("Guest count exceeds room capacity", 400);
  }

  // Check for overlaps with OTHER bookings (exclude current booking)
  const overlappingBookingsCount = await Booking.countDocuments({
    roomId: booking.roomId._id,
    _id: { $ne: booking._id }, // Exclude current booking
    ...buildOverlapQuery(checkInDate, checkOutDate),
  });

  if (overlappingBookingsCount >= booking.roomId.totalUnits) {
    throw new AppError(
      "The room is not available for the selected dates. Please choose different dates.",
      409
    );
  }

  // Update booking
  const totalAmount = nights * booking.roomId.pricePerNight;
  const oldCheckIn = booking.checkIn;
  const oldCheckOut = booking.checkOut;
  
  booking.checkIn = checkInDate;
  booking.checkOut = checkOutDate;
  booking.nights = nights;
  booking.guests = updatedGuests;
  if (guestName) {
    booking.guestName = guestName;
  }
  if (guestEmail) {
    booking.guestEmail = guestEmail.toLowerCase();
  }
  if (guestPhone) {
    booking.guestPhone = guestPhone;
  }
  booking.totalAmount = totalAmount;
  await booking.save();

  // Send reschedule confirmation email asynchronously (don't wait for it)
  sendRescheduleConfirmationEmail(booking, booking.roomId, oldCheckIn, oldCheckOut).catch((emailError) => {
    logError("Failed to send reschedule email", { bookingId: booking._id, error: emailError.message });
  });

  res.json({
    success: true,
    booking,
    billing: {
      nights,
      pricePerNight: booking.roomId.pricePerNight,
      totalAmount,
      currency: "USD",
      paymentMode: "pay-at-property",
    },
  });
}

async function adminListBookings(req, res) {
  const bookings = await Booking.find({})
    .sort({ checkIn: 1 })
    .limit(100)
    .populate("roomId", "name")
    .populate("userId", "name email role");

  res.json({
    success: true,
    bookings,
  });
}

async function cancelBooking(req, res) {
  const { bookingId } = req.params;
  const { reason } = req.body;

  info(`\n=== CANCEL BOOKING ENDPOINT CALLED ===`);
  info(`📍 BookingId param: ${bookingId}`);
  info(`📍 Reason: ${reason}`);
  info(`📍 User ID: ${req.user._id}`);
  info(`📍 User Role: ${req.user.role}`);

  // Find the booking by MongoDB ID or booking ID format (BKG-*)
  let booking;
  if (bookingId.startsWith("BKG-")) {
    // Search by booking ID format
    info(`🔍 Searching by booking ID format: ${bookingId}`);
    booking = await Booking.findOne({ bookingId: bookingId }).populate("roomId");
    info(`🔍 Search result: ${booking ? "Found" : "Not found"}`);
  } else {
    // Search by MongoDB _id
    info(`🔍 Searching by MongoDB _id: ${bookingId}`);
    booking = await Booking.findById(bookingId).populate("roomId");
    info(`🔍 Search result: ${booking ? "Found" : "Not found"}`);
  }
  
  if (!booking) {
    info(`❌ Booking not found`);
    throw new AppError("Booking not found", 404);
  }

  info(`✓ Found booking: ${booking.bookingId || booking._id}`);
  info(`  Status before: ${booking.status}`);
  info(`  Room: ${booking.roomNameSnapshot}`);

  // Ensure user owns this booking (or is admin)
  if (booking.userId.toString() !== req.user._id.toString() && req.user.role !== "admin") {
    info(`❌ Authorization failed: booking owner ${booking.userId} != user ${req.user._id}`);
    throw new AppError("Unauthorized: You can only cancel your own bookings", 403);
  }

  // Cannot cancel already cancelled bookings
  if (booking.status === "cancelled") {
    info(`❌ Booking already cancelled`);
    throw new AppError("This booking is already cancelled", 400);
  }

  // Update booking status to cancelled
  booking.status = "cancelled";
  booking.cancellationReason = reason || "User requested cancellation";
  booking.cancelledAt = new Date();
  
  try {
    const savedBooking = await booking.save();
    info(`✓ Booking saved to database successfully`);
    info(`  Saved ID: ${savedBooking._id}`);
    info(`  Status after save: ${savedBooking.status}`);
    info(`  Cancellation reason: ${savedBooking.cancellationReason}`);
    
    // Verify by re-fetching from database
    const verifyBooking = await Booking.findById(savedBooking._id);
    info(`✓ Verification - Status in DB: ${verifyBooking.status}`);
    
    if (verifyBooking.status !== "cancelled") {
      info(`⚠️ WARNING: Status mismatch! Expected "cancelled" but got "${verifyBooking.status}"`);
    }
    
    info(`✓ Booking cancelled: ${savedBooking.bookingId || savedBooking._id}`);
    info(`=== CANCEL BOOKING ENDPOINT COMPLETED ===\n`);

    res.json({
      success: true,
      message: "Booking cancelled successfully",
      booking: {
        id: savedBooking._id,
        bookingId: savedBooking.bookingId,
        status: savedBooking.status,
        cancellationReason: savedBooking.cancellationReason,
        cancelledAt: savedBooking.cancelledAt,
      },
    });
  } catch (saveError) {
    info(`✗ ERROR saving booking: ${saveError.message}`);
    info(`✗ ERROR stack: ${saveError.stack}`);
    info(`=== CANCEL BOOKING ENDPOINT FAILED ===\n`);
    throw new AppError(`Failed to save cancellation: ${saveError.message}`, 500);
  }
}

module.exports = {
  createBooking,
  getBookingStatus,
  listMyBookings,
  rescheduleBooking,
  adminListBookings,
  cancelBooking,
};
