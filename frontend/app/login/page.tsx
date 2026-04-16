"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Header } from "@/components/Header";
import { saveAuthState } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { AuthUser } from "@/lib/types";

type LoginResponse = {
  success: boolean;
  token: string;
  user: AuthUser;
};

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      setError("");
      setLoading(true);

      const response = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });

      saveAuthState({ token: response.token, user: response.user });
      window.location.href = response.user.role === "admin" ? "/admin" : "/";
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="auth-layout">
        <section className="card auth-card">
          <h1 className="auth-title">Welcome Back</h1>
          <p>Sign in to manage your hotel bookings and room availability.</p>
          {error && <p className="message error">{error}</p>}

          <form className="stack gap-md" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Login"}
            </button>
          </form>

          <p>
            New customer? <Link href="/register">Create user account</Link>
          </p>
          <p>
            Need admin onboarding? <Link href="/admin/register">Temporary admin register</Link>
          </p>
        </section>
      </main>
    </>
  );
}
