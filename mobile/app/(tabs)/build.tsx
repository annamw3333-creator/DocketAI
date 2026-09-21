import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Text, TextInput, StyleSheet, View, Pressable } from "react-native";
import { router, useFocusEffect } from "expo-router";
import * as Clipboard from "expo-clipboard";
import {
  Screen,
  Title,
  Subtitle,
  Card,
  Button,
  Loading,
  ErrorBox,
  Badge,
  SectionLabel,
  Divider,
} from "@/src/components";
import {
  createBotFromBrand,
  BrandDraft,
  fetchThemes,
  fetchBots,
  patchBotTheme,
  fetchEmbedSnippet,
  WidgetTheme,
  BotRecord,
} from "@/src/api";
import { colors, spacing, type } from "@/src/theme";

const POSITIONS = ["right", "left"] as const;
const AVATARS = ["monogram", "dot", "initials", "none"] as const;

function SwatchRow({ swatches }: { swatches?: string[] }) {
  const list = swatches && swatches.length ? swatches : ["#161513", "#ECEAE4", "#C9A227"];
  return (
    <View style={styles.swatchRow}>
      {list.slice(0, 4).map((c, i) => (
        <View key={`${c}-${i}`} style={[styles.swatch, { backgroundColor: c }]} />
      ))}
    </View>
  );
}

function LivePreview({
  theme,
  displayName,
  greeting,
}: {
  theme: WidgetTheme | null;
  displayName: string;
  greeting: string;
}) {
  if (!theme) {
    return (
      <Card>
        <Text style={styles.meta}>Select a theme to preview the customer-facing widget.</Text>
      </Card>
    );
  }
  const primary = theme.primary || "#161513";
  const accent = theme.accent || "#C9A227";
  const bg = theme.bg || "#ECEAE4";
  const text = theme.text || "#161513";
  const headerText = theme.header_text || "#ECEAE4";
  const botBubble = theme.bot_bubble || "#DDD6C8";
  const userBubble = theme.user_bubble || "#FFFFFF";
  const name = displayName || theme.name || "Assistant";
  const greet = greeting || "Hi — how can I help?";

  return (
    <View style={[styles.previewShell, { backgroundColor: bg, borderColor: colors.border }]}>
      <View style={[styles.previewHeader, { backgroundColor: primary, borderBottomColor: accent }]}>
        <View style={[styles.previewAvatar, { backgroundColor: accent }]}>
          <Text style={[styles.previewAvatarText, { color: primary }]}>
            {(name.trim()[0] || "D").toUpperCase()}
          </Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[styles.previewTitle, { color: headerText }]} numberOfLines={1}>
            {name}
          </Text>
          <Text style={[styles.previewSub, { color: headerText }]} numberOfLines={1}>
            {theme.name || theme.theme_id || theme.id}
          </Text>
        </View>
      </View>
      <View style={styles.previewBody}>
        <View style={[styles.bubbleBot, { backgroundColor: botBubble }]}>
          <Text style={[styles.bubbleText, { color: text }]}>{greet}</Text>
        </View>
        <View style={[styles.bubbleUser, { backgroundColor: userBubble, borderColor: text + "22" }]}>
          <Text style={[styles.bubbleText, { color: text }]}>What are your hours?</Text>
        </View>
      </View>
      <View style={styles.previewLauncherRow}>
        <View
          style={[
            styles.previewLauncher,
            {
              backgroundColor: theme.launcher_bg || primary,
              alignSelf: theme.position === "left" ? "flex-start" : "flex-end",
            },
          ]}
        >
          <Text style={{ color: theme.launcher_text || headerText, fontWeight: "600", fontSize: 12 }}>
            Chat
          </Text>
        </View>
      </View>
    </View>
  );
}

