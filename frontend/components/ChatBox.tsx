"use client";

import { KeyboardEvent, ReactNode, useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/lib/types";
import { AGENT_WS_URL } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface ChatBoxProps {
  userId?: string;
  compact?: boolean;
}

export default function ChatBox({ userId, compact = false }: ChatBoxProps) {
  const { auth } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const currentUserId = userId || auth?.user.id;

  const appendMessage = (message: Omit<ChatMessage, "id">) => {
    setMessages((prev) => [
      ...prev,
      {
        ...message,
        id: crypto.randomUUID(),
      },
    ]);
  };

  const renderInline = (text: string): ReactNode[] => {
    const segments = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
    return segments.map((segment, index) => {
      if (segment.startsWith("**") && segment.endsWith("**")) {
        return (
          <strong key={`segment-${index}`} className="font-semibold text-current">
            {segment.slice(2, -2)}
          </strong>
        );
      }
      if (segment.startsWith("`") && segment.endsWith("`")) {
        return (
          <code
            key={`segment-${index}`}
            className="rounded bg-black/10 px-1.5 py-0.5 text-[0.82rem] font-medium"
          >
            {segment.slice(1, -1)}
          </code>
        );
      }
      return <span key={`segment-${index}`}>{segment}</span>;
    });
  };

  const renderMessageContent = (content: string) => {
    const lines = content
      .split("\n")
      .map((line) => line.trimEnd())
      .filter((line, index, arr) => line !== "" || (index > 0 && arr[index - 1] !== ""));

    const blocks: ReactNode[] = [];
    let idx = 0;

    while (idx < lines.length) {
      const line = lines[idx].trim();
      if (!line) {
        idx += 1;
        continue;
      }

      if (/^[-*]\s+/.test(line)) {
        const items: string[] = [];
        while (idx < lines.length && /^[-*]\s+/.test(lines[idx].trim())) {
          items.push(lines[idx].trim().replace(/^[-*]\s+/, ""));
          idx += 1;
        }
        blocks.push(
          <ul key={`ul-${idx}`} className="ml-5 list-disc space-y-1 text-[0.93rem] leading-relaxed">
            {items.map((item, itemIndex) => (
              <li key={`li-${idx}-${itemIndex}`}>{renderInline(item)}</li>
            ))}
          </ul>
        );
        continue;
      }

      if (/^\d+\.\s+/.test(line)) {
        const items: string[] = [];
        while (idx < lines.length && /^\d+\.\s+/.test(lines[idx].trim())) {
          items.push(lines[idx].trim().replace(/^\d+\.\s+/, ""));
          idx += 1;
        }
        blocks.push(
          <ol key={`ol-${idx}`} className="ml-5 list-decimal space-y-1 text-[0.93rem] leading-relaxed">
            {items.map((item, itemIndex) => (
              <li key={`oli-${idx}-${itemIndex}`}>{renderInline(item)}</li>
            ))}
          </ol>
        );
        continue;
      }

      if (line.startsWith("### ") || line.startsWith("## ")) {
        blocks.push(
          <h4 key={`h-${idx}`} className="mt-1 text-[0.98rem] font-semibold tracking-tight">
            {renderInline(line.replace(/^#{2,3}\s+/, ""))}
          </h4>
        );
        idx += 1;
        continue;
      }

      if (line.startsWith(">")) {
        blocks.push(
          <blockquote
            key={`q-${idx}`}
            className="border-l-2 border-current/30 pl-3 text-[0.92rem] italic opacity-90"
          >
            {renderInline(line.replace(/^>\s*/, ""))}
          </blockquote>
        );
        idx += 1;
        continue;
      }

      blocks.push(
        <p key={`p-${idx}`} className="text-[0.94rem] leading-relaxed">
          {renderInline(line)}
        </p>
      );
      idx += 1;
    }

    return <div className="space-y-2 whitespace-pre-wrap wrap-break-word">{blocks}</div>;
  };

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    if (!currentUserId || !auth?.token) {
      console.log("⏳ Waiting for auth - currentUserId:", currentUserId, "token:", auth?.token ? "present" : "missing");
      return;
    }

    const connectWebSocket = () => {
      try {
        const token = auth.token;
        const wsUrl = `${AGENT_WS_URL}/${currentUserId}?token=${token}`;
        
        console.log("🔌 Attempting WebSocket connection to:", wsUrl);
        
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log("✅ WebSocket connected successfully");
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log("📨 WebSocket message received:", data);
          
          // Handle different message types
          if (data.role === "agent") {
            // Check if it's an error message
            if (data.type === "error") {
              setIsTyping(false);
              appendMessage({
                role: "agent",
                content: `❌ ${data.content}`,
                timestamp: data.timestamp || new Date().toISOString(),
                status: "sent",
              });
              console.error("❌ Error from agent:", data.content);
              return;
            }
            
            // Handle regular agent messages
            if (data.type === "connection" || data.type === "message") {
              setIsTyping(false);
              appendMessage({
                role: "agent",
                content: data.content,
                timestamp: data.timestamp || new Date().toISOString(),
                toolUsage: data.tool_usage,
                status: "sent",
              });
              console.log("✓ Message added to chat");
            }
          } else {
            console.warn("⚠️ Unexpected message format:", data);
          }
        };

        ws.onerror = (error) => {
          console.error("❌ WebSocket error:", error);
          setError("Connection error");
          setIsConnected(false);
          setIsTyping(false);
        };

        ws.onclose = () => {
          console.log("⛔ WebSocket disconnected");
          setIsConnected(false);
          setIsTyping(false);
          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        };

        wsRef.current = ws;
      } catch (err) {
        setError("Failed to connect to chat");
        console.error("WebSocket error:", err);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [currentUserId, auth?.token]);

  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn("⚠️ Cannot send message - WebSocket not ready or input empty");
      return;
    }

    appendMessage({
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
      status: "sent",
    });

    console.log("📤 Sending message:", input);
    wsRef.current.send(JSON.stringify({ message: input }));
    setInput("");
    setIsTyping(true);
  };

  const handleInputKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isTyping && input.trim()) {
        sendMessage(event as unknown as React.FormEvent);
      }
    }
  };

  if (!currentUserId) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Please log in to use the chat
      </div>
    );
  }

  const outerClass = compact
    ? "h-[560px]"
    : "h-[calc(100dvh-66px)] px-2 py-2 sm:px-4 sm:py-4";

  const shellClass = compact
    ? "flex h-full flex-col overflow-hidden rounded-2xl border border-(--border) bg-(--surface) shadow-[var(--shadow)]"
    : "mx-auto flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-(--border) bg-(--surface) shadow-[var(--shadow)]";

  return (
    <section
      className={`${outerClass} bg-[radial-gradient(circle_at_10%_-10%,rgba(201,164,93,0.17)_0%,transparent_42%),radial-gradient(circle_at_90%_0%,rgba(14,92,91,0.12)_0%,transparent_36%),var(--bg)]`}
    >
      <div className={shellClass}>
      {/* Header */}
      <header className="border-b border-(--border) bg-linear-to-r from-(--primary) to-[#164f62] px-4 py-3 text-white sm:px-6 sm:py-4">
        <div className="flex items-start justify-between gap-3 sm:items-center">
          <div className="min-w-0">
            <p className="text-[0.78rem] uppercase tracking-[0.22em] text-white/70">Live Assistant</p>
            <h2 className="truncate text-base font-semibold sm:text-lg">Blue Island Beach Concierge</h2>
          </div>
          <div className="flex shrink-0 items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs sm:text-sm">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                isConnected ? "bg-emerald-300" : "bg-rose-300"
              }`}
            />
            <span>{isConnected ? "Connected" : "Reconnecting"}</span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="chat-scrollbar flex-1 space-y-4 overflow-y-auto px-3 py-4 sm:px-6 sm:py-5">
        {messages.length === 0 && (
          <div className="grid h-full place-items-center">
            <div className="w-full max-w-md rounded-2xl border border-dashed border-(--border) bg-white/80 px-6 py-8 text-center text-(--text-soft) backdrop-blur">
              <div className="mb-4 text-4xl">💬</div>
              <p className="text-sm font-medium text-foreground">Start a conversation to book your stay</p>
              <p className="mt-2 text-xs sm:text-sm">Try: &quot;Book a room from 2026-04-20 to 2026-04-28 for 3 guests&quot;</p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-end gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "agent" && (
              <div className="mb-1 hidden h-8 w-8 shrink-0 items-center justify-center rounded-full bg-(--surface-muted) text-sm text-(--primary-strong) sm:flex">
                AI
              </div>
            )}
            <div
              className={`chat-rise max-w-[88%] rounded-2xl px-4 py-3 sm:max-w-[75%] ${
                msg.role === "user"
                  ? "rounded-br-md bg-(--primary) text-white"
                  : "rounded-bl-md border border-(--border) bg-(--surface-muted) text-foreground"
              }`}
            >
              {renderMessageContent(msg.content)}
              <div className="mt-2 flex items-center justify-between gap-2">
                <p className={`text-[0.7rem] ${
                msg.role === "user" ? "text-white/75" : "text-(--text-soft)"
              }`}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>

              {msg.toolUsage && (
                <div className="rounded-full border border-current/20 px-2 py-0.5 text-[0.68rem] opacity-85">
                  🔧 {msg.toolUsage.toolName}
                </div>
              )}
              </div>
            </div>
            {msg.role === "user" && (
              <div className="mb-1 hidden h-8 w-8 shrink-0 items-center justify-center rounded-full bg-(--accent)/20 text-sm font-semibold text-(--primary-strong) sm:flex">
                You
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-md border border-(--border) bg-(--surface-muted) px-4 py-3 text-foreground">
              <div className="flex gap-1">
                <div className="h-2 w-2 animate-bounce rounded-full bg-(--text-soft)" />
                <div className="h-2 w-2 animate-bounce rounded-full bg-(--text-soft)" style={{ animationDelay: "0.1s" }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-(--text-soft)" style={{ animationDelay: "0.2s" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <div className="border-y border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700 sm:px-6">
          {error} - Attempting to reconnect...
        </div>
      )}

      {/* Input */}
      <form onSubmit={sendMessage} className="border-t border-(--border) bg-white/85 px-3 py-3 backdrop-blur sm:px-5 sm:py-4">
        <div className="flex items-end gap-2 sm:gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Tell me about your booking needs..."
            rows={1}
            className="max-h-32 min-h-11 flex-1 resize-none rounded-xl border border-(--border) bg-white px-4 py-2.5 text-sm text-foreground outline-none ring-(--primary) transition focus:ring-2"
            disabled={!isConnected}
          />
          <button
            type="submit"
            disabled={!isConnected || isTyping || !input.trim()}
            className="h-11 rounded-xl bg-(--primary) px-4 font-semibold text-white transition hover:bg-(--primary-strong) disabled:cursor-not-allowed disabled:opacity-50 sm:px-6"
          >
            <span className="hidden sm:inline">Send</span>
            <span className="sm:hidden">➤</span>
          </button>
        </div>
        <p className="mt-2 text-[0.7rem] text-(--text-soft)">Press Enter to send, Shift+Enter for a new line.</p>
      </form>
      </div>
    </section>
  );
}
