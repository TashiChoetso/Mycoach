const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type User = {
  id: string;
  email: string;
  display_name: string;
  timezone: string;
  locale: string;
  currency: string;
  onboarding_completed_at: string | null;
  preferences: {
    theme: string;
    week_starts_on: number;
    scoring_weights: Record<string, number>;
    dashboard_sections: string[];
  } | null;
  areas: SelectedArea[];
};

export type SelectedArea = {
  id: string;
  area_id: string;
  name: string;
  slug: string | null;
  is_custom: boolean;
  is_enabled: boolean;
  dashboard_visible: boolean;
  sort_order: number;
  icon?: string | null;
};

export type CatalogArea = {
  id: string;
  slug: string | null;
  name: string;
  icon: string | null;
  selected: boolean;
};

export type FocusMark = {
  date: string;
  weekday: string;
  status: "open" | "completed" | "skipped" | string;
};

export type CalendarDay = {
  date: string;
  weekday: string;
  is_today: boolean;
  is_future: boolean;
};

export type FocusItem = {
  id: string;
  focus_id: string;
  user_area_id: string;
  name: string;
  prompt: string | null;
  kind: "check" | "count" | string;
  target_value: number | null;
  unit: string | null;
  is_system: boolean;
  is_enabled: boolean;
  status: "open" | "completed" | "skipped" | string;
  value: number | null;
  score: number | null;
  marks?: FocusMark[];
};

export type AreaBoard = {
  id: string;
  area_id: string;
  name: string;
  slug: string | null;
  tone: string;
  icon: string | null;
  score: number | null;
  completed: number;
  due: number;
  focuses: FocusItem[];
};

export type WeekDay = {
  date: string;
  score: number | null;
  completed: number;
  due: number;
};

export type ProgressDay = {
  date: string;
  weekday: string;
  score: number | null;
  completed: number;
  due: number;
  is_today: boolean;
  is_future: boolean;
  areas?: ProgressArea[];
};

export type ProgressArea = {
  id: string;
  name: string;
  tone: string;
  score: number | null;
  completed: number;
  due: number;
  focuses?: FocusItem[];
};

export type ProgressPayload = {
  range: "day" | "week" | "month" | string;
  offset: number;
  anchor: string;
  start: string;
  end: string;
  label: string;
  today: string;
  summary: {
    score: number | null;
    completed: number;
    due: number;
    days_active: number;
    streak: number;
    best: { date: string; score: number | null } | null;
  };
  series: ProgressDay[];
  weeks: { offset: number; label: string; start: string; end: string; score: number | null; completed: number; due: number }[];
  days: ProgressDay[];
  calendar: (ProgressDay & { in_month?: boolean })[];
  areas: ProgressArea[];
};

export type TodayPayload = {
  greeting: { name: string; period: string; hello: string; quote: string };
  momentum: {
    score: number | null;
    max: number;
    rest_day: boolean;
    label?: string;
    completed?: number;
    due?: number;
    remaining?: number;
  };
  week: WeekDay[];
  week_days?: CalendarDay[];
  tasks: { items: unknown[]; completed: number; total: number };
  habits: { items: unknown[]; completed: number; due: number };
  finance: { spent_today: number; daily_budget: number | null; remaining: number | null } | null;
  areas: AreaBoard[];
  coach: { message: string; cta: { label: string } | null } | null;
  date?: string;
  priorities?: { day: string; month: string };
};

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
};

// Access token stays in memory only. Refresh rides the httpOnly cookie.
let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

function token(): string | null {
  return accessToken;
}

function store(data: TokenResponse) {
  accessToken = data.access_token;
}

export function clearSession() {
  accessToken = null;
}

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.error?.message ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  const access = token();
  if (access) headers.set("Authorization", `Bearer ${access}`);
  let res = await fetch(`${API}/api/v1${path}`, { ...init, headers, credentials: "include" });
  if (res.status === 401) {
    const refreshed = await refresh();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed}`);
      res = await fetch(`${API}/api/v1${path}`, { ...init, headers, credentials: "include" });
    }
  }
  if (!res.ok) throw new Error(await readError(res));
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function refresh(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const res = await fetch(`${API}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        clearSession();
        return null;
      }
      const data = (await res.json()) as TokenResponse;
      store(data);
      return data.access_token;
    })().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function register(input: {
  email: string;
  password: string;
  display_name: string;
  timezone: string;
}): Promise<User> {
  const data = await api<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
  store(data);
  return data.user;
}

