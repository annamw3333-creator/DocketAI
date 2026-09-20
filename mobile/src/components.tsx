import React from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  ScrollView,
  ViewStyle,
} from "react-native";
import { colors, spacing } from "./theme";

export function Screen({ children, style }: { children: React.ReactNode; style?: ViewStyle }) {
  return (
    <ScrollView
      style={[styles.screen, style]}
      contentContainerStyle={styles.screenContent}
      keyboardShouldPersistTaps="handled"
    >
      {children}
    </ScrollView>
  );
}

export function Title({ children }: { children: React.ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function Subtitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.subtitle}>{children}</Text>;
}

export function Card({
  children,
  onPress,
  selected,
}: {
  children: React.ReactNode;
  onPress?: () => void;
  selected?: boolean;
}) {
  const inner = <View style={[styles.card, selected && styles.cardSelected]}>{children}</View>;
  if (onPress) {
    return (
      <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1 }]}>
        {inner}
      </Pressable>
    );
  }
  return inner;
}

export function Badge({ label, tone = "teal" }: { label: string; tone?: "teal" | "warn" | "ok" | "danger" | "muted" }) {
  const bg =
    tone === "warn"
      ? colors.warn
      : tone === "ok"
        ? colors.ok
        : tone === "danger"
          ? colors.danger
          : tone === "muted"
            ? colors.border
            : colors.teal;
  const fg = tone === "muted" ? colors.text : colors.navy;
  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{label}</Text>
    </View>
  );
}

export function Button({
  title,
  onPress,
  disabled,
  variant = "primary",
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  variant?: "primary" | "ghost";
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.btn,
        variant === "ghost" && styles.btnGhost,
        (disabled || pressed) && { opacity: 0.6 },
      ]}
    >
      <Text style={[styles.btnText, variant === "ghost" && styles.btnTextGhost]}>{title}</Text>
    </Pressable>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <View style={styles.loading}>
      <ActivityIndicator color={colors.teal} />
      <Text style={styles.muted}>{label}</Text>
    </View>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <View style={styles.error}>
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
}

export function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(Number(value) || 0)));
  return (
    <View style={{ marginBottom: spacing.sm }}>
      <View style={styles.rowBetween}>
        <Text style={styles.muted}>{label}</Text>
        <Text style={styles.scoreNum}>{pct}%</Text>
      </View>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
  title: { color: colors.text, fontSize: 26, fontWeight: "700", marginBottom: 4 },
  subtitle: { color: colors.muted, fontSize: 14, marginBottom: spacing.md, lineHeight: 20 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardSelected: { borderColor: colors.teal, backgroundColor: colors.surfaceAlt },
  badge: { alignSelf: "flex-start", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
  badgeText: { fontSize: 11, fontWeight: "700" },
  btn: {
    backgroundColor: colors.teal,
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 12,
    alignItems: "center",
    marginTop: spacing.sm,
  },
  btnGhost: { backgroundColor: "transparent", borderWidth: 1, borderColor: colors.border },
  btnText: { color: colors.navy, fontWeight: "700", fontSize: 15 },
  btnTextGhost: { color: colors.text },
  loading: { alignItems: "center", gap: 10, padding: spacing.lg },
  muted: { color: colors.muted, fontSize: 13 },
  error: {
    backgroundColor: "#3B1A1A",
    borderColor: colors.danger,
    borderWidth: 1,
    padding: spacing.md,
    borderRadius: 12,
    marginBottom: spacing.sm,
  },
  errorText: { color: colors.danger, fontSize: 13 },
  rowBetween: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  scoreNum: { color: colors.teal, fontWeight: "700" },
  barTrack: { height: 8, backgroundColor: colors.border, borderRadius: 4, overflow: "hidden" },
  barFill: { height: 8, backgroundColor: colors.teal, borderRadius: 4 },
});
