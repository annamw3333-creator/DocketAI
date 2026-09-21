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

export async function apiPatch<T = any>(path: string, body?: unknown): Promise<T> {
  const url = `${await base()}${path.startsWith("/") ? path : `/${path}`}`;
  const r = await fetch(url, {
    method: "PATCH",
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

export type ScenarioResult = {
  scenario_id: string;
  name?: string;
  scores?: Record<string, number>;
  user?: string;
  assistant?: string;
  passed?: boolean;
  severity?: string;
  reasons?: string[];
  suggested_fixes?: string[];
  overall?: number;
};

export type RunSummary = {
  id: string;
  bot_id: string;
  pack_id: string;
  scores?: Record<string, number>;
  patches?: string[];
  scenarios?: ScenarioResult[];
  transcript?: { user?: string; assistant?: string; scenario_id?: string }[];
  diff?: unknown;
  created_at?: string;
};

export type BrandDraft = {
  draft?: boolean;
  label?: string;
  name: string;
  vertical: string;
  prompt: string;
  faq: { question: string; answer: string }[];
  script?: string[];
  bot_id_suggestion?: string;
  source?: { website_url?: string; page_title?: string; fetch_error?: string | null };
};

export type WidgetTheme = {
  id?: string;
  theme_id?: string;
  name?: string;
  description?: string;
  vibe?: string;
  primary: string;
  accent: string;
  bg: string;
  text: string;
  header_text?: string;
  bot_bubble?: string;
  user_bubble?: string;
  launcher_bg?: string;
  launcher_text?: string;
  position?: "left" | "right" | string;
  avatar_style?: string;
  bot_name?: string;
  display_name?: string;
  greeting?: string;
  swatches?: string[];
};

export type BotRecord = {
  id: string;
  name: string;
  vertical?: string;
  prompt?: string;
  theme?: WidgetTheme;
  theme_config?: Record<string, unknown>;
};

export async function fetchHealth() {
  return apiGet<{ status: string; service: string }>("/health");
}

export async function fetchPacks() {
  return apiGet<{ packs: Pack[] }>("/api/packs");
}

export async function fetchBots() {
  return apiGet<{ bots: BotRecord[] }>("/api/bots");
}

export async function fetchThemes() {
  return apiGet<{ themes: WidgetTheme[]; default_theme_id: string; count: number }>("/api/themes");
}

export async function patchBotTheme(
  botId: string,
  theme: Partial<WidgetTheme> & { theme_id?: string }
) {
  return apiPatch<{
    bot: BotRecord;
    theme: WidgetTheme;
    theme_config: Record<string, unknown>;
  }>(`/api/bots/${encodeURIComponent(botId)}/theme`, theme);
}

export async function fetchEmbedSnippet(botId: string, serviceUrl?: string) {
  const baseUrl = serviceUrl || (await base());
  // Prefer GET with bot's saved theme
  try {
    return await apiGet<{
      snippet: string;
      widget_url: string;
      theme: WidgetTheme;
      bot_id: string;
      steps?: Record<string, string>;
    }>(
      `/api/bots/${encodeURIComponent(botId)}/embed?service_url=${encodeURIComponent(baseUrl)}`
    );
  } catch {
    return apiPost<{
      snippet: string;
      widget_url: string;
      theme: WidgetTheme;
      bot_id: string;
      steps?: Record<string, string>;
    }>("/api/embed-snippet", { service_url: baseUrl, bot_id: botId });
  }
}

export async function runMysteryShop(bot_id: string, pack_id: string) {
  return apiPost<{
    run_id: string;
    report_id: string;
    scores: Record<string, number>;
    patches?: string[];
    scenarios?: ScenarioResult[];
    failures?: { scenario_id: string; reason: string }[];
  }>("/api/mystery-shop", { bot_id, pack_id });
}

export async function fetchRuns(limit = 30) {
  return apiGet<{ runs: RunSummary[] }>(`/api/runs?limit=${limit}`);
}

export async function fetchRun(run_id: string) {
  return apiGet<RunSummary>(`/api/runs/${encodeURIComponent(run_id)}`);
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

export async function createBotFromBrand(input: {
  website_url: string;
  brand_notes?: string;
  name?: string;
  vertical?: string;
  create?: boolean;
  theme_id?: string;
}) {
  return apiPost<{
    draft: BrandDraft;
    bot: BotRecord | null;
    created: boolean;
    label?: string;
    note?: string;
  }>("/api/bots/from-brand", {
    website_url: input.website_url,
    brand_notes: input.brand_notes || "",
    name: input.name || undefined,
    vertical: input.vertical || undefined,
    create: input.create !== false,
    theme_id: input.theme_id || undefined,
  });
}
