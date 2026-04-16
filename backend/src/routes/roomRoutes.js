const express = require("express");
const { asyncHandler } = require("../utils/asyncHandler");
const { validateBody, validateQuery } = require("../middleware/validate");
const { requireAuth, requireRole } = require("../middleware/auth");
const { createRoomSchema, listRoomsQuerySchema } = require("../validators/roomSchemas");
const { createRoom, listRooms, getRoomById } = require("../controllers/roomController");

const router = express.Router();

// Search route - MUST come before /:id route
router.get("/search", validateQuery(listRoomsQuerySchema), asyncHandler(listRooms));

// List all rooms route
router.get("/", validateQuery(listRoomsQuerySchema), asyncHandler(listRooms));

// Get room by ID
router.get("/:id", asyncHandler(getRoomById));
router.post(
  "/",
  requireAuth,
  requireRole("admin"),
  validateBody(createRoomSchema),
  asyncHandler(createRoom)
);

module.exports = router;
