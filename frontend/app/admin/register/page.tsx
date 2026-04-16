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

export default function AdminRegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [adminKey, setAdminKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();

    try {
      setError("");
      setLoading(true);

      const response = await apiRequest<RegisterResponse>("/auth/admin/register-temp", {
        method: "POST",
        body: { name, email, password, adminKey },
      });

      saveAuthState({ token: response.token, user: response.user });
      window.location.href = "/admin";
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Admin registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />
      <main className="auth-layout">
        <section className="card auth-card">
          <h1 className="auth-title">Temporary Admin Registration</h1>
          <p>Use the secured temporary key to onboard hotel administrators.</p>
          {error && <p className="message error">{error}</p>}

          <form className="stack gap-md" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="name">Admin Name</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>

            <div className="field">
              <label htmlFor="email">Admin Email</label>
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

            <div className="field">
              <label htmlFor="adminKey">Temporary Admin Key</label>
              <input
                id="adminKey"
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                required
              />
            </div>

            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Registering..." : "Register Admin"}
            </button>
          </form>

          <p>
            Back to <Link href="/login">Login</Link>
          </p>
        </section>
      </main>
    </>
  );
}
