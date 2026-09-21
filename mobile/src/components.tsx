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

/** Large light editorial wordmark */
export function Hero({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <View style={styles.hero}>
      <Text style={styles.heroTitle}>{title}</Text>
      <View style={styles.heroRule} />
      {subtitle ? <Text style={styles.heroSub}>{subtitle}</Text> : null}
    </View>
  );
}

export function Title({ children }: { children: React.ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function Subtitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.subtitle}>{children}</Text>;
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionLabel}>{children}</Text>;
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
      <Pressable onPress={onPress} style={({ pressed }) => [{ opacity: pressed ? 0.75 : 1 }]}>
        {inner}
      </Pressable>
    );
  }
  return inner;
}

/** Slim outline status — gold/muted hairline, never chubby filled pills */
export function Badge({
  label,
  tone = "gold",
}: {
  label: string;
  tone?: "gold" | "warn" | "ok" | "danger" | "muted";
}) {
  const border =
    tone === "danger"
      ? colors.danger
      : tone === "muted"
        ? colors.border
        : colors.goldDim;
  const fg =
    tone === "danger"
      ? colors.danger
      : tone === "muted"
        ? colors.muted
        : colors.gold;
  return (
    <View style={[styles.badge, { borderColor: border }]}>
      <Text style={[styles.badgeText, { color: fg }]}>{label.toUpperCase()}</Text>
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
  variant?: "primary" | "ghost" | "text";
}) {
  if (variant === "text") {
    return (
      <Pressable
        onPress={onPress}
        disabled={disabled}
        style={({ pressed }) => [styles.btnTextOnly, (disabled || pressed) && { opacity: 0.5 }]}
      >
        <Text style={styles.btnTextOnlyLabel}>{title.toUpperCase()}</Text>
      </Pressable>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.btn,
        variant === "ghost" && styles.btnGhost,
        (disabled || pressed) && { opacity: 0.55 },
      ]}
    >
      <Text style={[styles.btnText, variant === "ghost" && styles.btnTextGhost]}>
        {title.toUpperCase()}
      </Text>
    </Pressable>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
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

export function Divider() {
  return <View style={styles.divider} />;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xl * 2,
  },
  hero: {
    marginBottom: spacing.lg,
    paddingTop: spacing.sm,
  },
  heroTitle: {
    color: colors.text,
    fontSize: 36,
    fontWeight: type.titleWeight,
    letterSpacing: type.titleTracking + 2,
    lineHeight: 44,
  },
  heroRule: {
    width: 48,
    height: StyleSheet.hairlineWidth * 2,
    backgroundColor: colors.gold,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  heroSub: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    lineHeight: 22,
    maxWidth: 320,
  },
  title: {
    color: colors.text,
    fontSize: 26,
    fontWeight: type.titleWeight,
    letterSpacing: type.titleTracking,
    marginBottom: spacing.xs,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 14,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.lg,
    lineHeight: 22,
  },
  sectionLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: type.labelWeight,
    letterSpacing: type.labelTracking,
    textTransform: "uppercase",
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 4,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  cardSelected: {
    borderColor: colors.goldDim,
    backgroundColor: colors.surfaceAlt,
  },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 2,
    borderWidth: StyleSheet.hairlineWidth,
    backgroundColor: "transparent",
  },
  badgeText: {
    fontSize: 10,
    fontWeight: type.labelWeight,
    letterSpacing: type.labelTracking,
  },
  btn: {
    backgroundColor: colors.gold,
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 2,
    alignItems: "center",
    marginTop: spacing.sm,
  },
  btnGhost: {
    backgroundColor: "transparent",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.goldDim,
  },
  btnText: {
    color: colors.black,
    fontWeight: type.labelWeight,
    fontSize: 12,
    letterSpacing: type.labelTracking + 0.4,
  },
  btnTextGhost: { color: colors.gold },
  btnTextOnly: {
    alignSelf: "flex-start",
    paddingVertical: spacing.sm,
    marginTop: 4,
  },
  btnTextOnlyLabel: {
    color: colors.gold,
    fontSize: 11,
    fontWeight: type.labelWeight,
    letterSpacing: type.labelTracking,
  },
  loading: { alignItems: "center", gap: 12, paddingVertical: spacing.lg },
  muted: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  error: {
    borderColor: colors.danger,
    borderWidth: StyleSheet.hairlineWidth,
    padding: spacing.md,
    borderRadius: 2,
    marginBottom: spacing.md,
    backgroundColor: colors.bg,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  rowBetween: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  scoreNum: {
    color: colors.text,
    fontWeight: type.labelWeight,
    letterSpacing: type.letterSpacing,
    fontSize: 13,
  },
  barTrack: {
    height: StyleSheet.hairlineWidth * 2,
    backgroundColor: colors.border,
    overflow: "hidden",
  },
  barFill: { height: StyleSheet.hairlineWidth * 2, backgroundColor: colors.gold },
  divider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: colors.border,
    marginVertical: spacing.md,
  },
});
