"use client";

import Link from "next/link";
import { Header } from "@/components/Header";
import { getAuthState } from "@/lib/auth";

export default function Home() {
  const auth = getAuthState();
  const agentHref = auth ? "/chat" : "/login";

  return (
    <>
      <Header />
      <main className="ai-app-shell">
        <section className="lp-hero">
          <div className="lp-hero-content">
            <span className="lp-badge">Agentic AI + Traditional Booking Platform</span>
            <h1>From Static Booking Forms to a 24/7 Conversational Hotel Agent</h1>
            <p>
              This project modernizes a traditional Node.js hotel booking system with an AI booking assistant.
              Customers can now book with natural conversation, cancel or reschedule with guided confirmations,
              and ask hotel questions through RAG-based knowledge retrieval, all in a live assistant experience.
            </p>
            <p>
              This is an MVP (Minimal Viable Product) that proves the concept end-to-end: Next.js frontend,
              Node.js booking management backend, FastAPI agent backend, and WebSocket real-time chat.
              The AI assistant is built on agentic frameworks using LangChain and LangGraph.
            </p>
            <div className="lp-actions">
              <Link href={agentHref} className="btn">
                Try Live Agent
              </Link>
              <Link href="/rooms" className="btn btn-secondary">Explore Rooms Demo</Link>
            </div>
          </div>
          <aside className="lp-highlight-card">
            <h3>Why This Matters</h3>
            <ul>
              <li>Reduces booking friction with natural language flow.</li>
              <li>Improves customer satisfaction with instant responses.</li>
              <li>Connects AI to real backend APIs and database records.</li>
              <li>Runs continuously as a 24/7 customer-facing concierge.</li>
            </ul>
          </aside>
        </section>

        <section className="lp-metric-grid">
          <article className="lp-metric-card">
            <h4>Core Stack</h4>
            <p>Node.js + FastAPI + Agentic AI</p>
          </article>
          <article className="lp-metric-card">
            <h4>MVP Scope</h4>
            <p>Minimal Viable Product + Concept Validation</p>
          </article>
          <article className="lp-metric-card">
            <h4>Conversation Actions</h4>
            <p>Book, Cancel, Reschedule, Q&A</p>
          </article>
          <article className="lp-metric-card">
            <h4>Knowledge Layer</h4>
            <p>Vector DB + RAG Retrieval</p>
          </article>
          <article className="lp-metric-card">
            <h4>Agentic Framework</h4>
            <p>LangChain + LangGraph</p>
          </article>
          <article className="lp-metric-card">
            <h4>Availability</h4>
            <p>24/7 Real-Time Assistant</p>
          </article>
        </section>

        <section className="lp-compare-grid">
          <article className="ai-card">
            <h3>Traditional Booking Experience</h3>
            <ul className="lp-list">
              <li>User manually fills forms and dates repeatedly.</li>
              <li>Users must navigate many pages for one task.</li>
              <li>No conversational guidance for corrections.</li>
              <li>Hotel FAQs require separate support channels.</li>
            </ul>
          </article>
          <article className="ai-card lp-agentic-card">
            <h3>Agentic AI Booking Experience</h3>
            <ul className="lp-list">
              <li>Users simply chat: “Book from April 20 to 28 for 3 guests.”</li>
              <li>Agent gathers missing details step by step.</li>
              <li>Actions are confirmed and executed via backend tools.</li>
              <li>Hotel policy and service questions answered instantly with RAG.</li>
            </ul>
          </article>
        </section>

        <section className="lp-agent-panel ai-card">
          <div>
            <h3>Try the Agent UX</h3>
            <p>
              Experience the conversational flow used by real customers: guided booking, booking status retrieval,
              cancellation confirmations, rescheduling support, and contextual hotel Q&A.
            </p>
          </div>
          <div className="lp-prompt-grid">
            <div className="lp-prompt">Book a room from 2026-04-20 to 2026-04-28 for 3 guests.</div>
            <div className="lp-prompt">I want to cancel my booking BKG-XXXXXX.</div>
            <div className="lp-prompt">Can I reschedule my booking to next weekend?</div>
            <div className="lp-prompt">What amenities are included in the deluxe room?</div>
          </div>
          <div className="lp-actions">
            <Link href={agentHref} className="btn">
              Open AI Agent
            </Link>
            <Link href="/rooms" className="btn btn-secondary">Open Rooms Page</Link>
          </div>
        </section>
      </main>
    </>
  );
}
