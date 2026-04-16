function calculateNights(checkIn, checkOut) {
  const msInDay = 24 * 60 * 60 * 1000;
  const diff = checkOut.getTime() - checkIn.getTime();
  return Math.ceil(diff / msInDay);
}

function buildOverlapQuery(checkIn, checkOut) {
  return {
    checkIn: { $lt: checkOut },
    checkOut: { $gt: checkIn },
    status: "confirmed", // Only count confirmed bookings; cancelled bookings release availability
  };
}

module.exports = {
  calculateNights,
  buildOverlapQuery,
};
