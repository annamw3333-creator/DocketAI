import React, { useCallback, useState } from "react";
import { Text, View, StyleSheet } from "react-native";
import { useFocusEffect } from "expo-router";
import {
  Screen,
  Title,
  Subtitle,
  Card,
  Button,
  Loading,
  ErrorBox,
  ScoreBar,
  Badge,
} from "@/src/components";
import { fetchBots, fetchPacks, runMysteryShop, setBaseline, fetchBaseline, Pack } from "@/src/api";
import { colors, spacing, type } from "@/src/theme";

export default function RunScreen() {
  const [packs, setPacks] = useState<Pack[]>([]);
  const [bots, setBots] = useState<{ id: string; name: string }[]>([]);
  const [packId, setPackId] = useState<string | null>(null);
  const [botId, setBotId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastScores, setLastScores] = useState<Record<string, number> | null>(null);
  const [baseline, setBaselineScores] = useState<Record<string, number> | null>(null);
  const [runId, setRunId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [p, b] = await Promise.all([fetchPacks(), fetchBots()]);
      setPacks(p.packs || []);
      setBots(b.bots || []);
      if (!packId && p.packs?.[0]) setPackId(p.packs[0].id);
      if (!botId && b.bots?.[0]) setBotId(b.bots[0].id);
    } catch (e: any) {
      setError(e?.message || "Failed to load packs/bots");
    }
  }, [packId, botId]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const overall = (s?: Record<string, number> | null) => {
    if (!s) return null;
    const v = s.overall ?? s.Overall;
    return typeof v === "number" ? v : null;
  };

  const onRun = async () => {
    if (!packId || !botId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await runMysteryShop(botId, packId);
      setLastScores(res.scores || null);
      setRunId(res.run_id);
      try {
        const bl = await fetchBaseline(packId);
        setBaselineScores(bl.baseline || bl.scores || null);
      } catch {
        setBaselineScores(null);
      }
    } catch (e: any) {
      setError(e?.message || "Run failed");
    } finally {
      setBusy(false);
    }
  };

  const onBaseline = async () => {
    if (!packId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await setBaseline(packId, botId || undefined);
      setBaselineScores(res.baseline || null);
    } catch (e: any) {
      setError(e?.message || "Could not set baseline");
    } finally {
      setBusy(false);
    }
  };

  const basePct = overall(baseline);
  const recheckPct = overall(lastScores);
  const delta =
    basePct != null && recheckPct != null ? Math.round(recheckPct - basePct) : null;

  return (
    <Screen>
      <Title>Run</Title>
      <Subtitle>Select a bot and pack, then mystery-shop. Capture Baseline or Re-check after KB updates.</Subtitle>

      {error ? <ErrorBox message={error} /> : null}

      <Text style={styles.section}>Bot</Text>
      {bots.length === 0 && !error ? <Loading /> : null}
      {bots.map((b) => (
        <Card key={b.id} onPress={() => setBotId(b.id)} selected={botId === b.id}>
          <Text style={styles.cardTitle}>{b.name}</Text>
          <Text style={styles.meta}>{b.id}</Text>
        </Card>
      ))}

      <Text style={styles.section}>Pack</Text>
      {packs.map((p) => (
        <Card key={p.id} onPress={() => setPackId(p.id)} selected={packId === p.id}>
          <Text style={styles.cardTitle}>{p.name}</Text>
          <Text style={styles.meta}>{p.description || p.id}</Text>
          {p.scenarios?.length ? (
            <Text style={styles.meta}>{p.scenarios.length} scenarios</Text>
          ) : null}
        </Card>
      ))}

      <Button title={busy ? "Running…" : "Run mystery shop"} onPress={onRun} disabled={busy || !packId || !botId} />
      <Button title="Save as Baseline" onPress={onBaseline} disabled={busy || !packId} variant="ghost" />

      <Card>
        <Text style={styles.section}>Regression · Baseline vs Re-check</Text>
        <View style={styles.compareRow}>
          <View style={styles.compareCol}>
            <Badge label="Baseline" tone="muted" />
            <Text style={styles.bigPct}>{basePct != null ? `${Math.round(basePct)}%` : "—"}</Text>
            <Text style={styles.meta}>before</Text>
          </View>
          <View style={styles.compareCol}>
            <Badge label="Re-check" tone="gold" />
            <Text style={styles.bigPct}>{recheckPct != null ? `${Math.round(recheckPct)}%` : "—"}</Text>
            <Text style={styles.meta}>after</Text>
          </View>
          <View style={styles.compareCol}>
            <Badge
              label="Δ"
              tone={delta == null ? "muted" : delta >= 0 ? "ok" : "danger"}
            />
            <Text style={styles.bigPct}>
              {delta == null ? "—" : `${delta > 0 ? "+" : ""}${delta}%`}
            </Text>
            <Text style={styles.meta}>change</Text>
          </View>
        </View>
        {runId ? <Text style={styles.meta}>Last run: {runId}</Text> : null}
        {lastScores
          ? Object.entries(lastScores)
              .filter(([k]) => k.toLowerCase() !== "overall")
              .map(([k, v]) => <ScoreBar key={k} label={k} value={Number(v)} />)
          : null}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { color: colors.text, fontWeight: type.mediumWeight, fontSize: 15, marginTop: spacing.md, marginBottom: spacing.xs, letterSpacing: type.letterSpacing },
  cardTitle: { color: colors.text, fontWeight: type.labelWeight, fontSize: 15, letterSpacing: type.letterSpacing },
  meta: { color: colors.muted, fontSize: 12, marginTop: 2, fontWeight: type.bodyWeight, letterSpacing: type.letterSpacing },
  compareRow: { flexDirection: "row", justifyContent: "space-between", marginTop: spacing.sm, marginBottom: spacing.md },
  compareCol: { flex: 1, alignItems: "center", gap: 6 },
  bigPct: { color: colors.text, fontSize: 28, fontWeight: type.mediumWeight, letterSpacing: type.letterSpacing },
});
