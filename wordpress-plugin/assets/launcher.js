/**
 * Local launcher for Docket Assistant.
 * Opens a sandboxed iframe to the Docket service. No remote JavaScript is executed.
 */
(function () {
	"use strict";
	if (!window.docketAssistant || !window.docketAssistant.widgetUrl) {
		return;
	}
	if (window.__docketAssistantLoaded) {
		return;
	}
	window.__docketAssistantLoaded = true;

	var url = String(window.docketAssistant.widgetUrl);
	// Defense: only allow http(s) widget URLs from localize_script.
	if (!/^https?:\/\//i.test(url)) {
		return;
	}
	var openLabel = window.docketAssistant.openLabel || "Open chat";
	var closeLabel = window.docketAssistant.closeLabel || "Close chat";

	var iframe = document.createElement("iframe");
	iframe.src = url;
	iframe.title = openLabel;
	iframe.setAttribute("aria-label", openLabel);
	// Restrictive sandbox: scripts + same-origin + forms for the chat UI; no top-navigation.
	iframe.setAttribute(
		"sandbox",
		"allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
	);
	iframe.setAttribute("referrerpolicy", "no-referrer");
	iframe.style.cssText =
		"position:fixed;right:16px;bottom:84px;width:360px;height:520px;max-width:calc(100vw - 24px);max-height:calc(100dvh - 96px);border:0;border-radius:16px;z-index:2147483647;box-shadow:0 18px 40px -18px rgba(0,0,0,.45);display:none;background:#eceae4;";

	var btn = document.createElement("button");
	btn.type = "button";
	btn.setAttribute("aria-expanded", "false");
	btn.setAttribute("aria-label", openLabel);
	btn.style.cssText =
		"position:fixed;right:16px;bottom:16px;width:56px;height:56px;border:0;border-radius:28px;background:#161513;color:#eceae4;z-index:2147483647;cursor:pointer;box-shadow:0 10px 24px -12px rgba(0,0,0,.5);display:inline-flex;align-items:center;justify-content:center;";
	btn.innerHTML =
		'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>';

	var open = false;
	btn.addEventListener("click", function () {
		open = !open;
		iframe.style.display = open ? "block" : "none";
		btn.setAttribute("aria-expanded", open ? "true" : "false");
		btn.setAttribute("aria-label", open ? closeLabel : openLabel);
	});

	document.body.appendChild(iframe);
	document.body.appendChild(btn);
})();
