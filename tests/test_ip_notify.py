import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, MagicMock, patch
from urllib.error import HTTPError, URLError

import ip_notify


class TestGetConfig(unittest.TestCase):
    def test_prefers_args_over_env(self):
        args = Namespace(
            test=True,
            service="msteams",
            webhook="https://example.com/from-args",
            cache_file="/tmp/from-args.txt",
        )

        with (
            patch("ip_notify.get_args", return_value=args),
            patch.dict(
                "os.environ",
                {
                    "WEBHOOK_SERVICE": "discord",
                    "WEBHOOK_URL": "https://example.com/from-env",
                    "IP_CACHE": "/tmp/from-env.txt",
                    "EMBED_COLOR": "#abcdef",
                    "AUTHOR_URL": "https://example.com/author",
                    "ICON_URL": "https://example.com/icon.png",
                },
                clear=True,
            ),
        ):
            config = ip_notify.get_config()

        self.assertTrue(config.test)
        self.assertEqual(config.service, "msteams")
        self.assertEqual(config.webhook, "https://example.com/from-args")
        self.assertEqual(config.ip_cache, Path("/tmp/from-args.txt"))
        self.assertEqual(config.embed_color, "#abcdef")
        self.assertEqual(config.author_url, "https://example.com/author")
        self.assertEqual(config.icon_url, "https://example.com/icon.png")

    def test_uses_xdg_cache(self):
        args = Namespace(test=False, service=None, webhook=None, cache_file=None)

        with (
            TemporaryDirectory() as xdg_cache,
            TemporaryDirectory() as home,
            patch("ip_notify.get_args", return_value=args),
            patch.dict(
                "os.environ", {"XDG_CACHE_HOME": xdg_cache, "HOME": home}, clear=True
            ),
        ):
            config = ip_notify.get_config()

        self.assertEqual(config.service, "discord")
        self.assertIsNone(config.webhook)
        self.assertEqual(config.ip_cache, Path(xdg_cache, "ip_notify_cache"))

    def test_uses_default_home_cache(self):
        args = Namespace(test=False, service=None, webhook=None, cache_file=None)

        with (
            TemporaryDirectory() as home,
            patch("ip_notify.get_args", return_value=args),
            patch.dict("os.environ", {"HOME": home}, clear=True),
        ):
            config = ip_notify.get_config()

        self.assertEqual(config.service, "discord")
        self.assertIsNone(config.webhook)
        self.assertEqual(config.ip_cache, Path(home, ".config", "ip_notify_cache"))


class TestWebhookPayloads(unittest.TestCase):
    def test_discord_data_builds_expected_payload(self):
        config = Namespace(
            embed_color="#1bb106",
            author_url="https://example.com/author",
            icon_url="https://example.com/icon.png",
        )

        payload = ip_notify.discord_data(config, "1.2.3.4", "5.6.7.8")

        self.assertEqual(payload["username"], "IP Notify")
        self.assertEqual(payload["avatar_url"], "https://example.com/author")
        embed = payload["embeds"][0]
        self.assertEqual(embed["color"], int("1bb106", 16))
        self.assertEqual(embed["author"]["url"], "https://example.com/author")
        self.assertEqual(embed["author"]["icon_url"], "https://example.com/icon.png")
        self.assertEqual(embed["fields"][0]["value"], "**1.2.3.4**")
        self.assertEqual(embed["fields"][1]["value"], "~~5.6.7.8~~")
        self.assertIn("T", embed["timestamp"])

    def test_teams_data_builds_expected_payload(self):
        payload = ip_notify.teams_data(Namespace(), "5.6.7.8", "1.2.3.4")

        self.assertEqual(payload["type"], "message")
        attachment = payload["attachments"][0]
        self.assertEqual(
            attachment["contentType"], "application/vnd.microsoft.card.adaptive"
        )
        facts = attachment["content"]["body"][1]["facts"]
        self.assertEqual(facts[0], {"title": "Old:", "value": "5.6.7.8"})
        self.assertEqual(facts[1], {"title": "New:", "value": "1.2.3.4"})


