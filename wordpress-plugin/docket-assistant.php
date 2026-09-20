<?php
/**
 * Plugin Name:       Docket Assistant
 * Plugin URI:        https://github.com/annamw3333-creator/docket-assistant
 * Description:       Adds your Docket website chat to every public page. Connects to the Docket desk service — paste your desk URL and bot ID in settings. Includes embed snippets and alert webhook fields for mystery-shop score drops.
 * Version:           1.1.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Anna Walker / Docket
 * Author URI:        https://github.com/annamw3333-creator
 * License:           GPLv2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       docket-assistant
 * Domain Path:       /languages
 *
 * @package DocketAssistant
 */

if (!defined('ABSPATH')) {
	exit;
}

define('DOCKET_ASSISTANT_VERSION', '1.1.0');
define('DOCKET_ASSISTANT_FILE', __FILE__);
define('DOCKET_ASSISTANT_DIR', plugin_dir_path(__FILE__));

/**
 * Hosts allowed for service_url (exact match or subdomain of listed suffixes).
 * Document these in readme.txt / SECURITY.md. localhost / 127.0.0.1 for local desks.
 *
 * @return string[]
 */
function docket_assistant_allowed_hosts() {
	$hosts = array(
		'docket.app',
		'www.docket.app',
		'docketdesk.com',
		'www.docketdesk.com',
		'app.docketdesk.com',
		'desk.docket.app',
		'docketlab.grok.me',
		'grok.me',
		'aestheticabodes.ca',
		'www.aestheticabodes.ca',
		'trycloudflare.com',
		'localhost',
		'127.0.0.1',
	);
	/**
	 * Filter the allowlist of Docket service hosts.
	 *
	 * @param string[] $hosts Hostnames (no scheme/port).
	 */
	return apply_filters('docket_assistant_allowed_hosts', $hosts);
}

/**
 * Default option payload.
 *
 * @return array<string, string>
 */
function docket_assistant_defaults() {
	return array(
		'service_url'      => '',
		'bot_id'           => '',
		'alert_webhook'    => '',
		'alert_email'      => '',
		'desk_api_url'     => '',
	);
}

/**
 * @return array<string, string>
 */
function docket_assistant_get_settings() {
	$stored = get_option('docket_assistant_settings', array());
	if (!is_array($stored)) {
		$stored = array();
	}
	return wp_parse_args($stored, docket_assistant_defaults());
}

/**
 * Whether a hostname is on the allowlist (exact or subdomain of a suffix host).
 *
 * @param string $host Hostname without port.
 * @return bool
 */
function docket_assistant_host_allowed($host) {
	$host = strtolower((string) $host);
	if ($host === '') {
		return false;
	}
	foreach (docket_assistant_allowed_hosts() as $allowed) {
		$allowed = strtolower((string) $allowed);
		if ($host === $allowed) {
			return true;
		}
		// Subdomain of allowlisted suffix (e.g. tenant.docket.app).
		if (substr($allowed, 0, 1) !== '.' && strlen($host) > strlen($allowed) + 1) {
			$suffix = '.' . $allowed;
			if (substr($host, -strlen($suffix)) === $suffix) {
				return true;
			}
		}
	}
	return false;
}

/**
 * Reject userinfo, odd ports, non-http(s), and hosts outside the allowlist.
 * HTTPS required unless WP_DEBUG is true (then http://localhost / 127.0.0.1 ok).
 *
 * @param string $url Candidate URL.
 * @return string Sanitized URL or empty string on reject.
 */
