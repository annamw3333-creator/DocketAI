import React, { useCallback, useEffect, useState } from "react";
import { Text, StyleSheet, View } from "react-native";
import { useFocusEffect, useLocalSearchParams } from "expo-router";
import * as Clipboard from "expo-clipboard";
import {
  Screen,
  Title,
  Subtitle,
  Card,
  Loading,
  ErrorBox,
  Badge,
  ScoreBar,
  Button,
  SectionLabel,
  Divider,
} from "@/src/components";
import { fetchRuns, fetchRun, fetchBaseline, RunSummary, ScenarioResult } from "@/src/api";
import { PERSONAS, ATTACKS } from "@/src/library";
import { colors, spacing, type } from "@/src/theme";

function overallOf(s?: Record<string, number> | null): number | null {
  if (!s) return null;
  const v = s.overall ?? (s as any).Overall;
  return typeof v === "number" ? v : null;
}


function lensLabel(run: RunSummary): string | null {
  const lens = run.lens || run.meta;
  const pid = run.persona_id ?? lens?.persona_id;
  const aid = run.attack_id ?? lens?.attack_id;
  const pl =
    (lens as any)?.persona_label ||
    (pid ? PERSONAS.find((x) => x.id === pid)?.label : null);
  const al =
    (lens as any)?.attack_label ||
    (aid ? ATTACKS.find((x) => x.id === aid)?.label : null);
  if (!pl && !al) return null;
  return `${pl || "Any persona"}${al ? ` × ${al}` : ""}`;
}

function severityTone(sev?: string): "gold" | "danger" | "muted" | "ok" {
  if (sev === "high") return "danger";
  if (sev === "medium") return "gold";
  if (sev === "low") return "muted";
  return "ok";
}

