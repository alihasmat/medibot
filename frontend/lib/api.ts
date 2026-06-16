// lib/api.ts — thin client for the MediBot backend.
const BASE = "http://localhost:8000";

export interface Source {
  source_document: string;
  section_title: string;
  collection: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  retrieval_type: "hybrid_rag" | "sql_rag";
  role: string;
}

export interface LoginResponse {
  token: string;
  role: string;
  collections: string[];
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Invalid credentials");
  return res.json();
}

export async function chat(
  question: string,
  token: string
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Request failed");
  return res.json();
}

export const DEMO_ACCOUNTS = [
  { label: "Doctor", username: "dr.mehta", password: "doctor-pass" },
  { label: "Nurse", username: "nurse.priya", password: "nurse-pass" },
  { label: "Billing Exec", username: "billing.ravi", password: "billing-pass" },
  { label: "Technician", username: "tech.anand", password: "tech-pass" },
  { label: "Admin", username: "admin.sys", password: "admin-pass" },
];
