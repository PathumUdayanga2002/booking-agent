"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Header } from "@/components/Header";
import { saveAuthState } from "@/lib/auth";
import { apiRequest } from "@/lib/api";
import { AuthUser } from "@/lib/types";

type RegisterResponse = {
  success: boolean;
  token: string;
  user: AuthUser;
};

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      setError("");
      setLoading(true);

      const response = await apiRequest<RegisterResponse>("/auth/register", {
        method: "POST",
        body: { name, email, password },
      });

      saveAuthState({ token: response.token, user: response.user });
      window.location.href = "/";
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="auth-layout">
        <section className="card auth-card">
          <h1 className="auth-title">Create User Account</h1>
          <p>Register using email and password to book rooms online.</p>
          {error && <p className="message error">{error}</p>}

          <form className="stack gap-md" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="name">Full Name</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>

            <div className="field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Register"}
            </button>
          </form>

          <p>
            Already registered? <Link href="/login">Login here</Link>
          </p>
        </section>
      </main>
    </>
  );
}
