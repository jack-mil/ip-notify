#!/usr/bin/env python3
#
# /// script
# requires-python = ">=3.11"
# ///


import argparse
import json
import logging
import os
import urllib.request
from argparse import Namespace
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.error import HTTPError, URLError

IP_PROVIDERS = [
    "https://am.i.mullvad.net/ip",  # See: https://mullvad.net/en/check
    "https://ip.me/",  # See: https://ip.me/about
]


def get_args() -> Namespace:
    args = argparse.ArgumentParser()
    args.add_argument(
        "--service",
        type=str,
        help="Service type to send webhook to; discord or msteams (default: discord)",
    )
    args.add_argument(
        "--webhook",
        type=str,
        help="URL of webhook endpoint",
    )
    args.add_argument(
        "-o",
        "--cache-file",
        type=str,
        help="File to store IP",
    )
    args.add_argument(
        "--test",
        action="store_true",
        help="Always send the webhook data",
    )
    return args.parse_args()


def get_config() -> Namespace:
    args = get_args()
    config = Namespace()
    config.test = args.test
    config.service = args.service or os.getenv("WEBHOOK_SERVICE") or "discord"
    config.webhook = args.webhook or os.getenv("WEBHOOK_URL")
    config.embed_color = os.getenv("EMBED_COLOR", "1bb106")
    config.author_url = os.getenv(
        "AUTHOR_URL", "https://codeberg.org/jack-mil/ip-notify"
    )
    config.icon_url = os.getenv("ICON_URL")

    ip_cache_path = args.cache_file or os.getenv("IP_CACHE")
    # Create the default directory if no env var
    if ip_cache_path is None:
        cache_home = os.getenv("XDG_CACHE_HOME")
        if cache_home is None:
            cache_home = os.getenv("HOME") or Path.home()
        ip_cache_path = Path(cache_home, "ip_notify_cache")
    config.ip_cache = Path(ip_cache_path)
    config.ip_cache.parent.mkdir(parents=True, exist_ok=True)
    return config


logger = logging.getLogger()


def setup_logging():
    # debug to rotating file, errors to stderr
    formatter = logging.Formatter("[%(asctime)s] (%(name)s) %(levelname)s: %(message)s")
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)

    log_file = os.getenv("LOG_FILE")
    if log_file is not None:
        file_handler = RotatingFileHandler(
            filename=log_file, maxBytes=5 * 1e3, backupCount=1
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)


def send_notification(webhook_url: str, new_ip: str, old_ip: str, config):
    """Send the webhook POST request directly"""
    match config.service:
        case "discord":
            func = discord_data
        case "msteams":
            func = teams_data
        case err:
            logging.error("Unsupported webhook service %s", err)
            return
    payload = func(config, new_ip, old_ip)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "ip-notify/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as res:
            if res.status == 200:
                logging.info("Sent %s notification", config.service)
            else:
                logging.info(
                    "Sent %s notification (response %s)", config.service, res.status
                )
    except TimeoutError:
        logging.error("%s webhook request timed out after 5s", config.service)
    except HTTPError as exc:
        error_body = exc.read().decode().strip()
        logging.error(
            "Failed to send %s notification: HTTP %s - { %s } ",
            config.service,
            exc.code,
            error_body,
        )
    except URLError as exc:
        error_body = exc.read().decode().strip()
        logging.error(
            "Send %s notification failed due to POST error: %s",
            config.service,
            exc,
        )


def discord_data(config, new_ip: str, old_ip: str) -> dict:
    """Construct payload data for Discord webhook"""
    color_decimal = int(config.embed_color.lstrip("#"), 16)
    payload = {
        "username": "IP Notify",
        "avatar_url": config.author_url,
        "embeds": [
            {
                "title": "IP Address Changed",
                "color": color_decimal,
                "author": {
                    "name": "IP Notify",
                    "url": config.author_url,
                    "icon_url": config.icon_url,
                },
                "fields": [
                    {
                        "name": "New :green_circle:",
                        "value": f"**{new_ip}**",
                        "inline": False,
                    },
                    {
                        "name": "Old :red_circle:",
                        "value": f"~~{old_ip}~~",
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": "Occurred",
                },
                # ISO-8601 timestamp
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
    return payload


def teams_data(config, old_ip: str, new_ip: str) -> dict:
    """Construct webhook data for MS Teams webhook"""
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": "null",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.2",
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Medium",
                            "weight": "Bolder",
                            "text": "IP Address Changed",
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Old:", "value": old_ip},
                                {"title": "New:", "value": new_ip},
                            ],
                        },
                    ],
                },
            }
        ],
    }
    return payload


def get_current_ip(providers: list[str]):
    """Uses Mullvad or Proton VPN trace service to lookup current public IP"""
    for provider in providers:
        with urllib.request.urlopen(provider, timeout=1.5) as res:
            if res.status == 200:
                # both providers return a single line with the ip address
                info = res.read().decode().split("\n")
                current_ip = info[0]

                logging.debug(f"Public ip [{current_ip}] grabbed from [{provider}]")
                return current_ip

            logging.warning(f"Provider error: [{provider}] Response: {res.status}")
    logging.error("FATAL: All providers unavailable. IP lookup failed")


def get_last_ip(ip_file: str):
    """Read old ip from a file"""
    if not ip_file.exists():
        logging.info("No existing ip record found")
        return None
    old_ip = ip_file.read_text().split("\n")[0]
    return old_ip


def save_current_ip(ip: str, ip_file: str):
    """Saves the current public IP to a file"""
    try:
        ip_file.write_text(ip + "\n")
    except OSError as e:
        logger.error(f"Could not save current IP: {e}")


def main() -> int:
    """Run once to check current IP against old IP and notify if changed"""

    config = get_config()
    setup_logging()

    cache_path = config.ip_cache
    url = config.webhook

    if url is None:
        logging.error("Must configure a webhook endpoint using args or env vars")
        return 1

    logging.info("Checking for IP changes")
    new_ip = get_current_ip(IP_PROVIDERS)
    old_ip = get_last_ip(cache_path)

    if new_ip is None:
        logging.error("Could not determine public IP. Task failed")
        return 1

    elif old_ip is None or config.test:
        logging.info(f"First time detected. IP is [{new_ip}]")
        send_notification(url, new_ip, old_ip, config)
        save_current_ip(new_ip, cache_path)

    elif new_ip != old_ip:
        logging.info(f"Public ip changed from {old_ip} to {new_ip}")
        send_notification(url, new_ip, old_ip, config)
        save_current_ip(new_ip, cache_path)

    else:
        logging.info("No change in public IP")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
