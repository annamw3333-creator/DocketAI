import React, { useCallback, useState } from "react";
import { Text, StyleSheet } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen, Title, Subtitle, Card, Loading, ErrorBox, Badge, ScoreBar, Button } from "@/src/components";
import { fetchRuns, RunSummary } from "@/src/api";
import { colors, spacing, type } from "@/src/theme";

export default function ResultsScreen() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRuns(40);
      setRuns(res.runs || []);
    } catch (e: any) {
      setError(e?.message || "Failed to load runs");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <Screen>
      <Title>Results</Title>
      <Subtitle>Recent mystery-shop runs and scorecards from Docket Desk.</Subtitle>
      <Button title="Refresh" onPress={load} variant="ghost" />
      {error ? <ErrorBox message={error} /> : null}
      {loading ? <Loading /> : null}
      {!loading && !error && runs.length === 0 ? (
        <Card>
          <Text style={styles.empty}>No runs yet. Start one from the Run tab.</Text>
        </Card>
      ) : null}
      {runs.map((r) => {
        const overall = r.scores?.overall ?? r.scores?.Overall;
        return (
          <Card key={r.id}>
            <Text style={styles.title}>{r.pack_id}</Text>
            <Text style={styles.meta}>
              bot {r.bot_id} · {r.created_at || "—"}
            </Text>
            {overall != null ? (
              <Badge label={`Overall ${Math.round(Number(overall))}%`} tone="gold" />
            ) : (
              <Badge label="No scores" tone="muted" />
            )}
            {r.scores
              ? Object.entries(r.scores)
                  .filter(([k]) => k.toLowerCase() !== "overall")
                  .slice(0, 6)
                  .map(([k, v]) => <ScoreBar key={k} label={k} value={Number(v)} />)
              : null}
            <Text style={styles.id}>{r.id}</Text>
          </Card>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontWeight: type.mediumWeight, fontSize: 16, marginBottom: 2, letterSpacing: type.letterSpacing },
  meta: { color: colors.muted, fontSize: 12, marginBottom: spacing.sm, fontWeight: type.bodyWeight, letterSpacing: type.letterSpacing },
  empty: { color: colors.muted, fontWeight: type.bodyWeight, letterSpacing: type.letterSpacing },
  id: { color: colors.muted, fontSize: 10, marginTop: spacing.sm, fontFamily: "monospace", letterSpacing: type.letterSpacing },
});
