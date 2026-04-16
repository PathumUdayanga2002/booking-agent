const express = require("express");
const { asyncHandler } = require("../utils/asyncHandler");
const { validateBody } = require("../middleware/validate");
const { requireAuth, requireRole } = require("../middleware/auth");
const { createBookingSchema, rescheduleBookingSchema } = require("../validators/bookingSchemas");
const {
  createBooking,
  getBookingStatus,
  listMyBookings,
  rescheduleBooking,
  adminListBookings,
  cancelBooking,
} = require("../controllers/bookingController");

const router = express.Router();

router.post(
  "/",
  requireAuth,
  requireRole("user", "admin"),
  validateBody(createBookingSchema),
  asyncHandler(createBooking)
);
router.get("/me", requireAuth, requireRole("user", "admin"), asyncHandler(listMyBookings));
router.get("/admin/all", requireAuth, requireRole("admin"), asyncHandler(adminListBookings));
router.get("/:bookingId", requireAuth, requireRole("user", "admin"), asyncHandler(getBookingStatus));
router.put(
  "/:bookingId",
  requireAuth,
  requireRole("user", "admin"),
  validateBody(rescheduleBookingSchema),
  asyncHandler(rescheduleBooking)
);
router.delete(
  "/:bookingId",
  requireAuth,
  requireRole("user", "admin"),
  asyncHandler(cancelBooking)
);

module.exports = router;
