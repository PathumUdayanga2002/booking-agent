const Booking = require("../models/Booking");
const Room = require("../models/Room");
const { buildOverlapQuery } = require("../utils/bookingMath");

async function getDashboardStats(req, res) {
  const startDate = req.query.checkIn ? new Date(req.query.checkIn) : new Date();
  const defaultEndDate = new Date(startDate.getTime() + 24 * 60 * 60 * 1000);
  const endDate = req.query.checkOut ? new Date(req.query.checkOut) : defaultEndDate;

  const [totalBookings, rooms, latestBookings] = await Promise.all([
    Booking.countDocuments({ status: "confirmed" }),
    Room.find({ isActive: true }),
    Booking.find({ status: "confirmed" })
      .sort({ checkIn: 1 })
      .limit(12)
      .populate("roomId", "name")
      .populate("userId", "name email"),
  ]);

  const roomAvailability = await Promise.all(
    rooms.map(async (room) => {
      const overlappingBookingsCount = await Booking.countDocuments({
        roomId: room._id,
        ...buildOverlapQuery(startDate, endDate),
      });

      return {
        roomId: room._id,
        roomName: room.name,
        totalUnits: room.totalUnits,
        bookedUnits: overlappingBookingsCount,
        availableUnits: Math.max(room.totalUnits - overlappingBookingsCount, 0),
        checkIn: startDate,
        checkOut: endDate,
      };
    })
  );

  const totalRoomUnits = roomAvailability.reduce((sum, item) => sum + item.totalUnits, 0);
  const bookedUnits = roomAvailability.reduce((sum, item) => sum + item.bookedUnits, 0);

  res.json({
    success: true,
    stats: {
      totalBookings,
      totalRooms: rooms.length,
      totalRoomUnits,
      bookedUnits,
      availableUnits: Math.max(totalRoomUnits - bookedUnits, 0),
      range: {
        checkIn: startDate,
        checkOut: endDate,
      },
    },
    roomAvailability,
    latestBookings,
  });
}

module.exports = {
  getDashboardStats,
};