function docket_assistant_sanitize_service_url($url) {
	$url = trim((string) $url);
	if ($url === '') {
		return '';
	}

	// Reject credentials in URL (user:pass@host).
	if (preg_match('#://[^/]*@#', $url)) {
		return '';
	}

	$parts = wp_parse_url($url);
	if (!is_array($parts) || empty($parts['scheme']) || empty($parts['host'])) {
		return '';
	}

	$scheme = strtolower((string) $parts['scheme']);
	$host   = strtolower((string) $parts['host']);
	$debug  = defined('WP_DEBUG') && WP_DEBUG;

	if ($scheme === 'https') {
		// ok
	} elseif ($scheme === 'http' && $debug && in_array($host, array('localhost', '127.0.0.1'), true)) {
		// Local desks only when debugging.
	} else {
		return '';
	}

	if (!docket_assistant_host_allowed($host)) {
		return '';
	}

	// Odd / non-default ports rejected. Allow default omit, 443 for https, 80 for http, and common local desk ports in debug.
	$port = isset($parts['port']) ? (int) $parts['port'] : 0;
	$allowed_ports = array(0, 443);
	if ($scheme === 'http') {
		$allowed_ports[] = 80;
	}
	if ($debug && in_array($host, array('localhost', '127.0.0.1'), true)) {
		$allowed_ports = array_merge($allowed_ports, array(3000, 5173, 8000, 8080, 8888));
	}
	if ($port !== 0 && !in_array($port, $allowed_ports, true)) {
		return '';
	}

	$clean = esc_url_raw($url, array('http', 'https'));
	if ($clean === '') {
		return '';
	}

	// Re-check after esc_url_raw (defense in depth).
	$re = wp_parse_url($clean);
	if (!is_array($re) || empty($re['host']) || !docket_assistant_host_allowed(strtolower((string) $re['host']))) {
		return '';
	}
	if (isset($re['user']) || isset($re['pass'])) {
		return '';
	}

	return untrailingslashit($clean);
}

/**
 * @param mixed $input Raw settings from the form.
 * @return array<string, string>
 */
function docket_assistant_sanitize_settings($input) {
	$clean = docket_assistant_defaults();
	if (!is_array($input)) {
		return $clean;
	}

	$clean['service_url'] = docket_assistant_sanitize_service_url(
		isset($input['service_url']) ? $input['service_url'] : ''
	);

	$id = isset($input['bot_id']) ? (string) $input['bot_id'] : '';
	$id = strtolower(preg_replace('/[^a-zA-Z0-9_-]/', '', $id));
	$clean['bot_id'] = substr($id, 0, 64);

	$webhook = isset($input['alert_webhook']) ? trim((string) $input['alert_webhook']) : '';
	if ($webhook !== '') {
		$webhook = esc_url_raw($webhook, array('https'));
		if ($webhook && preg_match('#://[^/]*@#', $webhook)) {
			$webhook = '';
		}
	}
	$clean['alert_webhook'] = $webhook ? $webhook : '';

	$email = isset($input['alert_email']) ? sanitize_email((string) $input['alert_email']) : '';
	$clean['alert_email'] = is_email($email) ? $email : '';

	$desk = isset($input['desk_api_url']) ? $input['desk_api_url'] : '';
	$clean['desk_api_url'] = docket_assistant_sanitize_service_url($desk);

	return $clean;
}

/**
 * @return bool
 */
function docket_assistant_is_configured() {
	$opts = docket_assistant_get_settings();
	return ($opts['service_url'] !== '' && $opts['bot_id'] !== '');
}

/**
 * @return string
 */
function docket_assistant_widget_url() {
	$opts = docket_assistant_get_settings();
	if ($opts['service_url'] === '' || $opts['bot_id'] === '') {
		return '';
	}
	return trailingslashit($opts['service_url']) . 'widget/' . rawurlencode($opts['bot_id']);
}

/**
 * Embed snippet for copy-paste (generic iframe + bubble pattern).
 *
 * @return string
 */
function docket_assistant_embed_snippet() {
	$opts = docket_assistant_get_settings();
	if ($opts['service_url'] === '' || $opts['bot_id'] === '') {
		return '';
	}
	$widget = esc_url(docket_assistant_widget_url());
	$bot    = esc_attr($opts['bot_id']);
	return "<!-- Docket Assistant embed -->\n"
		. '<div id="docket-assistant-root" data-bot="' . $bot . '"></div>' . "\n"
		. '<iframe id="docket-assistant-frame" src="' . $widget . '" title="Chat"'
		. ' sandbox="allow-scripts allow-same-origin allow-forms allow-popups"'
		. ' style="display:none;position:fixed;right:16px;bottom:84px;width:360px;height:520px;border:0;border-radius:16px;z-index:2147483647;"></iframe>' . "\n";
}

add_action(
	'plugins_loaded',
	function () {
		load_plugin_textdomain(
			'docket-assistant',
			false,
			dirname(plugin_basename(DOCKET_ASSISTANT_FILE)) . '/languages'
		);
	}
);

