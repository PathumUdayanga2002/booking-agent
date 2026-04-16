const Booking = require("../models/Booking");
const Room = require("../models/Room");
const { AppError } = require("../utils/errors");
const { buildOverlapQuery } = require("../utils/bookingMath");

async function createRoom(req, res) {
  const room = await Room.create(req.body);
  res.status(201).json({
    success: true,
    room,
  });
}

async function listRooms(req, res) {
  const { checkIn, checkOut, guests, facilities } = req.query;

  const filters = { isActive: true };
  if (guests) {
    filters.capacity = { $gte: Number(guests) };
  }

  if (facilities) {
    const facilityList = facilities
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    if (facilityList.length > 0) {
      filters.facilities = { $all: facilityList };
    }
  }

  const rooms = await Room.find(filters).sort({ createdAt: -1 });

  const checkInDate = checkIn ? new Date(checkIn) : null;
  const checkOutDate = checkOut ? new Date(checkOut) : null;

  const withAvailability = await Promise.all(
    rooms.map(async (room) => {
      if (!checkInDate || !checkOutDate) {
        return {
          ...room.toObject(),
          availableUnits: room.totalUnits,
        };
      }

      const overlappingBookingsCount = await Booking.countDocuments({
        roomId: room._id,
        ...buildOverlapQuery(checkInDate, checkOutDate),
      });

      return {
        ...room.toObject(),
        availableUnits: Math.max(room.totalUnits - overlappingBookingsCount, 0),
      };
    })
  );

  res.json({
    success: true,
    rooms: withAvailability,
  });
}

async function getRoomById(req, res) {
  const { id } = req.params;
  const { checkIn, checkOut } = req.query;

  const room = await Room.findById(id);
  if (!room || !room.isActive) {
    throw new AppError("Room not found", 404);
  }

  let availableUnits = room.totalUnits;

  if (checkIn && checkOut) {
    const overlappingBookingsCount = await Booking.countDocuments({
      roomId: room._id,
      ...buildOverlapQuery(new Date(checkIn), new Date(checkOut)),
    });

    availableUnits = Math.max(room.totalUnits - overlappingBookingsCount, 0);
  }

  res.json({
    success: true,
    room: {
      ...room.toObject(),
      availableUnits,
    },
  });
}

module.exports = {
  createRoom,
  listRooms,
  getRoomById,
};
