const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("retainiq_token");
}
export function authHeaders(): Record<string, string> {
  const t = token();
  return t ? { Authorization: `Bearer ${t}` } : {};
}
export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts.headers || {}) },
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth")) {
    localStorage.removeItem("retainiq_token");
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}
export function logout() {
  localStorage.removeItem("retainiq_token");
  window.location.href = "/login";
}
