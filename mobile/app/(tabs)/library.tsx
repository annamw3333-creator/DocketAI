import React, { useMemo, useState } from "react";
import { Text, StyleSheet, View, Pressable } from "react-native";
import { Screen, Title, Subtitle, Card, Badge, SectionLabel } from "@/src/components";
import { PERSONAS, ATTACKS, PersonaId, AttackId } from "@/src/library";
import { colors, spacing, type } from "@/src/theme";

type Mode = "personas" | "attacks" | "pair";

export default function LibraryScreen() {
  const [persona, setPersona] = useState<PersonaId | null>(null);
  const [attack, setAttack] = useState<AttackId | null>(null);
  const [mode, setMode] = useState<Mode>("personas");

  const pair = useMemo(() => {
    const p = PERSONAS.find((x) => x.id === persona);
    const a = ATTACKS.find((x) => x.id === attack);
    if (!p || !a) return null;
    return { p, a };
  }, [persona, attack]);

  return (
    <Screen>
      <Title>Library</Title>
      <Subtitle>Browse stress lenses. Pairing on Run actually filters pack scenarios server-side.</Subtitle>

      <View style={styles.modeRow}>
        {(["personas", "attacks", "pair"] as Mode[]).map((m) => (
          <Pressable key={m} onPress={() => setMode(m)} style={styles.modeItem}>
            <Text style={[styles.modeLabel, mode === m && styles.modeActive]}>
              {m.toUpperCase()}
            </Text>
            {mode === m ? <View style={styles.modeUnderline} /> : <View style={styles.modeSpacer} />}
          </Pressable>
        ))}
      </View>

      {mode === "personas"
        ? PERSONAS.map((p) => (
            <Card key={p.id} onPress={() => setPersona(p.id)} selected={persona === p.id}>
              <Text style={styles.cardTitle}>{p.label}</Text>
              <Text style={styles.meta}>{p.blurb}</Text>
            </Card>
          ))
        : null}

      {mode === "attacks"
        ? ATTACKS.map((a) => (
            <Card key={a.id} onPress={() => setAttack(a.id)} selected={attack === a.id}>
              <Text style={styles.cardTitle}>{a.label}</Text>
              <Text style={styles.meta}>{a.blurb}</Text>
            </Card>
          ))
        : null}

      {mode === "pair" ? (
        <Card>
          <SectionLabel>Selected</SectionLabel>
          <View style={styles.badges}>
            <Badge
              label={persona ? PERSONAS.find((p) => p.id === persona)!.label : "Persona"}
              tone={persona ? "gold" : "muted"}
            />
            <Badge
              label={attack ? ATTACKS.find((a) => a.id === attack)!.label : "Attack"}
              tone={attack ? "gold" : "muted"}
            />
          </View>
          {pair ? (
            <Text style={styles.meta}>
              A {pair.p.label.toLowerCase()} customer who {pair.a.label.toLowerCase()}.
            </Text>
          ) : (
            <Text style={styles.meta}>Choose a persona and an attack, then return here.</Text>
          )}
        </Card>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  modeRow: {
    flexDirection: "row",
    gap: spacing.md,
    marginBottom: spacing.lg,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  modeItem: { paddingBottom: spacing.sm },
  modeLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: type.labelWeight,
    letterSpacing: type.labelTracking,
  },
  modeActive: { color: colors.text },
  modeUnderline: {
    marginTop: spacing.sm,
    height: StyleSheet.hairlineWidth * 2,
    backgroundColor: colors.gold,
  },
  modeSpacer: { marginTop: spacing.sm, height: StyleSheet.hairlineWidth * 2 },
  cardTitle: {
    color: colors.text,
    fontWeight: type.bodyWeight,
    fontSize: 15,
    letterSpacing: type.letterSpacing,
  },
  meta: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 6,
    lineHeight: 20,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  badges: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginVertical: spacing.sm },
});
