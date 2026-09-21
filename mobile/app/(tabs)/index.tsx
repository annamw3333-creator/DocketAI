import React, { useCallback, useState } from "react";
import { Text, View, StyleSheet } from "react-native";
import { useFocusEffect, router } from "expo-router";
import { Screen, Hero, Card, Badge, Button, Loading, SectionLabel, Divider } from "@/src/components";
import { fetchHealth, fetchPacks, fetchBots } from "@/src/api";
import { PERSONAS, ATTACKS } from "@/src/library";
import { colors, spacing, type } from "@/src/theme";
import { getApiUrl } from "@/src/settings";

export default function HomeScreen() {
  const [status, setStatus] = useState<"idle" | "ok" | "err">("idle");
  const [detail, setDetail] = useState("");
  const [packCount, setPackCount] = useState(0);
  const [botCount, setBotCount] = useState(0);
  const [apiUrl, setApiUrlState] = useState("");

  useFocusEffect(
    useCallback(() => {
      let alive = true;
      (async () => {
        const url = await getApiUrl();
        if (!alive) return;
        setApiUrlState(url);
        try {
          const h = await fetchHealth();
          const packs = await fetchPacks().catch(() => ({ packs: [] as any[] }));
          const bots = await fetchBots().catch(() => ({ bots: [] as any[] }));
          if (!alive) return;
          setStatus("ok");
          setDetail(h.service || "docket-desk");
          setPackCount(packs.packs?.length || 0);
          setBotCount(bots.bots?.length || 0);
        } catch (e: any) {
          if (!alive) return;
          setStatus("err");
          setDetail(e?.message || "API unreachable");
        }
      })();
      return () => {
        alive = false;
      };
    }, [])
  );

  return (
    <Screen>
      <Hero
        title="DOCKETAI"
        subtitle="Mystery-shop QA for customer-service chatbots."
      />

      <SectionLabel>Connection</SectionLabel>
      <Card>
        <View style={styles.row}>
          <Text style={styles.label}>Desk API</Text>
          <Badge
            label={status === "ok" ? "Online" : status === "err" ? "Offline" : "Checking"}
            tone={status === "ok" ? "ok" : status === "err" ? "danger" : "muted"}
          />
        </View>
        <Text style={styles.mono}>{apiUrl || "…"}</Text>
        {status === "idle" ? <Loading label="Pinging…" /> : null}
        {status === "ok" ? (
          <Text style={styles.meta}>
            {detail} · {packCount} packs · {botCount} bots
          </Text>
        ) : null}
        {status === "err" ? <Text style={styles.err}>{detail}</Text> : null}
      </Card>

      <Divider />

      <SectionLabel>Library</SectionLabel>
      <Text style={styles.meta}>
        {PERSONAS.length} personas · {ATTACKS.length} attacks
      </Text>
      <Button title="Browse library" onPress={() => router.push("/library")} variant="text" />

      <SectionLabel>Start</SectionLabel>
      <Text style={styles.meta}>Run a pack, then compare Baseline vs Re-check.</Text>
      <Button title="Run a pack" onPress={() => router.push("/run")} />
      <Button title="View results" onPress={() => router.push("/results")} variant="text" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.sm,
  },
  label: {
    color: colors.text,
    fontWeight: type.bodyWeight,
    fontSize: 15,
    letterSpacing: type.letterSpacing,
  },
  mono: {
    color: colors.muted,
    fontFamily: "monospace",
    fontSize: 12,
    marginBottom: spacing.sm,
    letterSpacing: 0.4,
  },
  meta: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  err: {
    color: colors.danger,
    fontSize: 13,
    marginTop: 6,
    letterSpacing: type.letterSpacing,
  },
});
