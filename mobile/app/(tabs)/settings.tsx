import React, { useCallback, useState } from "react";
import { TextInput, Text, StyleSheet, View } from "react-native";
import { useFocusEffect, router } from "expo-router";
import { Screen, Title, Subtitle, Card, Button, Badge, ErrorBox, SectionLabel } from "@/src/components";
import {
  DEFAULT_API_URL,
  getApiUrl,
  setApiUrl,
  getAdminEmail,
  setAdminEmail,
  getAdminToken,
  setAdminToken,
  clearAdminCredentials,
  hasAdminCredentials,
} from "@/src/settings";
import {
  fetchHealth,
  fetchAdminMe,
  fetchAdminBillingOverview,
  adjustFoundingClaimed,
  type FoundingStatus,
} from "@/src/api";
import { colors, spacing, type } from "@/src/theme";

export default function SettingsScreen() {
  const [url, setUrl] = useState(DEFAULT_API_URL);
  const [saved, setSaved] = useState(false);
  const [ping, setPing] = useState<"idle" | "ok" | "err">("idle");
  const [msg, setMsg] = useState("");

  const [adminEmail, setAdminEmailState] = useState("");
  const [adminToken, setAdminTokenState] = useState("");
  const [adminSaved, setAdminSaved] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [adminOk, setAdminOk] = useState(false);
  const [adminErr, setAdminErr] = useState("");
  const [founding, setFounding] = useState<FoundingStatus | null>(null);
  const [adjustBusy, setAdjustBusy] = useState(false);

  useFocusEffect(
    useCallback(() => {
      (async () => {
        setUrl(await getApiUrl());
        const email = await getAdminEmail();
        const token = await getAdminToken();
        setAdminEmailState(email);
        setAdminTokenState(token);
        const has = await hasAdminCredentials();
        setShowAdmin(has);
        setSaved(false);
        setAdminSaved(false);
        setPing("idle");
        setAdminOk(false);
        setAdminErr("");
        if (has) {
          try {
            await fetchAdminMe();
            setAdminOk(true);
            const overview = await fetchAdminBillingOverview();
            setFounding(overview.founding);
          } catch (e: any) {
            setAdminErr(e?.message || "Admin auth failed");
            setAdminOk(false);
          }
        }
      })();
    }, [])
  );

  const onSave = async () => {
    await setApiUrl(url);
    setSaved(true);
    setPing("idle");
  };

  const onTest = async () => {
    await setApiUrl(url);
    try {
      const h = await fetchHealth();
      setPing("ok");
      setMsg(`${h.service || "ok"} · ${h.status}`);
    } catch (e: any) {
      setPing("err");
      setMsg(e?.message || "Unreachable");
    }
  };

  const onSaveAdmin = async () => {
    await setAdminEmail(adminEmail);
    await setAdminToken(adminToken);
    const has = Boolean(adminEmail.trim() || adminToken.trim());
    setShowAdmin(has);
    setAdminSaved(true);
    setAdminErr("");
    setAdminOk(false);
    if (!has) {
      setFounding(null);
      return;
    }
    try {
      await fetchAdminMe();
      setAdminOk(true);
      const overview = await fetchAdminBillingOverview();
      setFounding(overview.founding);
    } catch (e: any) {
      setAdminErr(e?.message || "Admin auth failed");
    }
  };

  const onClearAdmin = async () => {
    await clearAdminCredentials();
    setAdminEmailState("");
    setAdminTokenState("");
    setShowAdmin(false);
    setAdminOk(false);
    setFounding(null);
    setAdminSaved(false);
  };

  const onAdjust = async (delta: number) => {
    if (!founding) return;
    setAdjustBusy(true);
    setAdminErr("");
    try {
      const next = Math.max(0, Math.min(10, (founding.claimed || 0) + delta));
      const res = await adjustFoundingClaimed(next);
      setFounding(res.founding);
      if (!res.mutable) {
        setAdminErr(res.message);
      }
    } catch (e: any) {
      setAdminErr(e?.message || "Adjust failed");
    } finally {
      setAdjustBusy(false);
    }
  };

  return (
    <Screen>
      <Title>Settings</Title>
      <Subtitle>Point DocketAI at your Docket Desk API.</Subtitle>

      <SectionLabel>Subscription</SectionLabel>
      <Card>
        <Text style={styles.meta}>View plans, Founding Partner countdown, and subscribe.</Text>
        <Button title="Plans / Subscribe" onPress={() => router.push("/plans")} />
      </Card>

      <SectionLabel>API</SectionLabel>
      <Card>
        <Text style={styles.label}>URL</Text>
        <TextInput
          value={url}
          onChangeText={(t) => {
            setUrl(t);
            setSaved(false);
          }}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder={DEFAULT_API_URL}
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.hint}>
          Emulator → http://10.0.2.2:8080 · Device → http://&lt;lan-ip&gt;:8080
        </Text>
        <Button title="Save" onPress={onSave} />
        <Button title="Test /health" onPress={onTest} variant="text" />
        {saved ? <Badge label="Saved" tone="ok" /> : null}
        {ping === "ok" ? <Badge label={`OK · ${msg}`} tone="ok" /> : null}
        {ping === "err" ? <ErrorBox message={msg} /> : null}
      </Card>

      <SectionLabel>Admin credentials</SectionLabel>
      <Card>
        <Text style={styles.hint}>
          Owner access only. Store allowlisted email and/or ADMIN_TOKEN. Admin panel appears when saved.
        </Text>
        <Text style={styles.label}>Admin email</Text>
        <TextInput
          value={adminEmail}
          onChangeText={(t) => {
            setAdminEmailState(t);
            setAdminSaved(false);
          }}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          placeholder="anna@annabuildsai.com"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Admin token</Text>
        <TextInput
          value={adminToken}
          onChangeText={(t) => {
            setAdminTokenState(t);
            setAdminSaved(false);
          }}
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
          placeholder="X-Docket-Admin-Token"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Button title="Save admin" onPress={onSaveAdmin} />
        <Button title="Clear admin" onPress={onClearAdmin} variant="text" />
        {adminSaved ? <Badge label="Admin saved" tone="ok" /> : null}
      </Card>

      {showAdmin ? (
        <>
          <SectionLabel>Admin</SectionLabel>
          <Card>
            {adminOk ? (
              <>
                <Badge label="Admin · bypass paywall" tone="ok" />
                <Text style={styles.meta}>Subscription: Admin (unlimited entitlements)</Text>
              </>
            ) : (
              <Badge label="Credentials stored · auth pending" tone="warn" />
            )}
            {adminErr ? <ErrorBox message={adminErr} /> : null}
            {founding ? (
              <View style={{ marginTop: spacing.md }}>
                <Text style={styles.label}>Founding Partner</Text>
                <Text style={styles.meta}>
                  {founding.remaining} of {founding.limit} left · claimed {founding.claimed}
                  {founding.stripe_configured ? " · Stripe live" : " · local override"}
                </Text>
                {!founding.stripe_configured ? (
                  <View style={styles.rowBtns}>
                    <Button
                      title={adjustBusy ? "…" : "Claimed −1"}
                      onPress={() => onAdjust(-1)}
                      variant="ghost"
                      disabled={adjustBusy}
                    />
                    <Button
                      title={adjustBusy ? "…" : "Claimed +1"}
                      onPress={() => onAdjust(1)}
                      variant="ghost"
                      disabled={adjustBusy}
                    />
                  </View>
                ) : (
                  <Text style={styles.hint}>
                    Stripe configured — founding countdown is read-only (recounted from Stripe).
                  </Text>
                )}
                <Button title="Refresh overview" onPress={onSaveAdmin} variant="text" />
              </View>
            ) : null}
          </Card>
        </>
      ) : null}

      <SectionLabel>About</SectionLabel>
      <Card>
        <Text style={styles.meta}>DocketAI 1.3.2</Text>
        <Text style={styles.meta}>com.docketai.app</Text>
        <Text style={styles.meta}>JS embedded · no Metro required</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.muted,
    fontWeight: type.labelWeight,
    fontSize: 11,
    marginBottom: spacing.xs,
    letterSpacing: type.labelTracking,
    textTransform: "uppercase",
  },
  input: {
    backgroundColor: colors.bg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: 2,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: colors.text,
    fontSize: 14,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
    marginBottom: spacing.sm,
  },
  hint: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: spacing.md,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  meta: {
    color: colors.muted,
    fontSize: 13,
    marginTop: 4,
    fontWeight: type.bodyWeight,
    letterSpacing: type.letterSpacing,
  },
  rowBtns: {
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
});
