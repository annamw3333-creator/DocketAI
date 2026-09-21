import React, { useCallback, useState } from "react";
import { Text, View, StyleSheet, Linking } from "react-native";
import { useFocusEffect } from "expo-router";
import * as LinkingExpo from "expo-linking";
import {
  Screen,
  Title,
  Subtitle,
  Card,
  Button,
  Badge,
  Loading,
  ErrorBox,
  SectionLabel,
} from "@/src/components";
import {
  fetchBillingPlans,
  createCheckoutSession,
  type BillingPlan,
  type FoundingStatus,
} from "@/src/api";
import { hasAdminCredentials } from "@/src/settings";
import { colors, spacing, type } from "@/src/theme";

function priceLabel(plan: BillingPlan): string {
  const p = plan.pricing_display || {};
  if (plan.id === "founding") {
    return `${p.intro || "$10"} then ${p.then || "$29.99/mo"}`;
  }
  if (plan.id === "professional") {
    return `${p.intro || "$10"} → ${p.months_2_to_4 || "$29.99"} → ${p.then || "$99/mo"}`;
  }
  return String(p.then || "$189/mo");
}

function bulletsFor(plan: BillingPlan): string[] {
  if (plan.feature_bullets?.length) return plan.feature_bullets;
  const e = plan.entitlements;
  const lines: string[] = [];
  if (e.max_bots === -1) lines.push("Unlimited bots");
  else lines.push(`${e.max_bots} bots`);
  if (e.mystery_runs_per_month === -1) lines.push("Unlimited mystery runs");
  else lines.push(`${e.mystery_runs_per_month} mystery runs / month`);
  if (e.max_embeds === -1) lines.push("Unlimited embeds");
  else lines.push(`${e.max_embeds} embed${e.max_embeds === 1 ? "" : "s"}`);
  if (e.theme_studio) lines.push("Theme Studio");
  if (e.brand_to_bot) lines.push("Brand-to-Bot");
  if (e.custom_packs) lines.push("Custom packs");
  if (e.multi_seat) lines.push("Multi-seat");
  if (e.priority_support) lines.push("Priority support");
  if (e.founder_rate) lines.push("Founder rate for life");
  return lines;
}

export default function PlansScreen() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [founding, setFounding] = useState<FoundingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [data, admin] = await Promise.all([
        fetchBillingPlans(),
        hasAdminCredentials(),
      ]);
      setPlans(data.plans || []);
      setFounding(data.founding || null);
      setIsAdmin(admin);
    } catch (e: any) {
      setError(e?.message || "Failed to load plans");
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onSubscribe = async (tier: string) => {
    setBusy(tier);
    setError("");
    try {
      const success = LinkingExpo.createURL("plans?checkout=success");
      const cancel = LinkingExpo.createURL("plans?checkout=cancel");
      const session = await createCheckoutSession({
        tier,
        success_url: success,
        cancel_url: cancel,
      });
      if (!session?.url) throw new Error("No checkout URL returned");
      await Linking.openURL(session.url);
    } catch (e: any) {
      setError(e?.message || "Checkout failed");
    } finally {
      setBusy(null);
    }
  };

  const foundingRemaining = founding?.remaining ?? 10;
  const foundingSoldOut = foundingRemaining <= 0;

  return (
    <Screen>
      <Title>Plans</Title>
      <Subtitle>Choose a DocketAI subscription. Founding Partner is limited to 10 seats.</Subtitle>

      {isAdmin ? (
        <Card>
          <Badge label="Admin" tone="ok" />
          <Text style={styles.adminNote}>
            Subscription marked as Admin — paywall bypassed. Manage founding from Settings → Admin.
          </Text>
        </Card>
      ) : null}

      {loading ? <Loading label="Loading plans…" /> : null}
      {error ? <ErrorBox message={error} /> : null}

      {!loading &&
        plans.map((plan) => {
          const soldOut = plan.id === "founding" && foundingSoldOut;
          const highlight = plan.id === "founding" && !soldOut;
          return (
            <View key={plan.id}>
              <SectionLabel>{plan.name}</SectionLabel>
              <Card selected={highlight}>
                <View style={styles.row}>
                  <Text style={styles.planName}>{plan.name}</Text>
                  {plan.id === "founding" ? (
                    <Badge
                      label={
                        soldOut
                          ? "Sold out"
                          : `${foundingRemaining} of ${founding?.limit ?? 10} left`
                      }
                      tone={soldOut ? "danger" : "gold"}
                    />
                  ) : null}
                </View>
                <Text style={styles.price}>{priceLabel(plan)}</Text>
                {plan.tagline ? <Text style={styles.tagline}>{plan.tagline}</Text> : null}
                {bulletsFor(plan).map((b) => (
                  <Text key={b} style={styles.bullet}>
                    · {b}
                  </Text>
                ))}
                {soldOut ? (
                  <Text style={styles.soldOut}>Founding Partner seats are gone.</Text>
                ) : (
                  <Button
                    title={busy === plan.id ? "Opening…" : "Subscribe"}
                    onPress={() => onSubscribe(plan.id)}
                    disabled={busy !== null || isAdmin}
                  />
                )}
              </Card>
            </View>
          );
        })}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: spacing.sm,
    gap: spacing.sm,
  },
  planName: {
    color: colors.text,
    fontSize: 18,
    fontWeight: type.titleWeight,
    letterSpacing: type.titleTracking,
    flex: 1,
  },
  price: {
    color: colors.gold,
    fontSize: 15,
    fontWeight: type.labelWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.xs,
  },
  tagline: {
    color: colors.muted,
    fontSize: 13,
    marginBottom: spacing.sm,
    letterSpacing: type.letterSpacing,
  },
  bullet: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 22,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  soldOut: {
    color: colors.danger,
    marginTop: spacing.md,
    fontSize: 13,
    letterSpacing: type.letterSpacing,
  },
  adminNote: {
    color: colors.muted,
    marginTop: spacing.sm,
    fontSize: 13,
    lineHeight: 20,
    letterSpacing: type.letterSpacing,
  },
});