add_action(
	'admin_init',
	function () {
		register_setting(
			'docket_assistant',
			'docket_assistant_settings',
			array(
				'type'              => 'array',
				'sanitize_callback' => 'docket_assistant_sanitize_settings',
				'default'           => docket_assistant_defaults(),
				'show_in_rest'      => false,
			)
		);
	}
);

add_action(
	'admin_menu',
	function () {
		add_options_page(
			__('Docket Assistant', 'docket-assistant'),
			__('Docket Assistant', 'docket-assistant'),
			'manage_options',
			'docket-assistant',
			'docket_assistant_render_settings'
		);
	}
);

add_filter(
	'plugin_action_links_' . plugin_basename(DOCKET_ASSISTANT_FILE),
	function ($links) {
		if (!is_array($links)) {
			$links = array();
		}
		$url = admin_url('options-general.php?page=docket-assistant');
		array_unshift(
			$links,
			'<a href="' . esc_url($url) . '">' . esc_html__('Settings', 'docket-assistant') . '</a>'
		);
		return $links;
	}
);

add_action(
	'admin_notices',
	function () {
		if (!current_user_can('manage_options')) {
			return;
		}
		if (docket_assistant_is_configured()) {
			return;
		}
		$screen = function_exists('get_current_screen') ? get_current_screen() : null;
		if (!$screen) {
			return;
		}
		$on_plugins  = ($screen->id === 'plugins');
		$on_settings = ($screen->id === 'settings_page_docket-assistant');
		if (!$on_plugins && !$on_settings) {
			return;
		}
		$url = admin_url('options-general.php?page=docket-assistant');
		echo '<div class="notice notice-warning"><p>';
		echo esc_html__('Docket Assistant is installed but not connected.', 'docket-assistant');
		echo ' <a href="' . esc_url($url) . '">';
		echo esc_html__('Add your Docket URL and bot ID', 'docket-assistant');
		echo '</a>.</p></div>';
	}
);

/**
 * Settings screen with add-to-site wizard, embed snippets, alert fields.
 */
