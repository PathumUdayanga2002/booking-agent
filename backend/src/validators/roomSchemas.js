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

const createRoomSchema = z.object({
  name: z.string().min(2).max(120),
  description: z.string().min(10).max(600),
  pricePerNight: z.number().positive(),
  capacity: z.number().int().min(1).max(20),
  totalUnits: z.number().int().min(1).max(200),
  facilities: z.array(z.string().min(2).max(60)).max(25).default([]),
});

const listRoomsQuerySchema = z.object({
  checkIn: dateString.optional(),
  checkOut: dateString.optional(),
  guests: z.coerce.number().int().min(1).max(20).optional(),
  facilities: z.string().optional(),
});

module.exports = {
  createRoomSchema,
  listRoomsQuerySchema,
};