export async function login(email: string, password: string): Promise<User> {
  const data = await api<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  store(data);
  return data.user;
}

export async function logout() {
  try {
    await api("/auth/logout", { method: "POST", body: JSON.stringify({}) });
  } finally {
    clearSession();
  }
}

export async function forgotPassword(email: string): Promise<{ ok: boolean; reset_token?: string }> {
  return api("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) });
}

export async function resetPassword(token: string, password: string): Promise<void> {
  await api("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export async function changePassword(current_password: string, new_password: string): Promise<void> {
  await api("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password, new_password }),
  });
}

export async function updateMe(input: {
  display_name?: string;
  timezone?: string;
  locale?: string;
  currency?: string;
}): Promise<User> {
  return api("/me", { method: "PATCH", body: JSON.stringify(input) });
}

export async function updatePreferences(input: {
  theme?: string;
  week_starts_on?: number;
}): Promise<User> {
  return api("/me/preferences", { method: "PATCH", body: JSON.stringify(input) });
}

export async function exportAccount(): Promise<Record<string, unknown>> {
  return api("/me/export");
}

export async function deleteAccount(password: string): Promise<void> {
  await api("/me", { method: "DELETE", body: JSON.stringify({ password }) });
  clearSession();
}

export const me = () => api<User>("/me");
export const completeOnboarding = () => api<User>("/me/onboarding/complete", { method: "POST" });
export const setPriority = (period: "day" | "month", text: string) =>
  api<{ day: string; month: string }>("/me/priority", {
    method: "PUT",
    body: JSON.stringify({ period, text }),
  });
export const listAreas = () => api<{ catalog: CatalogArea[]; selected: SelectedArea[] }>("/areas");
export const selectArea = (area_id: string) =>
  api<SelectedArea>("/areas", { method: "POST", body: JSON.stringify({ area_id }) });
export const createArea = (name: string) =>
  api<SelectedArea>("/areas", { method: "POST", body: JSON.stringify({ name }) });
export const removeArea = (id: string) => api<void>(`/areas/${id}`, { method: "DELETE" });
export const today = () => api<TodayPayload>("/dashboard/today");
export const progress = (range: "day" | "week" | "month", offset = 0, day?: string) => {
  const params = new URLSearchParams({ range, offset: String(offset) });
  if (day) params.set("day", day);
  return api<ProgressPayload>(`/analytics/progress?${params.toString()}`);
};
export const areaBoard = (id: string) =>
  api<{
    area: AreaBoard;
    week: WeekDay[];
    week_days?: CalendarDay[];
    momentum: TodayPayload["momentum"];
    date: string;
  }>(`/areas/${id}`);
export const completeFocus = (id: string, value?: number, date?: string) =>
  api<{ focus: FocusItem }>("/focuses/" + id + "/complete", {
    method: "POST",
    body: JSON.stringify({
      ...(value == null ? {} : { value }),
      ...(date ? { date } : {}),
    }),
  });
export const skipFocus = (id: string, date?: string) =>
  api<{ focus: FocusItem }>(`/focuses/${id}/skip`, {
    method: "POST",
    body: JSON.stringify(date ? { date } : {}),
  });
export const undoFocus = (id: string, date?: string) =>
  api<{ focus: FocusItem }>(`/focuses/${id}/undo`, {
    method: "POST",
    body: JSON.stringify(date ? { date } : {}),
  });
export const createFocus = (input: {
  user_area_id: string;
  name: string;
  prompt?: string;
  kind: "check" | "count";
  target_value?: number;
  unit?: string;
}) => api<FocusItem>("/focuses", { method: "POST", body: JSON.stringify(input) });
export const deleteFocus = (id: string) => api<void>(`/focuses/${id}`, { method: "DELETE" });
