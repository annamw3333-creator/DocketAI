import React, { useCallback, useState } from "react";
import { Text, View, StyleSheet } from "react-native";
import { useFocusEffect, router } from "expo-router";
import {
  Screen,
  Title,
  Subtitle,
  Card,
  Button,
  Loading,
  ErrorBox,
  ScoreBar,
  SectionLabel,
  Badge,
} from "@/src/components";
import { fetchBots, fetchPacks, runMysteryShop, setBaseline, fetchBaseline, Pack } from "@/src/api";
import { PERSONAS, ATTACKS, PersonaId, AttackId } from "@/src/library";
import { colors, spacing, type } from "@/src/theme";

type Step = 1 | 2 | 3 | 4;

const STEP_LABELS: Record<Step, string> = {
  1: "Bot",
  2: "Pack",
  3: "Focus",
  4: "Run",
};

export default function RunScreen() {
  const [step, setStep] = useState<Step>(1);
  const [packs, setPacks] = useState<Pack[]>([]);
  const [bots, setBots] = useState<{ id: string; name: string }[]>([]);
  const [packId, setPackId] = useState<string | null>(null);
  const [botId, setBotId] = useState<string | null>(null);
  const [persona, setPersona] = useState<PersonaId | null>(null);
  const [attack, setAttack] = useState<AttackId | null>(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastScores, setLastScores] = useState<Record<string, number> | null>(null);
  const [baseline, setBaselineScores] = useState<Record<string, number> | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [patchCount, setPatchCount] = useState(0);
  const [scenarioCount, setScenarioCount] = useState<number | null>(null);
  const [lensMode, setLensMode] = useState<string | null>(null);

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
    setProgress("Contacting desk…");
    try {
      setProgress("Running mystery-shop scenarios…");
      const res = await runMysteryShop(botId, packId, { persona_id: persona, attack_id: attack });
      setLastScores(res.scores || null);
      setRunId(res.run_id);
      setPatchCount((res.patches || []).length);
      setScenarioCount(res.scenario_count ?? (res.scenarios || []).length ?? null);
      setLensMode(res.lens?.mode || (persona || attack ? "lens" : "full_pack"));
      setProgress("Comparing baseline…");
      try {
        const bl = await fetchBaseline(packId);
        setBaselineScores(bl.baseline || bl.scores || null);
      } catch {
        setBaselineScores(null);
      }
      setProgress("Done");
    } catch (e: any) {
      setError(e?.message || "Run failed");
      setProgress(null);
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

  const botName = bots.find((b) => b.id === botId)?.name;
  const packName = packs.find((p) => p.id === packId)?.name;
  const personaLabel = persona ? PERSONAS.find((p) => p.id === persona)?.label : null;
  const attackLabel = attack ? ATTACKS.find((a) => a.id === attack)?.label : null;

  return (
    <Screen>
      <Title>Run</Title>
      <Subtitle>Select bot → pack → optional focus → mystery-shop.</Subtitle>

      <View style={styles.steps}>
        {([1, 2, 3, 4] as Step[]).map((s) => (
          <View key={s} style={styles.stepItem}>
            <Text style={[styles.stepNum, step === s && styles.stepNumActive]}>{s}</Text>
            <Text style={[styles.stepLabel, step === s && styles.stepLabelActive]}>
              {STEP_LABELS[s]}
            </Text>
          </View>
        ))}
      </View>

      {error ? <ErrorBox message={error} /> : null}

      {step === 1 ? (
        <>
          <SectionLabel>1 · Select or create bot</SectionLabel>
          <Button title="Build bot from brand" onPress={() => router.push("/build")} variant="ghost" />
          {bots.length === 0 && !error ? <Loading /> : null}
          {bots.map((b) => (
            <Card key={b.id} onPress={() => setBotId(b.id)} selected={botId === b.id}>
              <Text style={styles.cardTitle}>{b.name}</Text>
              <Text style={styles.meta}>{b.id}</Text>
            </Card>
          ))}
          <Button title="Next · Pack" onPress={() => setStep(2)} disabled={!botId} />
        </>
      ) : null}

      {step === 2 ? (
        <>
          <SectionLabel>2 · Pack</SectionLabel>
          <Text style={styles.meta}>Bot · {botName || botId}</Text>
          {packs.map((p) => (
            <Card key={p.id} onPress={() => setPackId(p.id)} selected={packId === p.id}>
              <Text style={styles.cardTitle}>{p.name}</Text>
              <Text style={styles.meta}>{p.description || p.id}</Text>
              {p.scenarios?.length ? (
                <Text style={styles.meta}>{p.scenarios.length} scenarios</Text>
              ) : null}
            </Card>
          ))}
          <Button title="Back" onPress={() => setStep(1)} variant="text" />
          <Button title="Next · Focus" onPress={() => setStep(3)} disabled={!packId} />
        </>
      ) : null}

      {step === 3 ? (
        <>
          <SectionLabel>3 · Persona / attack (optional)</SectionLabel>
          <Text style={styles.meta}>
            Desk filters and rewrites pack scenarios for this lens — not cosmetic.
          </Text>
          <SectionLabel>Persona</SectionLabel>
          {PERSONAS.map((p) => (
            <Card
              key={p.id}
              onPress={() => setPersona(persona === p.id ? null : p.id)}
              selected={persona === p.id}
            >
              <Text style={styles.cardTitle}>{p.label}</Text>
              <Text style={styles.meta}>{p.blurb}</Text>
            </Card>
          ))}
          <SectionLabel>Attack focus</SectionLabel>
          {ATTACKS.map((a) => (
            <Card
              key={a.id}
              onPress={() => setAttack(attack === a.id ? null : a.id)}
              selected={attack === a.id}
            >
              <Text style={styles.cardTitle}>{a.label}</Text>
              <Text style={styles.meta}>{a.blurb}</Text>
            </Card>
          ))}
          <Button title="Back" onPress={() => setStep(2)} variant="text" />
          <Button title="Next · Run" onPress={() => setStep(4)} />
        </>
      ) : null}

      {step === 4 ? (
        <>
          <SectionLabel>4 · Confirm & run</SectionLabel>
          <Card>
            <Text style={styles.meta}>Bot · {botName || botId || "—"}</Text>
            <Text style={styles.meta}>Pack · {packName || packId || "—"}</Text>
            <Text style={styles.meta}>
              Focus · {personaLabel || "Any persona"}
              {attackLabel ? ` × ${attackLabel}` : ""}
            </Text>
            {persona || attack ? (
              <Badge label="Lens shapes scenarios" tone="gold" />
            ) : (
              <Badge label="No lens" tone="muted" />
            )}
          </Card>

          {busy || progress ? (
            <Card>
              <Loading label={progress || "Working…"} />
            </Card>
          ) : null}

          <Button
            title={busy ? "Running…" : "Run mystery shop"}
            onPress={onRun}
            disabled={busy || !packId || !botId}
          />
          <Button title="Back" onPress={() => setStep(3)} variant="text" disabled={busy} />
          <Button
            title="Save as Baseline"
            onPress={onBaseline}
            disabled={busy || !packId}
            variant="text"
          />

          {runId ? (
            <>
              <SectionLabel>Just finished</SectionLabel>
              <Card>
                <View style={styles.compareRow}>
                  <View style={styles.compareCol}>
                    <Text style={styles.compareLabel}>BASELINE</Text>
                    <Text style={styles.bigPct}>
                      {basePct != null ? `${Math.round(basePct)}%` : "—"}
                    </Text>
                  </View>
                  <View style={styles.compareCol}>
                    <Text style={styles.compareLabel}>RE-CHECK</Text>
                    <Text style={styles.bigPct}>
                      {recheckPct != null ? `${Math.round(recheckPct)}%` : "—"}
                    </Text>
                  </View>
                  <View style={styles.compareCol}>
                    <Text style={styles.compareLabel}>DELTA</Text>
                    <Text
                      style={[
                        styles.bigPct,
                        delta != null && delta < 0 ? { color: colors.danger } : null,
                        delta != null && delta >= 0 ? { color: colors.gold } : null,
                      ]}
                    >
                      {delta == null ? "—" : `${delta > 0 ? "+" : ""}${delta}%`}
                    </Text>
                  </View>
                </View>
                {scenarioCount != null ? (
                  <Text style={styles.meta}>{scenarioCount} scenario{scenarioCount === 1 ? "" : "s"} · mode {lensMode || "full_pack"}</Text>
                ) : null}
                {patchCount > 0 ? (
                  <Text style={styles.meta}>{patchCount} suggested fix{patchCount === 1 ? "" : "es"}</Text>
                ) : null}
                {lastScores
                  ? Object.entries(lastScores)
                      .filter(([k]) => k.toLowerCase() !== "overall")
                      .map(([k, v]) => <ScoreBar key={k} label={k} value={Number(v)} />)
                  : null}
              </Card>
              <Button
                title="Open in Results"
                onPress={() =>
                  router.push({ pathname: "/results", params: { runId: runId } })
                }
              />
            </>
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  steps: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.lg,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    paddingBottom: spacing.sm,
  },
  stepItem: { alignItems: "center", flex: 1, gap: 4 },
  stepNum: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: type.labelWeight,
    letterSpacing: type.letterSpacing,
  },
  stepNumActive: { color: colors.gold },
  stepLabel: {
    color: colors.muted,
    fontSize: 10,
    letterSpacing: type.labelTracking,
    fontWeight: type.labelWeight,
    textTransform: "uppercase",
  },
  stepLabelActive: { color: colors.text },
  cardTitle: {
    color: colors.text,
    fontWeight: type.bodyWeight,
    fontSize: 15,
    letterSpacing: type.letterSpacing,
  },
  meta: {
    color: colors.muted,
    fontSize: 12,
    marginTop: 4,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    lineHeight: 18,
  },
  compareRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  compareCol: { flex: 1, alignItems: "flex-start", gap: 8 },
  compareLabel: {
    color: colors.muted,
    fontSize: 10,
    letterSpacing: type.labelTracking,
    fontWeight: type.labelWeight,
  },
  bigPct: {
    color: colors.text,
    fontSize: 28,
    fontWeight: type.titleWeight,
    letterSpacing: type.letterSpacing,
  },
});
