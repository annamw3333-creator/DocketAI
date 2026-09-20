import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "docketai.apiUrl";
export const DEFAULT_API_URL = "http://10.0.2.2:8080";

export async function getApiUrl(): Promise<string> {
  const v = await AsyncStorage.getItem(KEY);
  return (v && v.trim()) || DEFAULT_API_URL;
}

export async function setApiUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(KEY, url.trim().replace(/\/$/, ""));
}
