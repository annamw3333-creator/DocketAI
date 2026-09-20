import React, { useMemo, useState } from "react";
import { Text, StyleSheet, View } from "react-native";
import { Screen, Title, Subtitle, Card, Badge, Button } from "@/src/components";
import { PERSONAS, ATTACKS, PersonaId, AttackId } from "@/src/library";
import { colors, spacing, type } from "@/src/theme";

export default function LibraryScreen() {
  const [persona, setPersona] = useState<PersonaId | null>(null);
  const [attack, setAttack] = useState<AttackId | null>(null);
  const [mode, setMode] = useState<"personas" | "attacks" | "matrix">("personas");

  const pair = useMemo(() => {
    const p = PERSONAS.find((x) => x.id === persona);
    const a = ATTACKS.find((x) => x.id === attack);
    if (!p || !a) return null;
    return { p, a };
  }, [persona, attack]);

  return (
    <Screen>
      <Title>Library</Title>
      <Subtitle>
        {PERSONAS.length} personas × {ATTACKS.length} attacks — mix for tougher mystery shops.
      </Subtitle>

      <View style={styles.modeRow}>
        <Button title="Personas" onPress={() => setMode("personas")} variant={mode === "personas" ? "primary" : "ghost"} />
        <Button title="Attacks" onPress={() => setMode("attacks")} variant={mode === "attacks" ? "primary" : "ghost"} />
        <Button title="Pair" onPress={() => setMode("matrix")} variant={mode === "matrix" ? "primary" : "ghost"} />
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

      {mode === "matrix" ? (
        <Card>
          <Text style={styles.cardTitle}>Selected pair</Text>
          <View style={styles.badges}>
            <Badge label={persona ? PERSONAS.find((p) => p.id === persona)!.label : "Pick persona"} tone={persona ? "gold" : "muted"} />
            <Badge label={attack ? ATTACKS.find((a) => a.id === attack)!.label : "Pick attack"} tone={attack ? "warn" : "muted"} />
          </View>
          {pair ? (
            <Text style={styles.meta}>
              Scenario stub: a {pair.p.label.toLowerCase()} customer who {pair.a.label.toLowerCase()}. Use this combo when authoring pack scenarios or live probes.
            </Text>
          ) : (
            <Text style={styles.meta}>Select a persona (Personas tab) and an attack (Attacks tab), then return here.</Text>
          )}
          <Text style={styles.hint}>
            Tip: prompt injection + testing rules is a high-risk pair; wants human + emotional pressure tests handoff quality.
          </Text>
        </Card>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  modeRow: { gap: 4, marginBottom: spacing.sm },
  cardTitle: { color: colors.text, fontWeight: type.labelWeight, fontSize: 15, letterSpacing: type.letterSpacing },
  meta: { color: colors.muted, fontSize: 13, marginTop: 4, lineHeight: 20, fontWeight: type.bodyWeight, letterSpacing: type.letterSpacing },
  badges: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginVertical: spacing.sm },
  hint: { color: colors.goldDim, fontSize: 12, marginTop: spacing.md, lineHeight: 18, fontWeight: type.bodyWeight, letterSpacing: type.letterSpacing },
});
