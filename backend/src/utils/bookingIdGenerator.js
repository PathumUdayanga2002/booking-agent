/**
 * Generate human-readable booking ID from guest email and MongoDB ObjectId
 * Format: BKG-EMAIL_PREFIX-MONGOID_PREFIX
 * Example: BKG-PATHUM-69D61FE
 */

function generateBookingId(guestEmail, mongoId) {
  if (!guestEmail || !mongoId) {
    throw new Error("guestEmail and mongoId are required");
  }

  // Extract first name/part from email (before @)
  const emailName = guestEmail.split("@")[0].toUpperCase();
  
  // Get first part of email name (if longer than 10 chars, truncate)
  const emailPrefix = emailName.substring(0, 10);

  // Get first 7 characters of MongoDB ObjectId
  const mongoIdPrefix = mongoId.toString().substring(0, 7).toUpperCase();

  // Format: BKG-EMAILPREFIX-MONGOIDPREFIX
  const bookingId = `BKG-${emailPrefix}-${mongoIdPrefix}`;

  return bookingId;
}

module.exports = {
  generateBookingId,
};
