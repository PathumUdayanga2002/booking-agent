"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Header } from "@/components/Header";
import { getAuthState } from "@/lib/auth";
import { apiRequest } from "@/lib/api";

type DashboardResponse = {
  success: boolean;
  stats: {
    totalBookings: number;
    totalRooms: number;
    totalRoomUnits: number;
    bookedUnits: number;
    availableUnits: number;
    range: {
      checkIn: string;
      checkOut: string;
    };
  };
  roomAvailability: Array<{
    roomId: string;
    roomName: string;
    totalUnits: number;
    bookedUnits: number;
    availableUnits: number;
    checkIn: string;
    checkOut: string;
  }>;
  latestBookings: Array<{
    _id: string;
    roomNameSnapshot: string;
    guestName: string;
    checkIn: string;
    checkOut: string;
    totalAmount: number;
    status: string;
  }>;
};

function toDateInputValue(date: Date) {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export default function AdminDashboardPage() {
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
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [pricePerNight, setPricePerNight] = useState(120);
  const [capacity, setCapacity] = useState(2);
  const [totalUnits, setTotalUnits] = useState(1);
  const [facilities, setFacilities] = useState("WiFi, Breakfast");

  const auth = getAuthState();

  async function loadDashboard() {
    if (!auth?.token) {
      return;
    }

    try {
      setError("");
      const response = await apiRequest<DashboardResponse>(
        `/admin/dashboard?checkIn=${encodeURIComponent(checkIn)}&checkOut=${encodeURIComponent(checkOut)}`,
        { token: auth.token }
      );

      setDashboard(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load dashboard");
    }
  }

  useEffect(() => {
    if (!auth || auth.user.role !== "admin") {
      window.location.href = "/login";
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboard();
  }, []);

  async function onAddRoom(event: FormEvent) {
    event.preventDefault();

    if (!auth?.token) {
      return;
    }

    try {
      setError("");
      setSuccess("");

      await apiRequest<{ success: boolean }>("/rooms", {
        method: "POST",
        token: auth.token,
        body: {
          name,
          description,
          pricePerNight,
          capacity,
          totalUnits,
          facilities: facilities
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        },
      });

      setSuccess("Room created successfully");
      setName("");
      setDescription("");
      setFacilities("WiFi, Breakfast");
      await loadDashboard();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not create room");
    }
  }

  return (
    <>
      <Header />
      <main className="ai-app-shell">
        <section className="ai-hero">
          <h1>Admin Command Center</h1>
          <p>
            Track operational health, room inventory, and incoming stays in one modern control panel.
          </p>
        </section>

        {error && <p className="message error">{error}</p>}
        {success && <p className="message">{success}</p>}

        <section className="ai-grid-2">
          <article className="ai-card">
            <h2>Add Room</h2>
            <form className="stack gap-md" onSubmit={onAddRoom}>
              <div className="field">
                <label htmlFor="name">Room Name</label>
                <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="pricePerNight">Price / Night</label>
                <input
                  id="pricePerNight"
                  type="number"
                  min={1}
                  value={pricePerNight}
                  onChange={(e) => setPricePerNight(Number(e.target.value))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="capacity">Capacity</label>
                <input
                  id="capacity"
                  type="number"
                  min={1}
                  value={capacity}
                  onChange={(e) => setCapacity(Number(e.target.value))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="totalUnits">Total Units</label>
                <input
                  id="totalUnits"
                  type="number"
                  min={1}
                  value={totalUnits}
                  onChange={(e) => setTotalUnits(Number(e.target.value))}
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="facilities">Facilities</label>
                <input
                  id="facilities"
                  value={facilities}
                  onChange={(e) => setFacilities(e.target.value)}
                  placeholder="WiFi, Pool, Breakfast"
                />
              </div>
              <button className="btn" type="submit">
                Add Room
              </button>
            </form>
          </article>

          <article className="ai-card">
            <h2>Live Availability</h2>
            <form
              className="filter-card"
              style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
              onSubmit={(event) => {
                event.preventDefault();
                void loadDashboard();
              }}
            >
              <div className="field">
                <label htmlFor="checkIn">Check-in</label>
                <input
                  id="checkIn"
                  type="date"
                  value={checkIn}
                  onChange={(e) => setCheckIn(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="checkOut">Check-out</label>
                <input
                  id="checkOut"
                  type="date"
                  value={checkOut}
                  onChange={(e) => setCheckOut(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Action</label>
                <button className="btn" type="submit">
                  Refresh
                </button>
              </div>
            </form>

            {dashboard?.stats && (
              <div className="ai-kpi-grid">
                <div className="ai-kpi-box">
                  <h4>Total Bookings</h4>
                  <p>{dashboard.stats.totalBookings}</p>
                </div>
                <div className="ai-kpi-box">
                  <h4>Total Rooms</h4>
                  <p>{dashboard.stats.totalRooms}</p>
                </div>
                <div className="ai-kpi-box">
                  <h4>Booked Units</h4>
                  <p>{dashboard.stats.bookedUnits}</p>
                </div>
                <div className="ai-kpi-box">
                  <h4>Available Units</h4>
                  <p>{dashboard.stats.availableUnits}</p>
                </div>
              </div>
            )}
          </article>
        </section>

        <section className="ai-card ai-table-card">
          <h2>Room Availability Table</h2>
          <div className="ai-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Room</th>
                  <th>Total Units</th>
                  <th>Booked Units</th>
                  <th>Available Units</th>
                </tr>
              </thead>
              <tbody>
                {dashboard?.roomAvailability.map((item) => (
                  <tr key={item.roomId}>
                    <td>{item.roomName}</td>
                    <td>{item.totalUnits}</td>
                    <td>{item.bookedUnits}</td>
                    <td>{item.availableUnits}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="ai-card ai-table-card">
          <h2>Upcoming Check-in / Check-out</h2>
          <div className="ai-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Guest</th>
                  <th>Room</th>
                  <th>Check-in</th>
                  <th>Check-out</th>
                  <th>Bill</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {dashboard?.latestBookings
                  .filter((booking) => booking.status === "confirmed")
                  .map((booking) => (
                    <tr key={booking._id}>
                      <td>{booking.guestName}</td>
                      <td>{booking.roomNameSnapshot}</td>
                      <td>{new Date(booking.checkIn).toLocaleDateString()}</td>
                      <td>{new Date(booking.checkOut).toLocaleDateString()}</td>
                      <td>${booking.totalAmount}</td>
                      <td>
                        <span className={`ai-status-pill ${booking.status}`}>
                          {booking.status}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </>
  );
}
