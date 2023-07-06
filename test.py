import unittest
import sys
from unittest import mock
import logging

target = __import__("ip_notify")

IP_PROVIDERS = [
    # "http://ifconfig.me",
    # "http://ip.me",
    "https://1.1.1.1/cdn-cgi/trace",
    "https://1.0.0.1/cdn-cgi/trace",
]

logger = logging.getLogger()
logger.level = logging.DEBUG
formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(levelname)s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TestSendWebhook(unittest.TestCase):
    def test_send(self):
        url = "https://discord.com/api/webhooks/1126211400243613767/U00LoWTqQvCp8ArMT_an1bX6MqVff9jOJbPU2jKvF1fMOntKEa3n7QvFLSu28JHBUJPP"
        target.send_notification(url, "123.456.789", "456.231.789")
        # Passes if no errors after this


class TestGetIP(unittest.TestCase):
    def get_valid(self):
        target.get_current_ip(IP_PROVIDERS)

    def get_invalid(self):
        target.get_current_ip(["https://1.1.1.1/returns/404/error"])

    def get_fallback(self):
        target.get_current_ip(
            ["https://1.1.1.1/returns/404/error", "https://1.0.0.1/cdn-cgi/trace"]
        )


if __name__ == "__main__":
    unittest.main()
