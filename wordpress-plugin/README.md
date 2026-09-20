# Docket Assistant (WordPress)

Hardened WordPress connector for the Docket desk chat bubble.

## Install

1. Zip this `wordpress-plugin` folder (or use the parent `docket-fixed.zip`).
2. WordPress → Plugins → Upload → Activate.
3. Settings → Docket Assistant → paste desk URL + bot ID.

## Security (1.1.0)

- Allowlisted hosts (`docket.app`, `docketdesk.com`, localhost)
- HTTPS required unless `WP_DEBUG` + localhost
- Rejects URL userinfo and odd ports
- Sandboxed iframe + CSP docs
- Local launcher JS only; Settings API + `manage_options`

See `SECURITY.md` and `tests/test_sanitize.py`.
