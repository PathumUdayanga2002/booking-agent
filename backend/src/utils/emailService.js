const nodemailer = require("nodemailer");
const { info, warn, error: logError } = require("./logger");

const {
  SMTP_HOST,
  SMTP_PORT,
  SMTP_USER,
  SMTP_PASS,
  SMTP_FROM_EMAIL,
  SMTP_FROM_NAME,
} = process.env;

let transporter = null;

/**
 * Initialize email transporter
 */
function initializeEmailTransporter() {
  if (transporter) return transporter;

  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS) {
    warn("Email service disabled: Missing SMTP configuration in .env");
    return null;
  }

  try {
    transporter = nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT || 587,
      secure: SMTP_PORT == 465, // true for 465, false for other ports
      auth: {
        user: SMTP_USER,
        pass: SMTP_PASS,
      },
      connectionTimeout: 5000,
      socketTimeout: 5000,
      tls: {
        rejectUnauthorized: false,
      },
    });

    info("Email transporter created (non-blocking mode)", {
      host: SMTP_HOST,
      port: SMTP_PORT,
    });

    return transporter;
  } catch (error) {
    logError("Failed to initialize email transporter", { error: error.message });
    return null;
  }
}

/**
 * Send booking confirmation email
 */
async function sendBookingConfirmationEmail(booking, room) {
  const transport = initializeEmailTransporter();
  if (!transport) {
    warn("Email not sent: Email service not configured", {
      to: booking.guestEmail,
      bookingId: booking._id,
    });
    return false;
  }

  try {
   const mailOptions = {
  from: `${SMTP_FROM_NAME} <${SMTP_FROM_EMAIL}>`,
  to: booking.guestEmail,
  subject: `✨ Booking Confirmed - ${room.name} at Blue Island Beach Hotel ✨`,
  html: `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Georgia', 'Times New Roman', Times, serif; background-color: #f7f5f0;">
      <div style="max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
        
        <!-- Hero Section -->
        <div style="background: linear-gradient(135deg, #c4a27a 0%, #9b7b5c 100%); padding: 40px 30px; text-align: center;">
          <h1 style="color: #ffffff; margin: 0; font-size: 32px; letter-spacing: 1px; font-weight: 400;">BLUE ISLAND BEACH HOTEL</h1>
          <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Where Skies Meet Serenity</p>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 40px 35px;">
          <!-- Greeting -->
          <div style="margin-bottom: 30px;">
            <h2 style="color: #2c3e2f; font-size: 24px; margin: 0 0 8px 0; font-weight: 400;">Dear ${booking.guestName},</h2>
            <div style="width: 50px; height: 2px; background-color: #c4a27a; margin: 15px 0 20px 0;"></div>
            <p style="color: #5a5a5a; line-height: 1.6; margin: 0; font-size: 16px;">
              Thank you for choosing <strong style="color: #c4a27a;">Blue Island Beach Hotel</strong>. We are delighted to confirm your reservation and look forward to welcoming you.
            </p>
          </div>
          
          <!-- Booking Reference -->
          <div style="background: linear-gradient(135deg, #c4a27a 0%, #9b7b5c 100%); border-radius: 12px; padding: 20px; margin-bottom: 25px; text-align: center;">
            <p style="color: rgba(255,255,255,0.9); margin: 0 0 10px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Your Booking Reference</p>
            <p style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold; letter-spacing: 2px; font-family: 'Courier New', monospace;">${booking.bookingId || booking._id}</p>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0; font-size: 12px;">Save this ID for future reference and support inquiries</p>
          </div>
          
          <!-- Booking Details Card -->
          <div style="background: #faf9f7; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #e8e2d9;">
            <h3 style="color: #2c3e2f; margin: 0 0 20px 0; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
              <span style="font-size: 22px; margin-right: 8px;">📅</span> Reservation Details
            </h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px 0; color: #7a6a5a; font-weight: 500;">Room</td>
                <td style="padding: 8px 0; color: #2c3e2f; font-weight: 500;">${room.name}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #7a6a5a;">Check-in</td>
                <td style="padding: 8px 0; color: #2c3e2f;"><strong>${new Date(booking.checkIn).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</strong> • 3:00 PM</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #7a6a5a;">Check-out</td>
                <td style="padding: 8px 0; color: #2c3e2f;"><strong>${new Date(booking.checkOut).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</strong> • 12:00 PM</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #7a6a5a;">Nights</td>
                <td style="padding: 8px 0; color: #2c3e2f;">${booking.nights} ${booking.nights === 1 ? 'Night' : 'Nights'}</td>
              </tr>
              <tr>
                <td style="padding: 8px 0; color: #7a6a5a;">Guests</td>
                <td style="padding: 8px 0; color: #2c3e2f;">${booking.guests} ${booking.guests === 1 ? 'Guest' : 'Guests'}</td>
              </tr>
              <tr>
                <td style="padding: 15px 0 0 0; border-top: 1px solid #e8e2d9;"></td>
                <td style="padding: 15px 0 0 0; border-top: 1px solid #e8e2d9;"></td>
              </tr>
              <tr>
                <td style="padding: 10px 0 0 0; color: #7a6a5a; font-size: 18px;">Total Amount</td>
                <td style="padding: 10px 0 0 0; color: #c4a27a; font-size: 28px; font-weight: bold;">$${booking.totalAmount}</td>
              </tr>
            </table>
          </div>
          
          <!-- Payment Information -->
          <div style="background: #faf9f7; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #e8e2d9;">
            <h3 style="color: #2c3e2f; margin: 0 0 15px 0; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
              <span style="font-size: 22px; margin-right: 8px;">💳</span> Payment Information
            </h3>
            <p style="margin: 0 0 12px 0; color: #5a5a5a;">
              <strong style="color: #c4a27a;">Payment Mode:</strong> Pay at Property
            </p>
            <p style="margin: 0; color: #5a5a5a; line-height: 1.5;">
              You may settle your payment upon arrival. We accept all major credit cards, debit cards, and cash.
            </p>
          </div>
          
          <!-- Room Details -->
          <div style="background: #faf9f7; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #e8e2d9;">
            <h3 style="color: #2c3e2f; margin: 0 0 15px 0; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
              <span style="font-size: 22px; margin-right: 8px;">🛏️</span> Room Features
            </h3>
            <p style="margin: 0 0 12px 0; color: #5a5a5a;">
              <strong style="color: #c4a27a;">Capacity:</strong> Up to ${room.capacity} ${room.capacity === 1 ? 'Guest' : 'Guests'}
            </p>
            ${room.facilities && room.facilities.length > 0 ? `
              <p style="margin: 0 0 8px 0; color: #5a5a5a;"><strong style="color: #c4a27a;">Amenities:</strong></p>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                ${room.facilities.map(facility => `
                  <span style="background: #e8e2d9; color: #5a4a3a; padding: 4px 12px; border-radius: 20px; font-size: 13px;">${facility}</span>
                `).join('')}
              </div>
            ` : '<p style="margin: 0; color: #5a5a5a;">Contact us for detailed room amenities.</p>'}
          </div>
          
          <!-- Important Information -->
          <div style="background: #fef7e8; border-left: 3px solid #c4a27a; padding: 20px; margin: 30px 0; border-radius: 8px;">
            <p style="margin: 0 0 10px 0; color: #7a6a5a; font-size: 14px;">
              <strong>📍 Hotel Address:</strong><br>
              123 Luxury Avenue, Downtown City, Country
            </p>
            <p style="margin: 0 0 10px 0; color: #7a6a5a; font-size: 14px;">
              <strong>📞 Contact Us:</strong><br>
              +1 (555) 123-4567 | reservations@blueislandbeachhotel.com
            </p>
            <p style="margin: 0; color: #7a6a5a; font-size: 14px;">
              <strong>🕒 Front Desk:</strong><br>
              24/7 Service Available
            </p>
          </div>
          
          <!-- Modification Info -->
          <div style="margin: 25px 0; text-align: center; padding: 20px 0; border-top: 1px solid #e8e2d9; border-bottom: 1px solid #e8e2d9;">
            <p style="color: #7a6a5a; margin: 0; font-size: 14px;">
              To modify or cancel your reservation, please log in to your account at <a href="#" style="color: #c4a27a; text-decoration: none;">www.blueislandbeachhotel.com/mybookings</a>
            </p>
          </div>
          
          <!-- Signature -->
          <div style="margin-top: 35px;">
            <p style="color: #5a5a5a; margin: 0 0 5px 0;">With warmest regards,</p>
            <p style="color: #2c3e2f; margin: 0; font-size: 18px; font-weight: 500;">The Blue Island Beach Hotel Team</p>
            <p style="color: #9b9b9b; margin: 15px 0 0 0; font-size: 12px; line-height: 1.4;">
              ✨ Experience luxury, embrace comfort ✨
            </p>
          </div>
        </div>
        
        <!-- Footer -->
        <div style="background: #f7f5f0; padding: 20px 35px; text-align: center; border-top: 1px solid #e8e2d9;">
          <p style="color: #9b9b9b; margin: 0 0 8px 0; font-size: 12px;">
            This is a confirmation of your reservation. Please keep this email for your records.
          </p>
          <p style="color: #9b9b9b; margin: 0; font-size: 11px;">
            © 2024 Blue Island Beach Hotel. All rights reserved.
          </p>
          <p style="color: #9b9b9b; margin: 8px 0 0 0; font-size: 11px;">
            This is an automated message, please do not reply directly to this email.
          </p>
        </div>
      </div>
    </body>
    </html>
  `,
};

    // Add timeout to prevent hanging indefinitely
    await Promise.race([
      transport.sendMail(mailOptions),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Email send timeout (3s)")), 3000)
      )
    ]);

    info("Booking confirmation email sent successfully", {
      to: booking.guestEmail,
      bookingId: booking._id,
    });

    return true;
  } catch (error) {
    const errorDetails = {
      to: booking.guestEmail,
      bookingId: booking._id,
      errorMessage: error.message,
      errorCode: error.code,
      errorName: error.name,
    };
    // This is non-blocking/optional - log but don't break booking
    logError("Failed to send booking confirmation email (non-critical)", errorDetails);
    return false; // Silently fail without throwing
  }
}

