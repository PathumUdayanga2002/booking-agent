const express = require("express");
const authRoutes = require("./authRoutes");
const roomRoutes = require("./roomRoutes");
const bookingRoutes = require("./bookingRoutes");
const adminRoutes = require("./adminRoutes");
const conversationRoutes = require("../routers/conversationRoutes");

const router = express.Router();

router.use("/auth", authRoutes);
router.use("/rooms", roomRoutes);
router.use("/bookings", bookingRoutes);
router.use("/admin", adminRoutes);
router.use("/conversations", conversationRoutes);

module.exports = router;
