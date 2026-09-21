import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "docketai.apiUrl";
const ADMIN_EMAIL_KEY = "docketai.adminEmail";
const ADMIN_TOKEN_KEY = "docketai.adminToken";

// DEFAULT_API_URL placeholder for local/emulator; replace once production API URL is known (do not invent).
export const DEFAULT_API_URL = "https://docketai-desk.onrender.com";

export async function getApiUrl(): Promise<string> {
  const v = await AsyncStorage.getItem(KEY);
  return (v && v.trim()) || DEFAULT_API_URL;
}

export async function setApiUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(KEY, url.trim().replace(/\/$/, ""));
}

export async function getAdminEmail(): Promise<string> {
  return ((await AsyncStorage.getItem(ADMIN_EMAIL_KEY)) || "").trim();
}

export async function setAdminEmail(email: string): Promise<void> {
  const v = email.trim().toLowerCase();
  if (!v) await AsyncStorage.removeItem(ADMIN_EMAIL_KEY);
  else await AsyncStorage.setItem(ADMIN_EMAIL_KEY, v);
}

export async function getAdminToken(): Promise<string> {
  return ((await AsyncStorage.getItem(ADMIN_TOKEN_KEY)) || "").trim();
}

export async function setAdminToken(token: string): Promise<void> {
  const v = token.trim();
  if (!v) await AsyncStorage.removeItem(ADMIN_TOKEN_KEY);
  else await AsyncStorage.setItem(ADMIN_TOKEN_KEY, v);
}

export async function clearAdminCredentials(): Promise<void> {
  await AsyncStorage.multiRemove([ADMIN_EMAIL_KEY, ADMIN_TOKEN_KEY]);
}

export async function hasAdminCredentials(): Promise<boolean> {
  const [e, t] = await Promise.all([getAdminEmail(), getAdminToken()]);
  return Boolean(e || t);
}
