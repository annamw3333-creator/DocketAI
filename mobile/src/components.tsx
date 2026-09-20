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
import { colors, spacing, type } from "./theme";

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

export function Badge({
  label,
  tone = "gold",
}: {
  label: string;
  tone?: "gold" | "warn" | "ok" | "danger" | "muted";
}) {
  const bg =
    tone === "warn"
      ? colors.warn
      : tone === "ok"
        ? colors.ok
        : tone === "danger"
          ? colors.danger
          : tone === "muted"
            ? colors.border
            : colors.gold;
  const fg = tone === "muted" ? colors.text : colors.black;
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
      <ActivityIndicator color={colors.gold} />
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
  title: {
    color: colors.text,
    fontSize: 28,
    fontWeight: type.titleWeight,
    letterSpacing: type.letterSpacing + 0.4,
    marginBottom: 6,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.md,
    lineHeight: 22,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 4,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  cardSelected: {
    borderColor: colors.gold,
    backgroundColor: colors.surfaceAlt,
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 2,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: type.mediumWeight,
    letterSpacing: type.letterSpacing,
  },
  btn: {
    backgroundColor: colors.gold,
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderRadius: 2,
    alignItems: "center",
    marginTop: spacing.sm,
  },
  btnGhost: {
    backgroundColor: "transparent",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  btnText: {
    color: colors.black,
    fontWeight: type.mediumWeight,
    fontSize: 14,
    letterSpacing: type.letterSpacing + 0.4,
  },
  btnTextGhost: { color: colors.text },
  loading: { alignItems: "center", gap: 10, padding: spacing.lg },
  muted: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  error: {
    backgroundColor: "#1A0A0A",
    borderColor: colors.danger,
    borderWidth: StyleSheet.hairlineWidth,
    padding: spacing.md,
    borderRadius: 4,
    marginBottom: spacing.sm,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  rowBetween: { flexDirection: "row", justifyContent: "space-between", marginBottom: 4 },
  scoreNum: {
    color: colors.gold,
    fontWeight: type.mediumWeight,
    letterSpacing: type.letterSpacing,
  },
  barTrack: {
    height: 2,
    backgroundColor: colors.border,
    borderRadius: 0,
    overflow: "hidden",
  },
  barFill: { height: 2, backgroundColor: colors.gold, borderRadius: 0 },
});
