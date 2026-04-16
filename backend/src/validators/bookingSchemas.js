const { z } = require("zod");

// Custom validator for dates in YYYY-MM-DD format
const dateString = z.string().refine(
  (val) => {
    // Accept YYYY-MM-DD format or ISO datetime format
    const dateRegex = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?$/;
    return dateRegex.test(val);
  },
  { message: "Date must be in YYYY-MM-DD format or ISO 8601 datetime format" }
);

const createBookingSchema = z.object({
  roomId: z.string().min(8),
  checkIn: dateString,
  checkOut: dateString,
  guests: z.number().int().min(1).max(20),
  guestName: z.string().min(2).max(120),
  guestEmail: z.string().email(),
  guestPhone: z.string().min(7).max(20),
});

const rescheduleBookingSchema = z.object({
  checkIn: dateString,
  checkOut: dateString,
  guests: z.number().int().min(1).max(20).optional(),
  guestName: z.string().min(2).max(120).optional(),
  guestEmail: z.string().email().optional(),
  guestPhone: z.string().min(7).max(20).optional(),
});

const adminStatsQuerySchema = z.object({
  checkIn: dateString.optional(),
  checkOut: dateString.optional(),
});

module.exports = {
  createBookingSchema,
  rescheduleBookingSchema,
  adminStatsQuerySchema,
};
