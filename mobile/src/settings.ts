import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "docketai.apiUrl";
// DEFAULT_API_URL placeholder for local/emulator; replace once production API URL is known (do not invent).
export const DEFAULT_API_URL = "https://docketai-desk.onrender.com";

export async function getApiUrl(): Promise<string> {
  const v = await AsyncStorage.getItem(KEY);
  return (v && v.trim()) || DEFAULT_API_URL;
}

export async function setApiUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(KEY, url.trim().replace(/\/$/, ""));
}
