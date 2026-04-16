"use client";

import { useState, useMemo } from "react";

type CalendarDay = {
  date: Date;
  isCurrentMonth: boolean;
  isBooked: boolean;
  isSelected: boolean;
  isInRange: boolean;
};

type BookingRange = {
  checkIn: string; // ISO date string
  checkOut: string; // ISO date string
};

type CalendarProps = {
  bookedDateRanges: BookingRange[]; // Array of booking date ranges
  selectedCheckIn?: string; // YYYY-MM-DD
  selectedCheckOut?: string; // YYYY-MM-DD
  onSelectDates: (checkIn: string, checkOut: string) => void;
};

export function AvailabilityCalendar({
  bookedDateRanges,
  selectedCheckIn,
  selectedCheckOut,
  onSelectDates,
}: CalendarProps) {
  const [displayMonth, setDisplayMonth] = useState(new Date());
  const [tempCheckIn, setTempCheckIn] = useState<Date | null>(
    selectedCheckIn ? new Date(`${selectedCheckIn}T00:00:00Z`) : null
  );
  const [tempCheckOut, setTempCheckOut] = useState<Date | null>(
    selectedCheckOut ? new Date(`${selectedCheckOut}T00:00:00Z`) : null
  );

  const bookedDateSet = useMemo(() => {
    const bookedDates = new Set<string>();
    
    // Iterate through each booking range and add all dates in that range
    for (const booking of bookedDateRanges) {
      const checkIn = new Date(booking.checkIn);
      const checkOut = new Date(booking.checkOut);
      
      // Add each date from checkIn (inclusive) to checkOut (exclusive)
      const current = new Date(checkIn);
      while (current < checkOut) {
        const dateStr = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}-${String(current.getDate()).padStart(2, "0")}`;
        bookedDates.add(dateStr);
        current.setDate(current.getDate() + 1);
      }
    }
    
    return bookedDates;
  }, [bookedDateRanges]);

  const calendarDays = useMemo(() => {
    const year = displayMonth.getFullYear();
    const month = displayMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    const days: CalendarDay[] = [];
    const current = new Date(startDate);

    for (let i = 0; i < 42; i++) {
      const dateStr = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}-${String(current.getDate()).padStart(2, "0")}`;
      const isCurrentMonth = current.getMonth() === month;
      const isBooked = bookedDateSet.has(dateStr);

      let isSelected = false;
      let isInRange = false;

      if (tempCheckIn && tempCheckOut) {
        isSelected = dateStr === tempCheckIn.toISOString().split("T")[0] || dateStr === tempCheckOut.toISOString().split("T")[0];
        if (tempCheckIn <= current && current < tempCheckOut) {
          isInRange = true;
        }
      }

      days.push({
        date: new Date(current),
        isCurrentMonth,
        isBooked,
        isSelected,
        isInRange,
      });

      current.setDate(current.getDate() + 1);
    }

    return days;
  }, [displayMonth, bookedDateSet, tempCheckIn, tempCheckOut]);

  function handleDayClick(day: CalendarDay) {
    if (day.isBooked || !day.isCurrentMonth) return;

    if (!tempCheckIn || (tempCheckIn && tempCheckOut)) {
      setTempCheckIn(day.date);
      setTempCheckOut(null);
    } else {
      if (day.date < tempCheckIn) {
        setTempCheckOut(tempCheckIn);
        setTempCheckIn(day.date);
      } else {
        setTempCheckOut(day.date);
      }
    }
  }

  function handleConfirm() {
    if (tempCheckIn && tempCheckOut) {
      const checkInStr = `${tempCheckIn.getFullYear()}-${String(tempCheckIn.getMonth() + 1).padStart(2, "0")}-${String(tempCheckIn.getDate()).padStart(2, "0")}`;
      const checkOutStr = `${tempCheckOut.getFullYear()}-${String(tempCheckOut.getMonth() + 1).padStart(2, "0")}-${String(tempCheckOut.getDate()).padStart(2, "0")}`;
      onSelectDates(checkInStr, checkOutStr);
    }
  }

  const monthName = displayMonth.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  return (
    <div style={{ background: "var(--surface)", borderRadius: "var(--radius)", padding: "1.5rem" }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <div className="row space-between center" style={{ marginBottom: "1rem" }}>
          <button
            onClick={() =>
              setDisplayMonth(new Date(displayMonth.getFullYear(), displayMonth.getMonth() - 1))
            }
            style={{
              background: "var(--primary)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius)",
              padding: "0.5rem 1rem",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            ← Prev
          </button>
          <h3 style={{ margin: 0, color: "var(--text)", fontSize: "1.1rem" }}>{monthName}</h3>
          <button
            onClick={() =>
              setDisplayMonth(new Date(displayMonth.getFullYear(), displayMonth.getMonth() + 1))
            }
            style={{
              background: "var(--primary)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius)",
              padding: "0.5rem 1rem",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Next →
          </button>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(7, 1fr)",
          gap: "0.5rem",
          marginBottom: "1.5rem",
        }}
      >
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <div key={day} style={{ textAlign: "center", fontWeight: "bold", color: "var(--text)", padding: "0.5rem" }}>
            {day}
          </div>
        ))}

        {calendarDays.map((day, idx) => {
          let bgColor = "var(--bg)";
          let textColor = "var(--text)";
          let opacity = 1;
          let cursor = "pointer";

          if (!day.isCurrentMonth) {
            opacity = 0.3;
          } else if (day.isBooked) {
            bgColor = "var(--danger)";
            textColor = "white";
            cursor = "not-allowed";
            opacity = 0.7;
          } else if (day.isSelected) {
            bgColor = "var(--primary)";
            textColor = "white";
          } else if (day.isInRange) {
            bgColor = "var(--primary)";
            textColor = "white";
            opacity = 0.5;
          }

          return (
            <div
              key={idx}
              onClick={() => handleDayClick(day)}
              style={{
                padding: "0.75rem",
                textAlign: "center",
                background: bgColor,
                color: textColor,
                borderRadius: "0.25rem",
                cursor,
                opacity,
                fontWeight: day.isSelected ? "bold" : "normal",
                fontSize: "0.9rem",
              }}
            >
              {day.date.getDate()}
            </div>
          );
        })}
      </div>

      <div
        style={{
          display: "flex",
          gap: "1rem",
          justifyContent: "flex-end",
          borderTop: "1px solid var(--border)",
          paddingTop: "1rem",
        }}
      >
        <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
          {tempCheckIn && tempCheckOut
            ? `Selected: ${tempCheckIn.toLocaleDateString()} to ${tempCheckOut.toLocaleDateString()} (${Math.ceil((tempCheckOut.getTime() - tempCheckIn.getTime()) / (1000 * 60 * 60 * 24))} nights)`
            : "Select check-in and check-out dates"}
        </div>
        <button
          onClick={handleConfirm}
          disabled={!tempCheckIn || !tempCheckOut}
          style={{
            background: tempCheckIn && tempCheckOut ? "var(--primary)" : "var(--border)",
            color: tempCheckIn && tempCheckOut ? "white" : "var(--text-secondary)",
            border: "none",
            borderRadius: "var(--radius)",
            padding: "0.5rem 1rem",
            cursor: tempCheckIn && tempCheckOut ? "pointer" : "not-allowed",
            fontWeight: "bold",
          }}
        >
          Confirm Dates
        </button>
      </div>
    </div>
  );
}
