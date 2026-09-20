# Changelog — Docket Assistant (WordPress)

## 1.1.0 — 2026-09-17

### Security
- Allowlist Docket service hosts; HTTPS required unless WP_DEBUG + localhost
- Reject URL userinfo and non-standard ports
- Sandboxed iframe + referrerpolicy on launcher
- CSP / frame-src guidance in readme.txt and settings UI

### Features
- Embed snippet + add-to-site wizard copy
- Slack/email alert fields and optional desk API URL
- `load_plugin_textdomain` with Domain Path `/languages`
- Plugin URI → GitHub; SECURITY.md; PHPCS CI; sanitize tests

## 1.0.0

- Initial connector: service URL, bot ID, local launcher