/**
 * Send booking reschedule email
 */
async function sendRescheduleConfirmationEmail(booking, room, oldCheckIn, oldCheckOut) {
  const transport = initializeEmailTransporter();
  if (!transport) {
    warn("Email not sent: Email service not configured", {
      to: booking.guestEmail,
      bookingId: booking._id,
    });
    return false;
  }

  try {
   const mailOptions = {
  from: `${SMTP_FROM_NAME} <${SMTP_FROM_EMAIL}>`,
  to: booking.guestEmail,
  subject: `🔄 Booking Rescheduled - ${room.name} at Blue Island Beach Hotel`,
  html: `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Georgia', 'Times New Roman', Times, serif; background-color: #f7f5f0;">
      <div style="max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
        
        <!-- Hero Section -->
        <div style="background: linear-gradient(135deg, #c4a27a 0%, #9b7b5c 100%); padding: 40px 30px; text-align: center;">
          <h1 style="color: #ffffff; margin: 0; font-size: 32px; letter-spacing: 1px; font-weight: 400;">BLUE ISLAND BEACH HOTEL</h1>
          <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Where Skies Meet Serenity</p>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 40px 35px;">
          <!-- Greeting -->
          <div style="margin-bottom: 30px;">
            <h2 style="color: #2c3e2f; font-size: 24px; margin: 0 0 8px 0; font-weight: 400;">Dear ${booking.guestName},</h2>
            <div style="width: 50px; height: 2px; background-color: #c4a27a; margin: 15px 0 20px 0;"></div>
            <p style="color: #5a5a5a; line-height: 1.6; margin: 0; font-size: 16px;">
              Your booking has been successfully rescheduled. Below are the details of your updated reservation.
            </p>
          </div>
          
          <!-- Booking Reference -->
          <div style="background: linear-gradient(135deg, #c4a27a 0%, #9b7b5c 100%); border-radius: 12px; padding: 20px; margin-bottom: 25px; text-align: center;">
            <p style="color: rgba(255,255,255,0.9); margin: 0 0 10px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Your Booking Reference</p>
            <p style="color: #ffffff; margin: 0; font-size: 28px; font-weight: bold; letter-spacing: 2px; font-family: 'Courier New', monospace;">${booking.bookingId || booking._id}</p>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0; font-size: 12px;">Use this ID for all future correspondence and inquiries</p>
          </div>
          
          <!-- Date Comparison Cards -->
          <div style="display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap;">
            <!-- Previous Dates -->
            <div style="flex: 1; background: #fef7e8; border-radius: 12px; padding: 20px; border: 1px solid #f0e5d8;">
              <div style="text-align: center; margin-bottom: 15px;">
                <span style="font-size: 32px;">📅</span>
                <h3 style="color: #c4a27a; margin: 8px 0 0 0; font-size: 16px; font-weight: 600;">Previous Dates</h3>
              </div>
              <div style="background: #ffffff; border-radius: 8px; padding: 15px; text-align: center;">
                <p style="margin: 0 0 8px 0; color: #7a6a5a;">
                  <strong style="color: #c4a27a;">Check-in:</strong><br>
                  <span style="font-size: 14px; color: #5a5a5a;">${new Date(oldCheckIn).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
                </p>
                <p style="margin: 0; color: #7a6a5a;">
                  <strong style="color: #c4a27a;">Check-out:</strong><br>
                  <span style="font-size: 14px; color: #5a5a5a;">${new Date(oldCheckOut).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
                </p>
              </div>
            </div>
            
            <!-- Arrow Icon (visible on desktop) -->
            <div style="display: flex; align-items: center; font-size: 28px; color: #c4a27a;">
              <span style="display: inline-block;">→</span>
            </div>
            
            <!-- New Dates -->
            <div style="flex: 1; background: #e8f0e8; border-radius: 12px; padding: 20px; border: 1px solid #d4e2d4;">
              <div style="text-align: center; margin-bottom: 15px;">
                <span style="font-size: 32px;">✨</span>
                <h3 style="color: #2c7a4d; margin: 8px 0 0 0; font-size: 16px; font-weight: 600;">New Dates</h3>
              </div>
              <div style="background: #ffffff; border-radius: 8px; padding: 15px; text-align: center;">
                <p style="margin: 0 0 8px 0; color: #7a6a5a;">
                  <strong style="color: #2c7a4d;">Check-in:</strong><br>
                  <span style="font-size: 14px; color: #2c3e2f; font-weight: 500;">${new Date(booking.checkIn).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
                </p>
                <p style="margin: 0; color: #7a6a5a;">
                  <strong style="color: #2c7a4d;">Check-out:</strong><br>
                  <span style="font-size: 14px; color: #2c3e2f; font-weight: 500;">${new Date(booking.checkOut).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
                </p>
              </div>
            </div>
          </div>
          
          <!-- Updated Booking Details -->
          <div style="background: #faf9f7; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #e8e2d9;">
            <h3 style="color: #2c3e2f; margin: 0 0 20px 0; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
              <span style="font-size: 22px; margin-right: 8px;">🏨</span> Updated Reservation Details
            </h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 10px 0; color: #7a6a5a; border-bottom: 1px solid #e8e2d9;">Room</td>
                <td style="padding: 10px 0; color: #2c3e2f; font-weight: 500; border-bottom: 1px solid #e8e2d9;">${room.name}</td>
              </tr>
              <tr>
                <td style="padding: 10px 0; color: #7a6a5a; border-bottom: 1px solid #e8e2d9;">Nights</td>
                <td style="padding: 10px 0; color: #2c3e2f; border-bottom: 1px solid #e8e2d9;">${booking.nights} ${booking.nights === 1 ? 'Night' : 'Nights'}</td>
              </tr>
              <tr>
                <td style="padding: 10px 0; color: #7a6a5a; border-bottom: 1px solid #e8e2d9;">Guests</td>
                <td style="padding: 10px 0; color: #2c3e2f; border-bottom: 1px solid #e8e2d9;">${booking.guests} ${booking.guests === 1 ? 'Guest' : 'Guests'}</td>
              </tr>
              <tr>
                <td style="padding: 15px 0 0 0; color: #7a6a5a; font-size: 16px;">Total Amount</td>
                <td style="padding: 15px 0 0 0; color: #c4a27a; font-size: 28px; font-weight: bold;">$${booking.totalAmount}</td>
              </tr>
            </table>
          </div>
          
          <!-- Room Details -->
          <div style="background: #faf9f7; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #e8e2d9;">
            <h3 style="color: #2c3e2f; margin: 0 0 15px 0; font-size: 18px; font-weight: 600; display: flex; align-items: center;">
              <span style="font-size: 22px; margin-right: 8px;">🛏️</span> Room Features
            </h3>
            <p style="margin: 0 0 12px 0; color: #5a5a5a;">
              <strong style="color: #c4a27a;">Capacity:</strong> Up to ${room.capacity} ${room.capacity === 1 ? 'Guest' : 'Guests'}
            </p>
            ${room.facilities && room.facilities.length > 0 ? `
              <p style="margin: 0 0 8px 0; color: #5a5a5a;"><strong style="color: #c4a27a;">Amenities:</strong></p>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                ${room.facilities.map(facility => `
                  <span style="background: #e8e2d9; color: #5a4a3a; padding: 4px 12px; border-radius: 20px; font-size: 13px;">${facility}</span>
                `).join('')}
              </div>
            ` : '<p style="margin: 0; color: #5a5a5a;">Contact us for detailed room amenities.</p>'}
          </div>
          
          <!-- Important Information -->
          <div style="background: #fef7e8; border-left: 3px solid #c4a27a; padding: 20px; margin: 30px 0; border-radius: 8px;">
            <p style="margin: 0 0 8px 0; color: #7a6a5a; font-size: 14px;">
              <strong>📝 Need to make further changes?</strong>
            </p>
            <p style="margin: 0 0 15px 0; color: #7a6a5a; font-size: 14px;">
              You can reschedule your booking anytime by logging into your account at <a href="#" style="color: #c4a27a; text-decoration: none;">www.blueislandbeachhotel.com/mybookings</a>
            </p>
            <p style="margin: 0; color: #7a6a5a; font-size: 14px;">
              <strong>📞 Questions?</strong><br>
              Our concierge team is available 24/7 at +1 (555) 123-4567 or reservations@blueislandbeachhotel.com
            </p>
          </div>
          
          <!-- Cancellation Policy Note -->
          <div style="margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; text-align: center;">
            <p style="color: #7a6a5a; margin: 0; font-size: 13px;">
              ⚠️ Please note that rescheduling may affect your cancellation policy. Review your updated reservation terms in your account.
            </p>
          </div>
          
          <!-- Signature -->
          <div style="margin-top: 35px;">
            <p style="color: #5a5a5a; margin: 0 0 5px 0;">Thank you for choosing Blue Island Beach Hotel,</p>
            <p style="color: #2c3e2f; margin: 0; font-size: 18px; font-weight: 500;">The Blue Island Beach Hotel Team</p>
            <p style="color: #9b9b9b; margin: 15px 0 0 0; font-size: 12px; line-height: 1.4;">
              🌟 We look forward to welcoming you soon 🌟
            </p>
          </div>
        </div>
        
        <!-- Footer -->
        <div style="background: #f7f5f0; padding: 20px 35px; text-align: center; border-top: 1px solid #e8e2d9;">
          <p style="color: #9b9b9b; margin: 0 0 8px 0; font-size: 12px;">
            This email confirms your rescheduled reservation. Please keep it for your records.
          </p>
          <p style="color: #9b9b9b; margin: 0; font-size: 11px;">
            © 2024 Blue Island Beach Hotel. All rights reserved.
          </p>
          <p style="color: #9b9b9b; margin: 8px 0 0 0; font-size: 11px;">
            This is an automated message, please do not reply directly to this email.
          </p>
        </div>
      </div>
    </body>
    </html>
  `,
};

    // Add timeout to prevent hanging indefinitely
    await Promise.race([
      transport.sendMail(mailOptions),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Email send timeout (3s)")), 3000)
      )
    ]);

    info("Booking reschedule confirmation email sent", {
      to: booking.guestEmail,
      bookingId: booking._id,
    });

    return true;
  } catch (error) {
    const errorDetails = {
      to: booking.guestEmail,
      bookingId: booking._id,
      errorMessage: error.message,
      errorCode: error.code,
      errorName: error.name,
    };
    // This is non-blocking/optional - log but don't break reschedule
    logError("Failed to send reschedule confirmation email (non-critical)", errorDetails);
    return false; // Silently fail without throwing
  }
}

module.exports = {
  sendBookingConfirmationEmail,
  sendRescheduleConfirmationEmail,
};