class TestFileHelpers(unittest.TestCase):
    def test_get_last_ip_returns_none_when_file_missing(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, "ip.txt")
            self.assertIsNone(ip_notify.get_last_ip(path))

    def test_get_last_ip_reads_first_line(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, "ip.txt")
            path.write_text("1.2.3.4\nextra\n")

            self.assertEqual(ip_notify.get_last_ip(path), "1.2.3.4")

    def test_save_current_ip_writes_trailing_newline(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, "ip.txt")
            ip_notify.save_current_ip("1.2.3.4", path)

            self.assertEqual(path.read_text(), "1.2.3.4\n")

    def test_save_current_ip_logs_oserror(self):
        path = MagicMock()
        path.write_text.side_effect = OSError("disk full")

        with patch.object(ip_notify, "logger") as mock_logger:
            ip_notify.save_current_ip("1.2.3.4", path)

        mock_logger.error.assert_called_once()


class TestGetCurrentIp(unittest.TestCase):
    def test_returns_ip_from_first_successful_provider(self):
        first_response = MagicMock()
        first_response.__enter__.return_value.status = 500

        second_response = MagicMock()
        second_response.__enter__.return_value.status = 200
        second_response.__enter__.return_value.read.return_value = b"1.2.3.4\n"

        with patch(
            "ip_notify.urllib.request.urlopen",
            side_effect=[first_response, second_response],
        ):
            current_ip = ip_notify.get_current_ip(["https://a", "https://b"])

        self.assertEqual(current_ip, "1.2.3.4")

    def test_returns_none_when_all_providers_fail(self):
        first_response = MagicMock()
        first_response.__enter__.return_value.status = 500

        second_response = MagicMock()
        second_response.__enter__.return_value.status = 503

        with (
            patch(
                "ip_notify.urllib.request.urlopen",
                side_effect=[first_response, second_response],
            ),
            patch("ip_notify.logging.error") as mock_error,
        ):
            current_ip = ip_notify.get_current_ip(["https://a", "https://b"])

        self.assertIsNone(current_ip)
        mock_error.assert_called_once()