function docket_assistant_render_settings() {
	if (!current_user_can('manage_options')) {
		return;
	}
	$opts    = docket_assistant_get_settings();
	$snippet = docket_assistant_embed_snippet();
	$host_list = implode(', ', docket_assistant_allowed_hosts());
	?>
	<div class="wrap">
		<h1><?php echo esc_html__('Docket Assistant', 'docket-assistant'); ?></h1>
		<p><?php echo esc_html__('This plugin is a connector for the Docket desk. Chat replies are generated on your Docket desk, not inside WordPress. You need a Docket account and a published assistant.', 'docket-assistant'); ?></p>

		<h2><?php echo esc_html__('Add to site wizard', 'docket-assistant'); ?></h2>
		<ol>
			<li><?php echo esc_html__('Run your Docket desk (see the companion desk/ service README). Publish an assistant and note its Bot ID.', 'docket-assistant'); ?></li>
			<li><?php echo esc_html__('Paste the public Docket URL (HTTPS) and Bot ID below. Only allowlisted Docket hosts are accepted.', 'docket-assistant'); ?></li>
			<li><?php echo esc_html__('Optional: set Slack/email alert targets so mystery-shop score drops notify your team.', 'docket-assistant'); ?></li>
			<li><?php echo esc_html__('Save. The chat bubble appears on every public page. Or copy the embed snippet for a custom theme.', 'docket-assistant'); ?></li>
		</ol>
		<p class="description"><?php echo esc_html(sprintf(/* translators: %s: comma-separated host list */ __('Allowed service hosts: %s (plus their subdomains). HTTPS required unless WP_DEBUG and localhost.', 'docket-assistant'), $host_list)); ?></p>

		<form action="options.php" method="post">
			<?php settings_fields('docket_assistant'); ?>
			<table class="form-table" role="presentation">
				<tr>
					<th scope="row">
						<label for="docket_assistant_service_url"><?php echo esc_html__('Docket URL', 'docket-assistant'); ?></label>
					</th>
					<td>
						<input
							type="url"
							class="regular-text code"
							id="docket_assistant_service_url"
							name="docket_assistant_settings[service_url]"
							value="<?php echo esc_attr($opts['service_url']); ?>"
							placeholder="https://desk.docket.app"
							autocomplete="off"
						/>
						<p class="description"><?php echo esc_html__('Public address of your Docket desk. Must be HTTPS on an allowlisted host (or http://localhost when WP_DEBUG). Userinfo and odd ports are rejected.', 'docket-assistant'); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row">
						<label for="docket_assistant_bot_id"><?php echo esc_html__('Bot ID', 'docket-assistant'); ?></label>
					</th>
					<td>
						<input
							type="text"
							class="regular-text code"
							id="docket_assistant_bot_id"
							name="docket_assistant_settings[bot_id]"
							value="<?php echo esc_attr($opts['bot_id']); ?>"
							maxlength="64"
							autocomplete="off"
							spellcheck="false"
						/>
						<p class="description"><?php echo esc_html__('Published assistant ID from Docket → Add to site.', 'docket-assistant'); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row">
						<label for="docket_assistant_desk_api_url"><?php echo esc_html__('Desk API URL', 'docket-assistant'); ?></label>
					</th>
					<td>
						<input
							type="url"
							class="regular-text code"
							id="docket_assistant_desk_api_url"
							name="docket_assistant_settings[desk_api_url]"
							value="<?php echo esc_attr($opts['desk_api_url']); ?>"
							placeholder="https://desk.docket.app"
							autocomplete="off"
						/>
						<p class="description"><?php echo esc_html__('Optional companion API base for scorecards and embed generation (same allowlist rules).', 'docket-assistant'); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row">
						<label for="docket_assistant_alert_webhook"><?php echo esc_html__('Alert webhook (Slack/etc.)', 'docket-assistant'); ?></label>
					</th>
					<td>
						<input
							type="url"
							class="regular-text code"
							id="docket_assistant_alert_webhook"
							name="docket_assistant_settings[alert_webhook]"
							value="<?php echo esc_attr($opts['alert_webhook']); ?>"
							placeholder="https://hooks.slack.com/services/..."
							autocomplete="off"
						/>
						<p class="description"><?php echo esc_html__('HTTPS webhook called by the desk when mystery-shop scores drop. Stored here for copy into desk .env / settings.', 'docket-assistant'); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row">
						<label for="docket_assistant_alert_email"><?php echo esc_html__('Alert email', 'docket-assistant'); ?></label>
					</th>
					<td>
						<input
							type="email"
							class="regular-text"
							id="docket_assistant_alert_email"
							name="docket_assistant_settings[alert_email]"
							value="<?php echo esc_attr($opts['alert_email']); ?>"
							placeholder="ops@example.com"
							autocomplete="off"
						/>
						<p class="description"><?php echo esc_html__('Email notified on score regressions (configure SMTP / desk ALERT_EMAIL).', 'docket-assistant'); ?></p>
					</td>
				</tr>
			</table>
			<?php submit_button(__('Save connection', 'docket-assistant')); ?>
		</form>

		<?php if ($snippet !== '') : ?>
			<h2><?php echo esc_html__('Embed snippet', 'docket-assistant'); ?></h2>
			<p><?php echo esc_html__('For custom themes or non-WP pages. The iframe uses a restrictive sandbox.', 'docket-assistant'); ?></p>
			<textarea class="large-text code" rows="6" readonly onclick="this.select();"><?php echo esc_textarea($snippet); ?></textarea>
		<?php endif; ?>

		<h2><?php echo esc_html__('Content Security Policy', 'docket-assistant'); ?></h2>
		<p><?php echo esc_html__('If your site sends a CSP header, allow the Docket desk origin in frame-src (and child-src if used). Example:', 'docket-assistant'); ?></p>
		<pre class="code" style="background:#f6f7f7;padding:12px;overflow:auto;">Content-Security-Policy: frame-src 'self' https://desk.docket.app https://*.docket.app https://*.docketdesk.com;</pre>
	</div>
	<?php
}

add_action(
	'wp_enqueue_scripts',
	function () {
		if (is_admin() || !docket_assistant_is_configured()) {
			return;
		}
		$widget = docket_assistant_widget_url();
		if ($widget === '') {
			return;
		}
		wp_enqueue_script(
			'docket-assistant',
			plugins_url('assets/launcher.js', DOCKET_ASSISTANT_FILE),
			array(),
			DOCKET_ASSISTANT_VERSION,
			true
		);
		wp_localize_script(
			'docket-assistant',
			'docketAssistant',
			array(
				'widgetUrl'  => esc_url_raw($widget),
				'openLabel'  => __('Open chat', 'docket-assistant'),
				'closeLabel' => __('Close chat', 'docket-assistant'),
			)
		);
	}
);
