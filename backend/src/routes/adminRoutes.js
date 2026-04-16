const express = require("express");
const { asyncHandler } = require("../utils/asyncHandler");
const { requireAuth, requireRole } = require("../middleware/auth");
const { validateQuery } = require("../middleware/validate");
const { adminStatsQuerySchema } = require("../validators/bookingSchemas");
const { getDashboardStats } = require("../controllers/adminController");

const router = express.Router();

router.get(
  "/dashboard",
  requireAuth,
  requireRole("admin"),
  validateQuery(adminStatsQuerySchema),
  asyncHandler(getDashboardStats)
);

module.exports = router;
