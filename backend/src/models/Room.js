const mongoose = require("mongoose");

const roomSchema = new mongoose.Schema(
  {
    name: { type: String, required: true, trim: true },
    description: { type: String, required: true, trim: true },
    pricePerNight: { type: Number, required: true, min: 1 },
    capacity: { type: Number, required: true, min: 1 },
    totalUnits: { type: Number, required: true, min: 1 },
    facilities: { type: [String], default: [] },
    isActive: { type: Boolean, default: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Room", roomSchema);
