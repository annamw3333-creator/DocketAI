#!/usr/bin/env python3
"""Mirror of docket_assistant_sanitize_service_url rules (no WordPress runtime)."""
from __future__ import annotations

import re
import unittest
from urllib.parse import urlparse

ALLOWED_HOSTS = {
    "docket.app",
    "www.docket.app",
    "docketdesk.com",
    "www.docketdesk.com",
    "app.docketdesk.com",
    "desk.docket.app",
    "docketlab.grok.me",
    "grok.me",
    "aestheticabodes.ca",
    "www.aestheticabodes.ca",
    "localhost",
    "127.0.0.1",
}

DEBUG_LOCAL_PORTS = {0, 80, 443, 3000, 5173, 8000, 8080, 8888}


def host_allowed(host: str) -> bool:
    host = (host or "").lower()
    if not host:
        return False
    for allowed in ALLOWED_HOSTS:
        if host == allowed:
            return True
        suffix = "." + allowed
        if host.endswith(suffix) and len(host) > len(suffix):
            return True
    return False


def sanitize_service_url(url: str, wp_debug: bool = False) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if re.search(r"://[^/]*@", url):
        return ""
    try:
        parts = urlparse(url)
    except Exception:
        return ""
    if not parts.scheme or not parts.hostname:
        return ""
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    if scheme == "https":
        pass
    elif scheme == "http" and wp_debug and host in ("localhost", "127.0.0.1"):
        pass
    else:
        return ""
    if not host_allowed(host):
        return ""
    port = parts.port or 0
    allowed_ports = {0, 443}
    if scheme == "http":
        allowed_ports.add(80)
    if wp_debug and host in ("localhost", "127.0.0.1"):
        allowed_ports |= DEBUG_LOCAL_PORTS
    if port and port not in allowed_ports:
        return ""
    if parts.username or parts.password:
        return ""
    cleaned = f"{scheme}://{host}"
    if port and port not in (80, 443):
        cleaned += f":{port}"
    if parts.path and parts.path != "/":
        cleaned += parts.path.rstrip("/")
    return cleaned


class SanitizeTests(unittest.TestCase):
    def test_https_allowlisted(self):
        self.assertEqual(
            sanitize_service_url("https://desk.docket.app"),
            "https://desk.docket.app",
        )
        self.assertEqual(
            sanitize_service_url("https://tenant.docket.app/path/"),
            "https://tenant.docket.app/path",
        )

    def test_reject_unknown_host(self):
        self.assertEqual(sanitize_service_url("https://evil.example"), "")

    def test_reject_userinfo(self):
        self.assertEqual(sanitize_service_url("https://user:pass@desk.docket.app"), "")

    def test_reject_odd_port(self):
        self.assertEqual(sanitize_service_url("https://desk.docket.app:8443"), "")

    def test_http_only_debug_localhost(self):
        self.assertEqual(sanitize_service_url("http://localhost:8000"), "")
        self.assertEqual(
            sanitize_service_url("http://localhost:8000", wp_debug=True),
            "http://localhost:8000",
        )

    def test_reject_ftp(self):
        self.assertEqual(sanitize_service_url("ftp://desk.docket.app"), "")


    def test_aesthetic_and_grok_hosts(self):
        self.assertEqual(
            sanitize_service_url("https://docketlab.grok.me"),
            "https://docketlab.grok.me",
        )
        self.assertEqual(
            sanitize_service_url("https://www.aestheticabodes.ca"),
            "https://www.aestheticabodes.ca",
        )

    def test_bot_id_chars(self):
        bot = re.sub(r"[^a-zA-Z0-9_-]", "", "Bot_ID-99!!")
        self.assertEqual(bot.lower()[:64], "bot_id-99")


if __name__ == "__main__":
    unittest.main()
