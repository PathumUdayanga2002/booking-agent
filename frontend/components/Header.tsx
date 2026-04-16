"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthUser } from "@/lib/types";
import { clearAuthState, getAuthState } from "@/lib/auth";

export function Header() {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    queueMicrotask(() => {
      const auth = getAuthState();
      setUser(auth?.user || null);
    });
  }, []);

  function logout() {
    clearAuthState();
    window.location.href = "/";
  }

  return (
    <header className="app-header">
      <div className="container row space-between center">
        <Link href="/" className="brand">
          Blue Island Beach Hotel
        </Link>

        <nav className="row gap-md">
          <Link href="/">Home</Link>
          <Link href="/rooms">Rooms</Link>
          {!user && <Link href="/register">Register</Link>}
          {!user && <Link href="/login">Login</Link>}
          {user && <Link href="/my-bookings">My Bookings</Link>}
          {user && <Link href="/chat">💬 Chat</Link>}
          {user?.role === "admin" && <Link href="/admin">Admin</Link>}
          {user?.role === "admin" && <Link href="/admin/knowledge">📚 Knowledge Base</Link>}
          {user && <button onClick={logout}>Logout</button>}
        </nav>
      </div>
    </header>
  );
}
