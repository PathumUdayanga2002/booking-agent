"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Header } from "@/components/Header";
import { AvailabilityCalendar } from "@/components/AvailabilityCalendar";
import { getAuthState } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { Booking, Room } from "@/lib/types";

type RoomsResponse = {
  success: boolean;
  rooms: Room[];
};

type BookingsResponse = {
  success: boolean;
  bookings: Booking[];
};

type BookingResponse = {
  success: boolean;
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

export default function RoomsPage() {
  const tomorrow = useMemo(() => {
    const next = new Date();
    next.setDate(next.getDate() + 1);
    return toDateInputValue(next);
  }, []);

  const dayAfterTomorrow = useMemo(() => {
    const next = new Date();
    next.setDate(next.getDate() + 2);
    return toDateInputValue(next);
  }, []);

  const [checkIn, setCheckIn] = useState(tomorrow);
  const [checkOut, setCheckOut] = useState(dayAfterTomorrow);
  const [guests, setGuests] = useState(1);
  const [facilities, setFacilities] = useState("");
  const [rooms, setRooms] = useState<Room[]>([]);
  const [allBookings, setAllBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null);
  const [guestName, setGuestName] = useState("");
  const [guestEmail, setGuestEmail] = useState("");
  const [guestPhone, setGuestPhone] = useState("");
  const [showCalendar, setShowCalendar] = useState(false);

  const auth = getAuthState();

  async function loadAllBookings() {
    try {
      const response = await apiRequest<BookingsResponse>("/bookings/me", {
        token: auth?.token,
      });
      setAllBookings(response.bookings);
    } catch {
      // Silently fail - calendar can still render without booking ranges.
    }
  }

  async function loadRooms() {
    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams({
        checkIn,
        checkOut,
        guests: String(guests),
      });

      if (facilities.trim()) {
        params.set("facilities", facilities.trim());
      }

      const response = await apiRequest<RoomsResponse>(`/rooms?${params.toString()}`);
      setRooms(response.rooms);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load rooms");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadRooms();
    if (auth) {
      void loadAllBookings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSearch(event: FormEvent) {
    event.preventDefault();
    await loadRooms();
  }

  function handleCalendarDatesSelected(newCheckIn: string, newCheckOut: string) {
    setCheckIn(newCheckIn);
    setCheckOut(newCheckOut);
    setShowCalendar(false);

    const checkInIso = toIso(newCheckIn);
    const checkOutIso = toIso(newCheckOut);

    void (async () => {
      try {
        setLoading(true);
        setError("");
        const params = new URLSearchParams({
          checkIn: checkInIso,
          checkOut: checkOutIso,
          guests: String(guests),
        });
        if (facilities.trim()) {
          params.set("facilities", facilities.trim());
        }
        const response = await apiRequest<RoomsResponse>(`/rooms?${params.toString()}`);
        setRooms(response.rooms);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Could not load rooms");
      } finally {
        setLoading(false);
      }
    })();
  }

  async function createBooking(event: FormEvent) {
    event.preventDefault();

    if (!auth?.token) {
      setError("Please login first to continue booking");
      return;
    }

    if (!selectedRoomId) {
      setError("Please select a room to book");
      return;
    }

    try {
      setError("");
      setSuccess("");

      const response = await apiRequest<BookingResponse>("/bookings", {
        method: "POST",
        token: auth.token,
        body: {
          roomId: selectedRoomId,
          checkIn: toIso(checkIn),
          checkOut: toIso(checkOut),
          guests,
          guestName,
          guestEmail,
          guestPhone,
        },
      });

      setSuccess(
        `Booking confirmed. Bill: ${response.billing.currency} ${response.billing.totalAmount}. Payment mode: ${response.billing.paymentMode}`
      );
      setSelectedRoomId(null);
      await loadRooms();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Booking failed");
    }
  }

  return (
    <>
      <Header />
      <main className="ai-app-shell">
        <section className="ai-hero">
          <h1>Rooms and Booking Demo</h1>
          <p>Use filters, check live availability, and complete bookings through the classic operational flow.</p>
        </section>

        <form className="ai-card filter-card" onSubmit={onSearch}>
          <div className="field">
            <label htmlFor="checkIn">Check-in Date</label>
            <input id="checkIn" type="date" value={checkIn} onChange={(e) => setCheckIn(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="checkOut">Check-out Date</label>
            <input id="checkOut" type="date" value={checkOut} onChange={(e) => setCheckOut(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="guests">Guests</label>
            <input id="guests" type="number" min={1} value={guests} onChange={(e) => setGuests(Number(e.target.value))} />
          </div>
          <div className="field">
            <label htmlFor="facilities">Facilities (comma-separated)</label>
            <input id="facilities" value={facilities} onChange={(e) => setFacilities(e.target.value)} placeholder="WiFi, Pool" />
          </div>
          <div className="field">
            <label>Actions</label>
            <div className="row gap-sm" style={{ display: "flex", gap: "0.5rem" }}>
              <button className="btn" type="submit">
                {loading ? "Checking..." : "Check Availability"}
              </button>
              <button
                className="btn"
                type="button"
                style={{ background: showCalendar ? "var(--accent)" : "var(--primary)" }}
                onClick={() => setShowCalendar(!showCalendar)}
              >
                {showCalendar ? "Hide Calendar" : "View Calendar"}
              </button>
            </div>
          </div>
        </form>

        {showCalendar && (
          <section className="ai-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
            <h3 style={{ marginBottom: "1rem" }}>Select Dates from Calendar</h3>
            <p style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "var(--text-soft)" }}>
              Red = Booked | Green = Available
            </p>
            <AvailabilityCalendar
              bookedDateRanges={allBookings.map((b) => ({ checkIn: b.checkIn, checkOut: b.checkOut }))}
              selectedCheckIn={checkIn}
              selectedCheckOut={checkOut}
              onSelectDates={handleCalendarDatesSelected}
            />
          </section>
        )}

        {error && <p className="message error">{error}</p>}
        {success && <p className="message">{success}</p>}

        <section className="rooms-grid" style={{ marginTop: "0.8rem" }}>
          {rooms.map((room) => (
            <article key={room._id} className="ai-card room-card">
              <div className="stack gap-sm">
                <h2>{room.name}</h2>
                <p>{room.description}</p>
              </div>

              <div className="row space-between">
                <strong>${room.pricePerNight} / night</strong>
                <span>Available: {room.availableUnits}/{room.totalUnits}</span>
              </div>

              <div className="pill-wrap">
                {room.facilities.map((facility) => (
                  <span key={facility} className="pill">
                    {facility}
                  </span>
                ))}
              </div>

              <div className="row space-between center gap-sm">
                <span>Capacity: {room.capacity} guests</span>
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={() => setSelectedRoomId(room._id)}
                  disabled={room.availableUnits < 1}
                >
                  {room.availableUnits < 1 ? "Sold Out" : "Book Room"}
                </button>
              </div>
            </article>
          ))}
        </section>

        {selectedRoomId && (
          <section className="ai-card" style={{ padding: "1rem", marginBottom: "2rem" }}>
            <h3>Complete Guest Details</h3>
            <p style={{ color: "var(--text-soft)" }}>Selected room ID: {selectedRoomId}</p>
            <form className="stack gap-md" onSubmit={createBooking}>
              <div className="field">
                <label htmlFor="guestName">Guest Name</label>
                <input id="guestName" value={guestName} onChange={(e) => setGuestName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="guestEmail">Guest Email</label>
                <input id="guestEmail" type="email" value={guestEmail} onChange={(e) => setGuestEmail(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="guestPhone">Guest Phone</label>
                <input id="guestPhone" value={guestPhone} onChange={(e) => setGuestPhone(e.target.value)} required />
              </div>
              <div className="row gap-sm">
                <button className="btn" type="submit">
                  Confirm Booking
                </button>
                <button className="btn btn-danger" type="button" onClick={() => setSelectedRoomId(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}
      </main>
    </>
  );
}
