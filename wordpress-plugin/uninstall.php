<?php
/**
 * Fired when the plugin is uninstalled.
 *
 * @package DocketAssistant
 */

if (!defined('WP_UNINSTALL_PLUGIN')) {
	exit;
}

delete_option('docket_assistant_settings');
