import React, { useCallback, useState } from "react";
import { TextInput, Text, StyleSheet } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen, Title, Subtitle, Card, Button, Badge, ErrorBox, SectionLabel } from "@/src/components";
import { DEFAULT_API_URL, getApiUrl, setApiUrl } from "@/src/settings";
import { fetchHealth } from "@/src/api";
import { colors, spacing, type } from "@/src/theme";

export default function SettingsScreen() {
  const [url, setUrl] = useState(DEFAULT_API_URL);
  const [saved, setSaved] = useState(false);
  const [ping, setPing] = useState<"idle" | "ok" | "err">("idle");
  const [msg, setMsg] = useState("");

  useFocusEffect(
    useCallback(() => {
      getApiUrl().then(setUrl);
      setSaved(false);
      setPing("idle");
    }, [])
  );

  const onSave = async () => {
    await setApiUrl(url);
    setSaved(true);
    setPing("idle");
  };

  const onTest = async () => {
    await setApiUrl(url);
    try {
      const h = await fetchHealth();
      setPing("ok");
      setMsg(`${h.service || "ok"} · ${h.status}`);
    } catch (e: any) {
      setPing("err");
      setMsg(e?.message || "Unreachable");
    }
  };

  return (
    <Screen>
      <Title>Settings</Title>
      <Subtitle>Point DocketAI at your Docket Desk API.</Subtitle>

      <SectionLabel>API</SectionLabel>
      <Card>
        <Text style={styles.label}>URL</Text>
        <TextInput
          value={url}
          onChangeText={(t) => {
            setUrl(t);
            setSaved(false);
          }}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder={DEFAULT_API_URL}
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.hint}>
          Emulator → http://10.0.2.2:8080 · Device → http://&lt;lan-ip&gt;:8080
        </Text>
        <Button title="Save" onPress={onSave} />
        <Button title="Test /health" onPress={onTest} variant="text" />
        {saved ? <Badge label="Saved" tone="ok" /> : null}
        {ping === "ok" ? <Badge label={`OK · ${msg}`} tone="ok" /> : null}
        {ping === "err" ? <ErrorBox message={msg} /> : null}
      </Card>

      <SectionLabel>About</SectionLabel>
      <Card>
        <Text style={styles.meta}>DocketAI 1.2.0</Text>
        <Text style={styles.meta}>com.docketai.app</Text>
        <Text style={styles.meta}>JS embedded · no Metro required</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontWeight: type.labelWeight,
    fontSize: 11,
    marginBottom: spacing.xs,
    letterSpacing: type.labelTracking,
    textTransform: "uppercase",
  },
  input: {
    backgroundColor: colors.bg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: 2,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: colors.text,
    fontSize: 14,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.sm,
  },
  hint: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: spacing.md,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  meta: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 4,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
});
