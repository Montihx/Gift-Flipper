// Запросы к бэкенду. initData — только в заголовке Authorization, никогда в URL.
import { initData } from "./telegram.js";

const BASE = import.meta.env.VITE_API_BASE || "";

function headers(extra = {}) {
  return { Authorization: `tma ${initData()}`, ...extra };
}

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: headers(body ? { "Content-Type": "application/json" } : {}),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    throw new Error(`${res.status}: ${detail || res.statusText}`);
  }
  return data;
}

export const api = {
  me: () => request("GET", "/api/me"),
  setState: (s) => request("POST", "/api/state", s),
  deals: (params = "") => request("GET", `/api/deals${params}`),
  deal: (id) => request("GET", `/api/deals/${id}`),
  dealSales: (id) => request("GET", `/api/deals/${id}/sales`),
  presets: () => request("GET", "/api/presets"),
  createPreset: (p) => request("POST", "/api/presets", p),
  updatePreset: (id, p) => request("PATCH", `/api/presets/${id}`, p),
  deletePreset: (id) => request("DELETE", `/api/presets/${id}`),
};

// SSE поверх fetch: EventSource не умеет заголовки, а initData в URL класть нельзя.
export async function streamDeals(afterId, onDeal, signal) {
  const res = await fetch(`${BASE}/api/deals/stream?after_id=${afterId}`, {
    headers: headers(),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`stream ${res.status}`);
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buf += value;
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {
      const chunk = buf.slice(0, i);
      buf = buf.slice(i + 2);
      const data = chunk
        .split("\n")
        .filter((l) => l.startsWith("data: "))
        .map((l) => l.slice(6))
        .join("\n");
      if (data) onDeal(JSON.parse(data));
    }
  }
}
