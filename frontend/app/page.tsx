"use client";

import { useState } from "react";
import {
  login,
  chat,
  DEMO_ACCOUNTS,
  type ChatResponse,
  type LoginResponse,
} from "@/lib/api";

interface Turn {
  question: string;
  response?: ChatResponse;
  error?: string;
  pending?: boolean;
}

const C = {
  primary: "#6B8E4E",
  secondary: "#B8860B",
  accent: "#DAA520",
  bg: "#F5EDE0",
  surface: "#FDF8F0",
  text: "#5D4E37",
};

const COLLECTION_COLORS: Record<string, { bg: string; fg: string }> = {
  general: { bg: "#EDE4D3", fg: "#5D4E37" },
  clinical: { bg: "#E3D9C0", fg: "#7A5C1E" },
  nursing: { bg: "#DCE6CE", fg: "#3F5A28" },
  billing: { bg: "#F0E3C2", fg: "#8A6A12" },
  equipment: { bg: "#E0DBC9", fg: "#5A5235" },
};

const heading = { fontFamily: "'Playfair Display', serif" };
const body = { fontFamily: "'Inter', sans-serif" };
const RADIUS = 20;
const SHADOW = "0px 8px 24px rgba(93, 78, 55, 0.15)";

export default function Home() {
  const [session, setSession] = useState<LoginResponse | null>(null);
  const [loginError, setLoginError] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleDemoLogin(username: string, password: string) {
    setLoginError("");
    try {
      setSession(await login(username, password));
      setTurns([]);
    } catch {
      setLoginError("Login failed — is the backend running on :8000?");
    }
  }

  async function handleAsk() {
    const q = input.trim();
    if (!q || !session || busy) return;
    setInput("");
    setBusy(true);
    const idx = turns.length;
    setTurns((t) => [...t, { question: q, pending: true }]);
    try {
      const response = await chat(q, session.token);
      setTurns((t) =>
        t.map((turn, i) => (i === idx ? { question: q, response } : turn))
      );
    } catch {
      setTurns((t) =>
        t.map((turn, i) =>
          i === idx ? { question: q, error: "Request failed" } : turn
        )
      );
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return (
      <main
        style={{ ...body, background: C.bg, color: C.text }}
        className="min-h-screen flex items-center justify-center p-6"
      >
        <div
          style={{
            background: C.surface,
            borderRadius: RADIUS,
            border: `2px solid ${C.primary}`,
            boxShadow: SHADOW,
          }}
          className="w-full max-w-md p-10 relative overflow-hidden"
        >
          <div
            aria-hidden
            style={{
              position: "absolute",
              top: -60,
              right: -60,
              width: 160,
              height: 160,
              borderRadius: "50%",
              border: `2px solid ${C.accent}`,
              opacity: 0.4,
            }}
          />
          <h1 style={{ ...heading, fontWeight: 700, color: C.primary }} className="text-4xl">
            MediBot
          </h1>
          <div
            style={{ background: C.accent }}
            className="h-[2px] w-16 my-3 rounded-full"
          />
          <p className="text-sm" style={{ color: C.text, opacity: 0.7 }}>
            MediAssist Health Network — internal assistant
          </p>
          <p
            className="text-xs mt-6 mb-3 uppercase tracking-widest"
            style={{ color: C.secondary }}
          >
            Sign in as a demo user
          </p>
          <div className="grid grid-cols-1 gap-3">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.username}
                onClick={() => handleDemoLogin(a.username, a.password)}
                style={{
                  borderRadius: RADIUS,
                  border: `2px solid ${C.primary}33`,
                  color: C.text,
                  cursor: "pointer",
                }}
                className="flex items-center justify-between px-5 py-3 text-left transition-all hover:shadow-md"
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = C.accent;
                  e.currentTarget.style.background = "#FBF3E3";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = `${C.primary}33`;
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <span style={{ fontFamily: "Helvetica, Arial, sans-serif" }} className="font-medium text-lg">
                  {a.label}
                </span>
                <span className="text-xs" style={{ color: C.secondary }}>
                  {a.username}
                </span>
              </button>
            ))}
          </div>
          {loginError && (
            <p className="text-sm mt-4" style={{ color: "#a13b2f" }}>
              {loginError}
            </p>
          )}
        </div>
      </main>
    );
  }

  return (
    <main
      style={{ ...body, background: C.bg, color: C.text }}
      className="min-h-screen flex flex-col"
    >
      <header
        style={{
          background: C.surface,
          borderBottom: `2px solid ${C.primary}`,
          boxShadow: SHADOW,
        }}
        className="px-8 py-4 flex items-center justify-between sticky top-0 z-10"
      >
        <div className="flex items-center gap-4">
          <span style={{ ...heading, fontWeight: 700, color: C.primary }} className="text-2xl">
            MediBot
          </span>
          <span
            style={{
              background: C.primary,
              color: C.surface,
              borderRadius: RADIUS,
            }}
            className="px-3 py-1 text-xs font-medium capitalize"
          >
            {session.role.replace("_", " ")}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: C.secondary }}>
            Access:
          </span>
          {session.collections.map((c) => {
            const col = COLLECTION_COLORS[c] ?? { bg: "#EDE4D3", fg: C.text };
            return (
              <span
                key={c}
                style={{ background: col.bg, color: col.fg, borderRadius: 12 }}
                className="px-2.5 py-1 text-xs font-medium"
              >
                {c}
              </span>
            );
          })}
          <button
            onClick={() => setSession(null)}
            className="ml-3 text-xs hover:underline"
            style={{ color: C.secondary, cursor: "pointer" }}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-8 max-w-3xl w-full mx-auto space-y-6">
        {turns.length === 0 && (
          <p
            className="text-center text-sm mt-12 italic"
            style={{ ...heading, color: C.secondary, opacity: 0.8 }}
          >
            Ask a question about your accessible documents.
          </p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className="space-y-3">
            <div className="flex justify-end">
              <div
                style={{
                  background: C.primary,
                  color: C.surface,
                  borderRadius: RADIUS,
                  borderBottomRightRadius: 6,
                  boxShadow: SHADOW,
                }}
                className="px-5 py-2.5 max-w-[80%]"
              >
                {turn.question}
              </div>
            </div>
            <div className="flex justify-start">
              <div
                style={{
                  background: C.surface,
                  border: `2px solid ${C.primary}22`,
                  borderRadius: RADIUS,
                  borderBottomLeftRadius: 6,
                  boxShadow: SHADOW,
                }}
                className="px-5 py-4 max-w-[85%] w-full"
              >
                {turn.pending && (
                  <p style={{ color: C.secondary }} className="text-sm italic">
                    Thinking…
                  </p>
                )}
                {turn.error && (
                  <p style={{ color: "#a13b2f" }} className="text-sm">
                    {turn.error}
                  </p>
                )}
                {turn.response && (
                  <>
                    <div className="flex items-center gap-2 mb-3">
                      <span
                        style={{
                          background:
                            turn.response.retrieval_type === "sql_rag"
                              ? C.secondary
                              : C.primary,
                          color: C.surface,
                          borderRadius: 12,
                        }}
                        className="px-2.5 py-0.5 text-xs font-medium"
                      >
                        {turn.response.retrieval_type === "sql_rag"
                          ? "SQL RAG"
                          : "Hybrid RAG"}
                      </span>
                    </div>
                    <p
                      className="whitespace-pre-wrap leading-relaxed"
                      style={{ color: C.text }}
                    >
                      {turn.response.answer}
                    </p>
                    {turn.response.sources.length > 0 && (
                      <div
                        className="mt-4 pt-3"
                        style={{ borderTop: `2px solid ${C.accent}33` }}
                      >
                        <p
                          className="text-xs font-medium mb-2 uppercase tracking-wider"
                          style={{ color: C.secondary }}
                        >
                          Sources
                        </p>
                        <ul className="space-y-1.5">
                          {turn.response.sources.map((s, j) => {
                            const col = COLLECTION_COLORS[s.collection] ?? {
                              bg: "#EDE4D3",
                              fg: C.text,
                            };
                            return (
                              <li
                                key={j}
                                className="text-xs flex items-center gap-2"
                                style={{ color: C.text }}
                              >
                                <span
                                  style={{
                                    background: col.bg,
                                    color: col.fg,
                                    borderRadius: 8,
                                  }}
                                  className="px-1.5 py-0.5"
                                >
                                  {s.collection}
                                </span>
                                <span className="font-medium">
                                  {s.source_document}
                                </span>
                                <span style={{ opacity: 0.6 }}>
                                  — {s.section_title}
                                </span>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div
        style={{ background: C.surface, borderTop: `2px solid ${C.primary}` }}
        className="px-6 py-5"
      >
        <div className="max-w-3xl mx-auto flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            placeholder="Ask MediBot…"
            style={{
              borderRadius: RADIUS,
              border: `2px solid ${C.primary}44`,
              background: C.bg,
              color: C.text,
            }}
            className="flex-1 px-5 py-3 focus:outline-none"
            onFocus={(e) => (e.currentTarget.style.borderColor = C.accent)}
            onBlur={(e) =>
              (e.currentTarget.style.borderColor = `${C.primary}44`)
            }
          />
          <button
            onClick={handleAsk}
            disabled={busy}
            style={{
              background: C.primary,
              color: C.surface,
              borderRadius: RADIUS,
              boxShadow: SHADOW,
              cursor: "pointer",
            }}
            className="px-6 py-3 font-medium disabled:opacity-50 transition-opacity"
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}
