# Security Policy — Docket Assistant

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| 1.0.x   | Limited (upgrade recommended) |

## Reporting a vulnerability

Email the maintainer (Anna Walker / repo owner on GitHub) privately. Do not open a public issue with exploit details.

## Threat model

| Threat | Mitigation |
|--------|------------|
| Attacker-controlled `service_url` loads hostile iframe | Allowlist (`docket.app`, `docketdesk.com`, localhost); HTTPS unless `WP_DEBUG` + localhost; reject userinfo and odd ports |
| Stored XSS via settings | Settings API sanitize callback; `esc_attr` / `esc_html` / `esc_url` on output; `manage_options` |
| Remote JS supply-chain | Launcher ships with plugin; no remote script tags |
| Clickjacking / iframe abuse of parent | iframe `sandbox` + `referrerpolicy=no-referrer`; document CSP `frame-src` |
| Settings leak on uninstall | `uninstall.php` deletes `docket_assistant_settings` |

## Hardening checklist for operators

1. Keep WordPress and PHP updated.
2. Prefer HTTPS desks only in production (`WP_DEBUG` off).
3. Set CSP `frame-src` to your desk origin.
4. Restrict who has `manage_options`.
5. Point alert webhooks only at trusted HTTPS endpoints.

## Extending the host allowlist

```php
add_filter( 'docket_assistant_allowed_hosts', function ( $hosts ) {
    $hosts[] = 'desk.example.com';
    return $hosts;
} );
```