class TestSendNotification(unittest.TestCase):
    def test_sends_discord_notification(self):
        config = Namespace(service="discord")
        response = MagicMock()
        response.__enter__.return_value.status = 200

        with (
            patch("ip_notify.discord_data", return_value={"ok": True}) as mock_payload,
            patch(
                "ip_notify.urllib.request.urlopen", return_value=response
            ) as mock_urlopen,
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_payload.assert_called_once_with(config, "1.2.3.4", "5.6.7.8")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.com/webhook")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data.decode("utf-8")), {"ok": True})
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 5)

    def test_sends_msteams_notification(self):
        config = Namespace(service="msteams")
        response = MagicMock()
        response.__enter__.return_value.status = 202

        with (
            patch("ip_notify.teams_data", return_value={"ok": True}) as mock_payload,
            patch("ip_notify.urllib.request.urlopen", return_value=response),
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_payload.assert_called_once_with(config, "1.2.3.4", "5.6.7.8")

    def test_logs_error_for_unsupported_service(self):
        config = Namespace(service="slack")

        with (
            patch("ip_notify.logging.error") as mock_error,
            patch("ip_notify.urllib.request.urlopen") as mock_urlopen,
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_error.assert_called_once_with("Unsupported webhook service %s", "slack")
        mock_urlopen.assert_not_called()

    def test_handles_timeout_error(self):
        config = Namespace(service="discord")

        with (
            patch("ip_notify.discord_data", return_value={"ok": True}),
            patch("ip_notify.urllib.request.urlopen", side_effect=TimeoutError),
            patch("ip_notify.logging.error") as mock_error,
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_error.assert_called_once_with(
            "%s webhook request timed out after 5s", "discord"
        )

    def test_handles_http_error(self):
        config = Namespace(service="discord")
        error = HTTPError(
            url="https://example.com/webhook",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=None,
        )
        error.read = MagicMock(return_value=b"bad payload")

        with (
            patch("ip_notify.discord_data", return_value={"ok": True}),
            patch("ip_notify.urllib.request.urlopen", side_effect=error),
            patch("ip_notify.logging.error") as mock_error,
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_error.assert_called_once_with(
            "Failed to send %s notification: HTTP %s - { %s } ",
            "discord",
            400,
            "bad payload",
        )

    def test_handles_url_error(self):
        config = Namespace(service="discord")
        error = URLError("connection refused")
        error.read = MagicMock(return_value=b"")

        with (
            patch("ip_notify.discord_data", return_value={"ok": True}),
            patch("ip_notify.urllib.request.urlopen", side_effect=error),
            patch("ip_notify.logging.error") as mock_error,
        ):
            ip_notify.send_notification(
                "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
            )

        mock_error.assert_called_once_with(
            "Send %s notification failed due to POST error: %s", "discord", error
        )


class TestMain(unittest.TestCase):
    def test_returns_error_when_webhook_missing(self):
        config = Namespace(ip_cache=Path("/tmp/ip.txt"), webhook=None, test=False)

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip") as mock_get_current_ip,
        ):
            result = ip_notify.main()

        self.assertEqual(result, 1)
        mock_get_current_ip.assert_not_called()

    def test_returns_error_when_current_ip_cannot_be_determined(self):
        config = Namespace(
            ip_cache=Path("/tmp/ip.txt"),
            webhook="https://example.com/webhook",
            test=False,
        )

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip", return_value=None),
            patch("ip_notify.get_last_ip", return_value="5.6.7.8"),
        ):
            result = ip_notify.main()

        self.assertEqual(result, 1)

    def test_sends_notification_on_first_run(self):
        config = Namespace(
            ip_cache=Path("/tmp/ip.txt"),
            webhook="https://example.com/webhook",
            test=False,
        )

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip", return_value="1.2.3.4"),
            patch("ip_notify.get_last_ip", return_value=None),
            patch("ip_notify.send_notification") as mock_send,
            patch("ip_notify.save_current_ip") as mock_save,
        ):
            result = ip_notify.main()

        self.assertEqual(result, 0)
        mock_send.assert_called_once_with(
            "https://example.com/webhook", "1.2.3.4", None, config
        )
        mock_save.assert_called_once_with("1.2.3.4", config.ip_cache)

    def test_sends_notification_in_test_mode_even_without_change(self):
        config = Namespace(
            ip_cache=Path("/tmp/ip.txt"),
            webhook="https://example.com/webhook",
            test=True,
        )

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip", return_value="1.2.3.4"),
            patch("ip_notify.get_last_ip", return_value="1.2.3.4"),
            patch("ip_notify.send_notification") as mock_send,
            patch("ip_notify.save_current_ip") as mock_save,
        ):
            result = ip_notify.main()

        self.assertEqual(result, 0)
        mock_send.assert_called_once_with(
            "https://example.com/webhook", "1.2.3.4", "1.2.3.4", config
        )
        mock_save.assert_called_once_with("1.2.3.4", config.ip_cache)

    def test_sends_notification_when_ip_changes(self):
        config = Namespace(
            ip_cache=Path("/tmp/ip.txt"),
            webhook="https://example.com/webhook",
            test=False,
        )

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip", return_value="1.2.3.4"),
            patch("ip_notify.get_last_ip", return_value="5.6.7.8"),
            patch("ip_notify.send_notification") as mock_send,
            patch("ip_notify.save_current_ip") as mock_save,
        ):
            result = ip_notify.main()

        self.assertEqual(result, 0)
        mock_send.assert_called_once_with(
            "https://example.com/webhook", "1.2.3.4", "5.6.7.8", config
        )
        mock_save.assert_called_once_with("1.2.3.4", config.ip_cache)

    def test_does_nothing_when_ip_is_unchanged(self):
        config = Namespace(
            ip_cache=Path("/tmp/ip.txt"),
            webhook="https://example.com/webhook",
            test=False,
        )

        with (
            patch("ip_notify.get_config", return_value=config),
            patch("ip_notify.setup_logging"),
            patch("ip_notify.get_current_ip", return_value="1.2.3.4"),
            patch("ip_notify.get_last_ip", return_value="1.2.3.4"),
            patch("ip_notify.send_notification") as mock_send,
            patch("ip_notify.save_current_ip") as mock_save,
        ):
            result = ip_notify.main()

        self.assertEqual(result, 0)
        mock_send.assert_not_called()
        mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