export default function ResultsScreen() {
  const params = useLocalSearchParams<{ runId?: string }>();
  const focusRunId =
    typeof params.runId === "string"
      ? params.runId
      : Array.isArray(params.runId)
        ? params.runId[0]
        : undefined;

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunSummary | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [baseline, setBaseline] = useState<Record<string, number> | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [openScenario, setOpenScenario] = useState<string | null>(null);

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

  useEffect(() => {
    if (focusRunId) setExpandedId(focusRunId);
  }, [focusRunId]);

  useEffect(() => {
    let alive = true;
    (async () => {
      if (!expandedId) {
        setDetail(null);
        setBaseline(null);
        setOpenScenario(null);
        return;
      }
      setDetailLoading(true);
      try {
        const full = await fetchRun(expandedId);
        if (!alive) return;
        setDetail(full);
        try {
          const bl = await fetchBaseline(full.pack_id);
          if (!alive) return;
          setBaseline(bl.baseline || bl.scores || null);
        } catch {
          if (alive) setBaseline(null);
        }
      } catch (e: any) {
        if (alive) setError(e?.message || "Failed to load run detail");
      } finally {
        if (alive) setDetailLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [expandedId]);

  const flashCopied = (key: string) => {
    setCopied(key);
    setTimeout(() => setCopied((c) => (c === key ? null : c)), 1500);
  };

  const copyOne = async (text: string, key: string) => {
    await Clipboard.setStringAsync(text);
    flashCopied(key);
  };

  const copyAllPatches = async (patches: string[]) => {
    if (!patches.length) return;
    await Clipboard.setStringAsync(patches.map((p, i) => `${i + 1}. ${p}`).join("\n\n"));
    flashCopied("all");
  };

  const toggle = (id: string) => {
    setExpandedId((cur) => (cur === id ? null : id));
  };

  const renderDetail = (run: RunSummary) => {
    const patches = run.patches || [];
    const scenarios = run.scenarios || [];
    const o = overallOf(run.scores);
    const basePct = overallOf(baseline);
    const delta = o != null && basePct != null ? Math.round(o - basePct) : null;
    const dims = run.scores
      ? Object.entries(run.scores).filter(([k]) => k.toLowerCase() !== "overall")
      : [];

    const lens = lensLabel(run);
    const failures = (run as any).failures as { scenario_id?: string; reason?: string }[] | undefined;
    const failedScenarios = (run.scenarios || []).filter((s) => s.passed === false);

    return (
      <View style={styles.detail}>
        <Divider />

        {lens ? (
          <>
            <SectionLabel>Lens used</SectionLabel>
            <Card>
              <Badge label={lens} tone="gold" />
              {(run.lens?.mode || run.meta?.mode) ? (
                <Text style={styles.meta}>Mode · {String(run.lens?.mode || run.meta?.mode)}</Text>
              ) : null}
            </Card>
          </>
        ) : (
          <>
            <SectionLabel>Lens used</SectionLabel>
            <Text style={styles.meta}>No persona / attack lens — full pack.</Text>
          </>
        )}

        <SectionLabel>Overall</SectionLabel>
        <View style={styles.compareRow}>
          <View style={styles.compareCol}>
            <Text style={styles.compareLabel}>SCORE</Text>
            <Text style={styles.bigPct}>{o != null ? `${Math.round(o)}%` : "—"}</Text>
          </View>
          <View style={styles.compareCol}>
            <Text style={styles.compareLabel}>BASELINE</Text>
            <Text style={styles.bigPct}>{basePct != null ? `${Math.round(basePct)}%` : "—"}</Text>
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

        <SectionLabel>Dimensions</SectionLabel>
        {dims.map(([k, v]) => (
          <ScoreBar key={k} label={k.replace(/_/g, " ")} value={Number(v)} />
        ))}

        <SectionLabel>Suggested fixes</SectionLabel>
        {patches.length === 0 ? (
          <Text style={styles.meta}>No patches for this run.</Text>
        ) : (
          <>
            <Button
              title={copied === "all" ? "Copied all" : "Copy all"}
              onPress={() => copyAllPatches(patches)}
              variant="ghost"
            />
            {patches.map((p, i) => (
              <Card key={`p-${i}`}>
                <Text style={styles.patchText}>{p}</Text>
                <Button
                  title={copied === `p-${i}` ? "Copied" : "Copy"}
                  onPress={() => copyOne(p, `p-${i}`)}
                  variant="text"
                />
              </Card>
            ))}
          </>
        )}

        {(failedScenarios.length > 0 || (failures && failures.length > 0)) ? (
          <>
            <SectionLabel>Failures ({failedScenarios.length || failures?.length || 0})</SectionLabel>
            {failedScenarios.length
              ? failedScenarios.map((sc) => (
                  <Card
                    key={`fail-${sc.scenario_id}`}
                    onPress={() => setOpenScenario(openScenario === sc.scenario_id ? null : sc.scenario_id)}
                  >
                    <View style={styles.rowBetween}>
                      <Text style={styles.cardTitle}>{sc.name || sc.scenario_id}</Text>
                      <Badge label={sc.severity || "fail"} tone={severityTone(sc.severity)} />
                    </View>
                    {(sc.reasons || []).slice(0, 2).map((r, i) => (
                      <Text key={i} style={styles.meta}>· {r}</Text>
                    ))}
                  </Card>
                ))
              : (failures || []).map((f, i) => (
                  <Card key={`f-${i}`}>
                    <Text style={styles.cardTitle}>{f.scenario_id || "scenario"}</Text>
                    <Text style={styles.meta}>{f.reason}</Text>
                  </Card>
                ))}
          </>
        ) : null}

        <SectionLabel>Scenarios</SectionLabel>
        {scenarios.length === 0 ? (
          <Text style={styles.meta}>No scenario detail stored for this run.</Text>
        ) : (
          scenarios.map((sc: ScenarioResult) => {
            const open = openScenario === sc.scenario_id;
            return (
              <Card
                key={sc.scenario_id}
                onPress={() => setOpenScenario(open ? null : sc.scenario_id)}
              >
                <View style={styles.rowBetween}>
                  <Text style={styles.cardTitle}>{sc.name || sc.scenario_id}</Text>
                  <Badge label={sc.passed ? "Pass" : "Fail"} tone={sc.passed ? "ok" : "danger"} />
                </View>
                <View style={styles.badgeRow}>
                  <Badge
                    label={`${Math.round(Number(sc.overall ?? overallOf(sc.scores) ?? 0))}%`}
                    tone="gold"
                  />
                  {sc.severity && sc.severity !== "none" ? (
                    <Badge label={sc.severity} tone={severityTone(sc.severity)} />
                  ) : null}
                </View>
                {open ? (
                  <View style={styles.scenarioBody}>
                    {(sc.reasons || []).map((r, i) => (
                      <Text key={i} style={styles.meta}>
                        · {r}
                      </Text>
                    ))}
                    {(sc.suggested_fixes || []).length > 0 ? (
                      <>
                        <Text style={styles.fixLabel}>Fixes</Text>
                        {sc.suggested_fixes!.map((f, i) => (
                          <View key={i} style={{ marginBottom: 6 }}>
                            <Text style={styles.meta}>· {f}</Text>
                            <Button
                              title={copied === `sf-${sc.scenario_id}-${i}` ? "Copied" : "Copy"}
                              onPress={() => copyOne(f, `sf-${sc.scenario_id}-${i}`)}
                              variant="text"
                            />
                          </View>
                        ))}
                        <Button
                          title={
                            copied === `sf-all-${sc.scenario_id}` ? "Copied fixes" : "Copy all fixes"
                          }
                          onPress={async () => {
                            const fixes = sc.suggested_fixes || [];
                            if (!fixes.length) return;
                            await Clipboard.setStringAsync(
                              fixes.map((f, i) => `${i + 1}. ${f}`).join("\n\n")
                            );
                            flashCopied(`sf-all-${sc.scenario_id}`);
                          }}
                          variant="ghost"
                        />
                      </>
                    ) : null}
                    {sc.user ? (
                      <>
                        <Text style={styles.fixLabel}>User</Text>
                        <Text style={styles.mono}>{sc.user}</Text>
                      </>
                    ) : null}
                    {sc.assistant ? (
                      <>
                        <Text style={styles.fixLabel}>Assistant</Text>
                        <Text style={styles.mono}>{sc.assistant}</Text>
                      </>
                    ) : null}
                    {sc.scores
                      ? Object.entries(sc.scores)
                          .filter(([k]) => k.toLowerCase() !== "overall")
                          .map(([k, v]) => (
                            <ScoreBar key={k} label={k.replace(/_/g, " ")} value={Number(v)} />
                          ))
                      : null}
                  </View>
                ) : (
                  <Text style={styles.tapHint}>Tap for detail</Text>
                )}
              </Card>
            );
          })
        )}
      </View>
    );
  };

  return (
    <Screen>
      <Title>Results</Title>
      <Subtitle>Scorecards, scenario verdicts, and copyable prompt fixes.</Subtitle>
      <Button title="Refresh" onPress={load} variant="text" />
      {error ? <ErrorBox message={error} /> : null}
      {loading ? <Loading /> : null}
      {!loading && !error && runs.length === 0 ? (
        <Card>
          <Text style={styles.empty}>No runs yet. Start from Run.</Text>
        </Card>
      ) : null}
      {!loading && runs.length > 0 ? <SectionLabel>History</SectionLabel> : null}
      {runs.map((r) => {
        const overall = overallOf(r.scores);
        const isOpen = expandedId === r.id;
        return (
          <Card key={r.id} selected={isOpen}>
            <Card onPress={() => toggle(r.id)} selected={isOpen}>
              <Text style={styles.cardTitle}>{r.pack_id}</Text>
              <Text style={styles.meta}>
                {r.bot_id} · {r.created_at || "—"}
              </Text>
              {lensLabel(r) ? (
                <Badge label={lensLabel(r)!} tone="gold" />
              ) : null}
              {overall != null ? (
                <Badge label={`${Math.round(Number(overall))}% overall`} tone="gold" />
              ) : (
                <Badge label="No scores" tone="muted" />
              )}
              {(r.patches?.length || 0) > 0 ? (
                <Text style={styles.meta}>
                  {r.patches!.length} suggested fix{r.patches!.length === 1 ? "" : "es"}
                </Text>
              ) : null}
              <Text style={styles.id}>{r.id}</Text>
              <Text style={styles.tapHint}>{isOpen ? "Tap to collapse" : "Tap to expand"}</Text>
            </Card>
            {isOpen ? (
              detailLoading && detail?.id !== r.id ? (
                <Loading label="Loading detail…" />
              ) : detail && detail.id === r.id ? (
                renderDetail(detail)
              ) : r.patches || r.scenarios ? (
                renderDetail(r)
              ) : (
                <Loading label="Loading detail…" />
              )
            ) : null}
          </Card>
        );
      })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  cardTitle: {
    color: colors.text,
    fontWeight: type.bodyWeight,
    fontSize: 16,
    marginBottom: 4,
    letterSpacing: type.letterSpacing,
  },
  meta: {
    color: colors.muted,
    fontSize: 12,
    marginBottom: spacing.sm,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    lineHeight: 18,
  },
  empty: {
    color: colors.muted,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  id: {
    color: colors.muted,
    fontSize: 10,
    marginTop: spacing.sm,
    fontFamily: "monospace",
    letterSpacing: 0.4,
  },
  detail: { marginTop: spacing.sm },
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
    fontSize: 24,
    fontWeight: type.titleWeight,
    letterSpacing: type.letterSpacing,
  },
  patchText: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.xs,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  badgeRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 6 },
  scenarioBody: { marginTop: spacing.sm },
  fixLabel: {
    color: colors.gold,
    fontSize: 11,
    letterSpacing: type.labelTracking,
    fontWeight: type.labelWeight,
    marginTop: spacing.sm,
    marginBottom: 4,
    textTransform: "uppercase",
  },
  mono: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    fontFamily: "monospace",
    marginBottom: spacing.sm,
  },
  tapHint: {
    color: colors.muted,
    fontSize: 11,
    letterSpacing: type.letterSpacing,
    marginTop: 4,
  },
});
