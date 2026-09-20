import { getApiUrl } from "./settings";

async function base(): Promise<string> {
  return (await getApiUrl()).replace(/\/$/, "");
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const url = `${await base()}${path.startsWith("/") ? path : `/${path}`}`;
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} @ ${path}`);
  return r.json();
}

export async function apiPost<T = any>(path: string, body?: unknown): Promise<T> {
  const url = `${await base()}${path.startsWith("/") ? path : `/${path}`}`;
  const r = await fetch(url, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText} @ ${path}${text ? `: ${text.slice(0, 200)}` : ""}`);
  }
  return r.json();
}

export type Pack = {
  id: string;
  name: string;
  description?: string;
  scenarios?: { id: string; name: string }[];
};

export type RunSummary = {
  id: string;
  bot_id: string;
  pack_id: string;
  scores?: Record<string, number>;
  created_at?: string;
};

export async function fetchHealth() {
  return apiGet<{ status: string; service: string }>("/health");
}

export async function fetchPacks() {
  return apiGet<{ packs: Pack[] }>("/api/packs");
}

export async function fetchBots() {
  return apiGet<{ bots: { id: string; name: string; vertical?: string }[] }>("/api/bots");
}

export async function runMysteryShop(bot_id: string, pack_id: string) {
  return apiPost<{
    run_id: string;
    report_id: string;
    scores: Record<string, number>;
    scenarios?: unknown[];
  }>("/api/mystery-shop", { bot_id, pack_id });
}

export async function fetchRuns(limit = 30) {
  return apiGet<{ runs: RunSummary[] }>(`/api/runs?limit=${limit}`);
}

export async function fetchBaseline(pack_id: string) {
  return apiGet<{ pack_id: string; baseline?: Record<string, number>; scores?: Record<string, number> }>(
    `/api/baselines/${encodeURIComponent(pack_id)}`
  );
}

export async function setBaseline(pack_id: string, bot_id?: string) {
  const q = bot_id ? `?bot_id=${encodeURIComponent(bot_id)}` : "";
  return apiPost(`/api/baselines/${encodeURIComponent(pack_id)}${q}`);
}
