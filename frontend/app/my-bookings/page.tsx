"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { getAuthState } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { Booking } from "@/lib/types";

type BookingsResponse = {
  success: boolean;
  bookings: Booking[];
};

type RescheduleResponse = {
  success: boolean;
  booking: Booking;
  billing: {
    nights: number;
    pricePerNight: number;
    totalAmount: number;
    currency: string;
    paymentMode: string;
  };
};

function toDateInputValue(date: Date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function toIso(dateValue: string) {
  return new Date(`${dateValue}T00:00:00.000Z`).toISOString();
}

export default function MyBookingsPage() {
  const router = useRouter();
  const auth = getAuthState();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [hasLoaded, setHasLoaded] = useState(false);

  // Reschedule modal state
  const [rescheduleModalOpen, setRescheduleModalOpen] = useState(false);
  const [rescheduleBookingId, setRescheduleBookingId] = useState<string | null>(null);
  const [rescheduleCheckIn, setRescheduleCheckIn] = useState("");
  const [rescheduleCheckOut, setRescheduleCheckOut] = useState("");
  const [rescheduleLoading, setRescheduleLoading] = useState(false);
  const [reschedulePricePerNight, setReschedulePricePerNight] = useState<number>(0);
  const [rescheduleBilling, setRescheduleBilling] = useState<{
    nights: number;
    pricePerNight: number;
    totalAmount: number;
  } | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!auth) {
      router.push("/login");
    }
  }, [auth, router]);

  // Load bookings once when authenticated
  useEffect(() => {
    if (auth && !hasLoaded) {
      loadBookings();
      setHasLoaded(true);
    }
  }, [auth, hasLoaded]);

  async function loadBookings() {
    try {
      setLoading(true);
      setError("");
      const response = await apiRequest<BookingsResponse>("/bookings/me", {
        token: auth?.token,
      });
      setBookings(Array.isArray(response.bookings) ? response.bookings : []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to load bookings";
      setError(errorMsg);
      setBookings([]);
    } finally {
      setLoading(false);
    }
  }

  function openRescheduleModal(booking: Booking) {
    setRescheduleBookingId(booking._id);
    setRescheduleCheckIn(toDateInputValue(new Date(booking.checkIn)));
    setRescheduleCheckOut(toDateInputValue(new Date(booking.checkOut)));
    
    // Get price per night from roomId if populated, otherwise calculate it
    let pricePerNight = 0;
    if (booking.roomId && typeof booking.roomId !== "string" && "pricePerNight" in booking.roomId) {
      pricePerNight = booking.roomId.pricePerNight;
    } else {
      // Fallback: calculate from total amount and nights
      pricePerNight = Math.ceil(booking.totalAmount / booking.nights);
    }
    
    setReschedulePricePerNight(pricePerNight);
    setRescheduleBilling(null);
    setRescheduleModalOpen(true);
  }

  function closeRescheduleModal() {
    setRescheduleModalOpen(false);
    setRescheduleBookingId(null);
    setRescheduleCheckIn("");
    setRescheduleCheckOut("");
    setReschedulePricePerNight(0);
    setRescheduleBilling(null);
  }

  async function handleCancelBooking(booking: Booking) {
    if (!confirm(`Are you sure you want to cancel your booking for ${booking.roomNameSnapshot}?`)) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      
      await apiRequest(
        `/bookings/${booking._id}`,
        {
          token: auth?.token,
          method: "DELETE",
          body: { reason: "Cancelled via My Bookings" },
        }
      );
      
      setSuccess(`Booking cancelled successfully`);
      setTimeout(() => setSuccess(""), 5000);
      // Reload bookings to show updated status
      await loadBookings();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to cancel booking";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleReschedule(e: React.FormEvent) {
    e.preventDefault();
    if (!rescheduleBookingId) return;

    try {
      setRescheduleLoading(true);
      setError("");
      const response = await apiRequest<RescheduleResponse>(
        `/bookings/${rescheduleBookingId}`,
        {
          method: "PUT",
          token: auth?.token,
          body: {
            checkIn: toIso(rescheduleCheckIn),
            checkOut: toIso(rescheduleCheckOut),
          },
        }
      );

      setSuccess(`Booking rescheduled successfully! New total: $${response.booking.totalAmount}`);
      closeRescheduleModal();
      await loadBookings();

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(""), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reschedule booking");
    } finally {
      setRescheduleLoading(false);
    }
  }

  function updateRescheduleDates(checkIn: string, checkOut: string) {
    setRescheduleCheckIn(checkIn);
    setRescheduleCheckOut(checkOut);

    const checkInDate = new Date(`${checkIn}T00:00:00.000Z`);
    const checkOutDate = new Date(`${checkOut}T00:00:00.000Z`);
    const nights = Math.ceil((checkOutDate.getTime() - checkInDate.getTime()) / (1000 * 60 * 60 * 24));

    if (nights > 0 && reschedulePricePerNight > 0) {
      const totalAmount = nights * reschedulePricePerNight;
      setRescheduleBilling({ nights, pricePerNight: reschedulePricePerNight, totalAmount });
    }
  }

  if (!auth) return null;

  return (
    <>
      <Header />
      <main className="ai-app-shell">
        <section className="ai-hero">
          <h1>My Bookings</h1>
          <p>Manage upcoming stays, reschedule dates, or cancel reservations from a single workspace.</p>
        </section>

        {error && (
          <div className="message error ai-toolbar" style={{ marginBottom: "1rem" }}>
            <span>{error}</span>
            <button onClick={() => loadBookings()} disabled={loading} className="btn btn-secondary">
              {loading ? "Retrying..." : "Retry"}
            </button>
          </div>
        )}

        {success && (
          <div className="message" style={{ background: "var(--primary)", color: "white", marginBottom: "1rem" }}>
            {success}
          </div>
        )}

        {loading ? (
          <section className="ai-card">
            <p>Loading your bookings...</p>
          </section>
        ) : bookings.length === 0 ? (
          <div className="ai-card" style={{ padding: "2rem", textAlign: "center" }}>
            <p style={{ fontSize: "1.05rem", color: "var(--text-soft)" }}>
              You have no bookings yet.{" "}
              <Link href="/" style={{ color: "var(--primary)", fontWeight: "bold" }}>
                Book a room now
              </Link>
            </p>
          </div>
        ) : (
          <section className="ai-card ai-table-card">
            <h2 style={{ marginBottom: "0.75rem" }}>Reservation History</h2>
            <div className="ai-table-wrap">
              <table>
              <thead>
                <tr>
                  <th>Room</th>
                  <th>Check-in</th>
                  <th>Check-out</th>
                  <th>Nights</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((booking) => (
                  <tr key={booking._id}>
                    <td>{booking.roomNameSnapshot}</td>
                    <td>{new Date(booking.checkIn).toLocaleDateString()}</td>
                    <td>{new Date(booking.checkOut).toLocaleDateString()}</td>
                    <td>{booking.nights}</td>
                    <td>${booking.totalAmount}</td>
                    <td>
                      <span className={`ai-status-pill ${booking.status}`}>
                        {booking.status}
                      </span>
                    </td>
                    <td>
                      {booking.status === "confirmed" ? (
                        <div className="ai-actions">
                          <button
                            className="btn"
                            style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}
                            onClick={() => openRescheduleModal(booking)}
                          >
                            Reschedule
                          </button>
                          <button
                            className="btn"
                            style={{ 
                              padding: "0.5rem 1rem", 
                              fontSize: "0.875rem",
                              background: "var(--danger)",
                              color: "white"
                            }}
                            onClick={() => handleCancelBooking(booking)}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span style={{ color: "var(--text-soft)" }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

      {/* Reschedule Modal */}
      {rescheduleModalOpen && (
        <div className="ai-modal-backdrop" onClick={closeRescheduleModal}>
          <div
            className="ai-card ai-modal-card"
            style={{ padding: "1.25rem" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: "1rem" }}>Reschedule Booking</h2>

            <form onSubmit={handleReschedule}>
              <div className="field">
                <label htmlFor="reschedule-checkIn">Check-in</label>
                <input
                  id="reschedule-checkIn"
                  type="date"
                  value={rescheduleCheckIn}
                  onChange={(e) => updateRescheduleDates(e.target.value, rescheduleCheckOut)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="reschedule-checkOut">Check-out</label>
                <input
                  id="reschedule-checkOut"
                  type="date"
                  value={rescheduleCheckOut}
                  onChange={(e) => updateRescheduleDates(rescheduleCheckIn, e.target.value)}
                  required
                />
              </div>

              {rescheduleBilling && (
                <div
                  style={{
                    background: "var(--surface-muted)",
                    padding: "1rem",
                    borderRadius: "var(--radius)",
                    marginBottom: "1rem",
                    border: "1px solid var(--border)",
                  }}
                >
                  <p style={{ marginBottom: "0.5rem" }}>
                    <strong>Nights:</strong> {rescheduleBilling.nights}
                  </p>
                  <p style={{ marginBottom: "0.5rem" }}>
                    <strong>Price/Night:</strong> ${rescheduleBilling.pricePerNight}
                  </p>
                  <p style={{ fontSize: "1.1rem", fontWeight: "bold", color: "var(--primary)" }}>
                    <strong>New Total:</strong> ${rescheduleBilling.totalAmount}
                  </p>
                </div>
              )}

              <div className="ai-actions">
                <button
                  className="btn"
                  type="submit"
                  disabled={rescheduleLoading}
                  style={{ flex: 1, minWidth: "180px" }}
                >
                  {rescheduleLoading ? "Updating..." : "Confirm Reschedule"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ flex: 1, minWidth: "120px" }}
                  onClick={closeRescheduleModal}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