export default function BuildBotScreen() {
  const [url, setUrl] = useState("https://");
  const [notes, setNotes] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<BrandDraft | null>(null);
  const [botId, setBotId] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  // Theme Studio
  const [themes, setThemes] = useState<WidgetTheme[]>([]);
  const [bots, setBots] = useState<BotRecord[]>([]);
  const [selectedThemeId, setSelectedThemeId] = useState<string>("editorial-gold");
  const [displayName, setDisplayName] = useState("");
  const [greeting, setGreeting] = useState("");
  const [primaryOverride, setPrimaryOverride] = useState("");
  const [accentOverride, setAccentOverride] = useState("");
  const [position, setPosition] = useState<"left" | "right">("right");
  const [avatarStyle, setAvatarStyle] = useState<string>("monogram");
  const [themeBusy, setThemeBusy] = useState(false);
  const [embedSnippet, setEmbedSnippet] = useState<string | null>(null);
  const [embedSteps, setEmbedSteps] = useState<Record<string, string> | null>(null);
  const [themesError, setThemesError] = useState<string | null>(null);

  const selectedPreset = useMemo(
    () => themes.find((t) => (t.id || t.theme_id) === selectedThemeId) || null,
    [themes, selectedThemeId]
  );

  const previewTheme: WidgetTheme | null = useMemo(() => {
    if (!selectedPreset) return null;
    return {
      ...selectedPreset,
      theme_id: selectedThemeId,
      primary: primaryOverride.trim() || selectedPreset.primary,
      accent: accentOverride.trim() || selectedPreset.accent,
      position,
      avatar_style: avatarStyle,
      bot_name: displayName.trim() || undefined,
      greeting: greeting.trim() || undefined,
    };
  }, [
    selectedPreset,
    selectedThemeId,
    primaryOverride,
    accentOverride,
    position,
    avatarStyle,
    displayName,
    greeting,
  ]);

  const refreshLists = useCallback(async () => {
    try {
      const [t, b] = await Promise.all([fetchThemes(), fetchBots()]);
      setThemes(t.themes || []);
      setBots(b.bots || []);
      if (!selectedThemeId && t.default_theme_id) setSelectedThemeId(t.default_theme_id);
      setThemesError(null);
    } catch (e: any) {
      setThemesError(e?.message || "Could not load themes");
    }
  }, [selectedThemeId]);

  useFocusEffect(
    useCallback(() => {
      refreshLists();
    }, [refreshLists])
  );

  useEffect(() => {
    if (botId && bots.length) {
      const bot = bots.find((x) => x.id === botId);
      if (bot?.theme) {
        const tid = bot.theme.theme_id || bot.theme.id;
        if (tid) setSelectedThemeId(tid);
        if (bot.theme.bot_name || bot.theme.display_name) {
          setDisplayName(String(bot.theme.bot_name || bot.theme.display_name));
        }
        if (bot.theme.greeting) setGreeting(String(bot.theme.greeting));
        if (bot.theme.position === "left" || bot.theme.position === "right") {
          setPosition(bot.theme.position);
        }
        if (bot.theme.avatar_style) setAvatarStyle(String(bot.theme.avatar_style));
      }
    }
  }, [botId, bots]);

  const flash = (key: string) => {
    setCopied(key);
    setTimeout(() => setCopied((c) => (c === key ? null : c)), 1600);
  };

  const onPreviewDraft = async () => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const res = await createBotFromBrand({
        website_url: url.trim(),
        brand_notes: notes.trim(),
        name: name.trim() || undefined,
        create: false,
        theme_id: selectedThemeId,
      });
      setDraft(res.draft);
      setBotId(null);
      setNote(
        res.note ||
          "[DRAFT] Template only — preview below. Save when ready; review before production."
      );
      if (res.draft?.name && !displayName) setDisplayName(res.draft.name);
    } catch (e: any) {
      setError(e?.message || "Draft preview failed");
    } finally {
      setBusy(false);
    }
  };

  const onBuild = async () => {
    setBusy(true);
    setError(null);
    setEmbedSnippet(null);
    try {
      const res = await createBotFromBrand({
        website_url: url.trim(),
        brand_notes: notes.trim(),
        name: name.trim() || undefined,
        create: true,
        theme_id: selectedThemeId,
      });
      setDraft(res.draft);
      setBotId(res.bot?.id || null);
      setNote(
        res.note ||
          "[DRAFT] Prompt and FAQ are templates — review before production use."
      );
      if (res.draft?.name && !displayName) setDisplayName(res.draft.name);
      await refreshLists();
    } catch (e: any) {
      setError(e?.message || "Brand build failed");
    } finally {
      setBusy(false);
    }
  };

  const onCopyPrompt = async () => {
    if (!draft?.prompt) return;
    await Clipboard.setStringAsync(draft.prompt);
    flash("prompt");
  };

  const targetBotId = botId || (bots[0]?.id ?? null);

  const onApplyTheme = async () => {
    if (!targetBotId) {
      setThemesError("Build or select a bot first.");
      return;
    }
    setThemeBusy(true);
    setThemesError(null);
    setEmbedSnippet(null);
    try {
      const payload: Record<string, string> = { theme_id: selectedThemeId };
      if (displayName.trim()) payload.bot_name = displayName.trim();
      if (greeting.trim()) payload.greeting = greeting.trim();
      if (primaryOverride.trim()) payload.primary = primaryOverride.trim();
      if (accentOverride.trim()) payload.accent = accentOverride.trim();
      payload.position = position;
      payload.avatar_style = avatarStyle;
      await patchBotTheme(targetBotId, payload);
      const emb = await fetchEmbedSnippet(targetBotId);
      setEmbedSnippet(emb.snippet);
      setEmbedSteps(emb.steps || null);
      setBotId(targetBotId);
      await refreshLists();
      flash("theme");
    } catch (e: any) {
      setThemesError(e?.message || "Failed to save theme");
    } finally {
      setThemeBusy(false);
    }
  };

  const onCopyEmbed = async () => {
    if (!embedSnippet) return;
    await Clipboard.setStringAsync(embedSnippet);
    flash("embed");
  };

  const onLoadEmbed = async () => {
    if (!targetBotId) return;
    setThemeBusy(true);
    try {
      const emb = await fetchEmbedSnippet(targetBotId);
      setEmbedSnippet(emb.snippet);
      setEmbedSteps(emb.steps || null);
    } catch (e: any) {
      setThemesError(e?.message || "Failed to load embed");
    } finally {
      setThemeBusy(false);
    }
  };

  return (
    <Screen>
      <Title>Build + Themes</Title>
      <Subtitle>
        Draft a bot from any public brand site, then customize its customer-facing look and copy an
        embed snippet for your website.
      </Subtitle>

      {error ? <ErrorBox message={error} /> : null}

      <SectionLabel>1 · Brand → bot</SectionLabel>
      <Card>
        <Text style={styles.label}>URL</Text>
        <TextInput
          value={url}
          onChangeText={setUrl}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          placeholder="https://example.com"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Brand / prompt notes (optional)</Text>
        <TextInput
          value={notes}
          onChangeText={setNotes}
          multiline
          placeholder={"Name: Acme Clean\nWarm tone. Never invent prices."}
          placeholderTextColor={colors.muted}
          style={[styles.input, styles.area]}
        />
        <Text style={styles.label}>Display name override (optional)</Text>
        <TextInput
          value={name}
          onChangeText={setName}
          placeholder="Leave blank to infer from site"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Button
          title={busy ? "Working…" : "Preview [DRAFT] prompt"}
          onPress={onPreviewDraft}
          disabled={busy || url.trim().length < 8}
          variant="ghost"
        />
        <Button
          title={busy ? "Saving…" : "Create bot from brand"}
          onPress={onBuild}
          disabled={busy || url.trim().length < 8}
        />
      </Card>

      {busy ? <Loading label="Fetching site + drafting…" /> : null}

      {draft ? (
        <>
          <SectionLabel>[DRAFT] prompt preview</SectionLabel>
          <Card>
            <View style={styles.row}>
              <Badge label="[DRAFT]" tone="gold" />
              {botId ? <Badge label="Saved" tone="ok" /> : null}
            </View>
            <Text style={styles.cardTitle}>{draft.name}</Text>
            <Text style={styles.meta}>
              {draft.vertical}
              {botId ? ` · ${botId}` : ""}
            </Text>
            {note ? <Text style={styles.meta}>{note}</Text> : null}
            {draft.source?.fetch_error ? (
              <Text style={styles.warn}>Fetch note: {draft.source.fetch_error}</Text>
            ) : null}
          </Card>

          <SectionLabel>[DRAFT] system prompt</SectionLabel>
          <Card>
            <Text style={styles.mono}>{draft.prompt}</Text>
            <Button
              title={copied === "prompt" ? "Copied" : "Copy prompt"}
              onPress={onCopyPrompt}
              variant="ghost"
            />
          </Card>

          <SectionLabel>[DRAFT] FAQ ({draft.faq?.length || 0})</SectionLabel>
          {(draft.faq || []).slice(0, 6).map((f, i) => (
            <Card key={i}>
              <Text style={styles.cardTitle}>{f.question}</Text>
              <Text style={styles.meta}>{f.answer}</Text>
            </Card>
          ))}
        </>
      ) : null}

      <Divider />

      <SectionLabel>2 · Theme Studio</SectionLabel>
      <Subtitle>
        Themes style the customer-facing widget only — DocketAI app chrome stays black / white /
        gold.
      </Subtitle>
      {themesError ? <ErrorBox message={themesError} /> : null}

      <Card>
        <Text style={styles.label}>Bot</Text>
        {bots.length === 0 ? (
          <Text style={styles.meta}>No bots yet — generate one above.</Text>
        ) : (
          <View style={styles.botChips}>
            {bots.slice(0, 8).map((b) => {
              const selected = (botId || targetBotId) === b.id;
              return (
                <Pressable
                  key={b.id}
                  onPress={() => setBotId(b.id)}
                  style={[styles.chip, selected && styles.chipOn]}
                >
                  <Text style={[styles.chipText, selected && styles.chipTextOn]} numberOfLines={1}>
                    {b.name}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        )}
        {targetBotId ? <Text style={styles.meta}>Active: {targetBotId}</Text> : null}
      </Card>

      <SectionLabel>Theme presets ({themes.length || 8})</SectionLabel>
      <View style={styles.themeGrid}>
        {themes.map((t) => {
          const tid = t.id || t.theme_id || "";
          const selected = tid === selectedThemeId;
          return (
            <Pressable
              key={tid}
              onPress={() => setSelectedThemeId(tid)}
              style={[styles.themeCard, selected && styles.themeCardOn]}
            >
              <SwatchRow swatches={t.swatches || [t.primary, t.bg, t.accent]} />
              <Text style={styles.themeName}>{t.name}</Text>
              <Text style={styles.themeDesc} numberOfLines={2}>
                {t.description}
              </Text>
              {selected ? <Badge label="Selected" tone="gold" /> : null}
            </Pressable>
          );
        })}
      </View>

      <SectionLabel>Customize</SectionLabel>
      <Card>
        <Text style={styles.label}>Widget display name</Text>
        <TextInput
          value={displayName}
          onChangeText={setDisplayName}
          placeholder="Shown in chat header"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Greeting</Text>
        <TextInput
          value={greeting}
          onChangeText={setGreeting}
          placeholder="Hi — ask about hours, bookings, or policies."
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Primary override (#hex, optional)</Text>
        <TextInput
          value={primaryOverride}
          onChangeText={setPrimaryOverride}
          autoCapitalize="none"
          placeholder="#161513"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Accent override (#hex, optional)</Text>
        <TextInput
          value={accentOverride}
          onChangeText={setAccentOverride}
          autoCapitalize="none"
          placeholder="#C9A227"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
        <Text style={styles.label}>Position</Text>
        <View style={styles.botChips}>
          {POSITIONS.map((p) => (
            <Pressable
              key={p}
              onPress={() => setPosition(p)}
              style={[styles.chip, position === p && styles.chipOn]}
            >
              <Text style={[styles.chipText, position === p && styles.chipTextOn]}>{p}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={[styles.label, { marginTop: spacing.sm }]}>Avatar</Text>
        <View style={styles.botChips}>
          {AVATARS.map((a) => (
            <Pressable
              key={a}
              onPress={() => setAvatarStyle(a)}
              style={[styles.chip, avatarStyle === a && styles.chipOn]}
            >
              <Text style={[styles.chipText, avatarStyle === a && styles.chipTextOn]}>{a}</Text>
            </Pressable>
          ))}
        </View>
      </Card>

      <SectionLabel>Live preview</SectionLabel>
      <LivePreview
        theme={previewTheme}
        displayName={displayName || draft?.name || selectedPreset?.name || "Assistant"}
        greeting={greeting}
      />

      <Button
        title={
          themeBusy
            ? "Saving…"
            : copied === "theme"
              ? "Theme saved"
              : "Save theme + refresh embed"
        }
        onPress={onApplyTheme}
        disabled={themeBusy || !targetBotId}
      />

      <SectionLabel>3 · Add to your site</SectionLabel>
      <Card>
        <Text style={styles.meta}>
          Copy the snippet below and paste it before {"</body>"} on any page. Chat hits Desk{" "}
          /api/chat immediately.
        </Text>
        {embedSteps ? (
          <>
            <Text style={styles.step}>WordPress — {embedSteps.wordpress}</Text>
            <Text style={styles.step}>Squarespace — {embedSteps.squarespace}</Text>
            <Text style={styles.step}>Any HTML — {embedSteps.any_html}</Text>
          </>
        ) : (
          <>
            <Text style={styles.step}>WordPress — Custom HTML block or footer code snippet.</Text>
            <Text style={styles.step}>Squarespace — Settings → Advanced → Code Injection → Footer.</Text>
            <Text style={styles.step}>Any HTML — paste before {"</body>"}.</Text>
          </>
        )}
        <Button
          title="Load embed code"
          onPress={onLoadEmbed}
          variant="ghost"
          disabled={!targetBotId || themeBusy}
        />
        {embedSnippet ? (
          <>
            <Text style={styles.mono} numberOfLines={12}>
              {embedSnippet}
            </Text>
            <Button
              title={copied === "embed" ? "Copied embed" : "Copy embed code"}
              onPress={onCopyEmbed}
            />
          </>
        ) : null}
      </Card>

      {targetBotId ? (
        <Button title="Use bot in Run" onPress={() => router.push("/run")} variant="text" />
      ) : null}
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
  area: { minHeight: 100, textAlignVertical: "top" },
  row: { flexDirection: "row", gap: 8, marginBottom: spacing.sm, flexWrap: "wrap" },
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
  warn: {
    color: colors.danger,
    fontSize: 12,
    marginTop: 8,
    letterSpacing: type.letterSpacing,
  },
  mono: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 16,
    fontFamily: "monospace",
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  themeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: spacing.md,
  },
  themeCard: {
    width: "47%",
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: 4,
    padding: 12,
    gap: 6,
  },
  themeCardOn: {
    borderColor: colors.gold,
  },
  themeName: {
    color: colors.text,
    fontSize: 13,
    fontWeight: type.mediumWeight,
    letterSpacing: type.letterSpacing,
  },
  themeDesc: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 15,
    letterSpacing: 0.4,
  },
  swatchRow: { flexDirection: "row", gap: 4, marginBottom: 4 },
  swatch: {
    width: 18,
    height: 18,
    borderRadius: 2,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  botChips: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: spacing.sm },
  chip: {
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 2,
    maxWidth: "100%",
  },
  chipOn: { borderColor: colors.gold },
  chipText: {
    color: colors.muted,
    fontSize: 11,
    letterSpacing: type.labelTracking,
    textTransform: "uppercase",
  },
  chipTextOn: { color: colors.gold },
  previewShell: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    overflow: "hidden",
    marginBottom: spacing.md,
  },
  previewHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 2,
  },
  previewAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  previewAvatarText: { fontSize: 12, fontWeight: "700" },
  previewTitle: { fontSize: 14, fontWeight: "600" },
  previewSub: { fontSize: 10, opacity: 0.75, marginTop: 1 },
  previewBody: { padding: 12, gap: 8, minHeight: 110 },
  bubbleBot: { alignSelf: "flex-start", padding: 10, borderRadius: 10, maxWidth: "88%" },
  bubbleUser: {
    alignSelf: "flex-end",
    padding: 10,
    borderRadius: 10,
    maxWidth: "88%",
    borderWidth: StyleSheet.hairlineWidth,
  },
  bubbleText: { fontSize: 13, lineHeight: 18 },
  previewLauncherRow: { padding: 12, paddingTop: 0 },
  previewLauncher: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  step: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 6,
    letterSpacing: type.letterSpacing,
  },
});
