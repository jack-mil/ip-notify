#!/usr/bin/env python3

import requests
import os
import logging
from logging.handlers import RotatingFileHandler
from discord_webhook import DiscordWebhook, DiscordEmbed
import argparse
from argparse import Namespace

IP_PROVIDERS = [
    # "http://ifconfig.me",
    # "http://ip.me",
    "https://1.1.1.1/cdn-cgi/trace",
    "https://1.0.0.1/cdn-cgi/trace",
]

def get_args() -> Namespace:
    args = argparse.ArgumentParser()
    args.add_argument("--webhook", type=str)
    args.add_argument("-o", "--cache-dir", type=str, required=False)
    return args.parse_args()

def get_config() -> Namespace:
    args = get_args()
    config = Namespace()
    config.webhook = args.webhook or os.getenv("WEBHOOK_URL")
    config.embed_color = os.getenv("EMBED_COLOR", "1bb106")
    config.author_url = os.getenv("AUTHOR_URL", "https://github.com/jack-mil")
    config.icon_url = os.getenv("ICON_URL", "https://1.1.1.1/favicon.ico")

    config.ip_cache =  args.cache_dir or os.getenv("IP_CACHE")
    # Create the default directory if no env var
    if config.ip_cache is None:
        cache_home = os.path.join(
            os.getenv("XDG_CONFIG_HOME") or os.environ["HOME"], ".config", "ip-notify"
        )
        os.makedirs(cache_home, exist_ok=True)
        config.ip_cache = os.path.join(cache_home, "old_ip")
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
        file_handler = RotatingFileHandler(filename=log_file, maxBytes=5 * 1e3, backupCount=1)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)



def send_notification(webhook_url, current_ip, old_ip, config):
    webhook = DiscordWebhook(
        url=webhook_url, username="IP Notify", avatar_url=config.author_url
    )
    # Create and format the embed
    embed = DiscordEmbed(title="IP Address Changed", color=config.embed_color)
    embed.set_author(
        name="IP Notify",
        url=config.author_url,
        icon_url=config.icon_url,
    )

    # Add embed fields with Discord formatting
    embed.add_embed_field(name="New :green_circle:", value=f"**{current_ip}**")
    embed.add_embed_field(name="Old :red_circle:", value=f"~~{old_ip}~~")
    # Set footer timestamp to now
    embed.set_footer(text="Occured")
    embed.set_timestamp()

    # Add the embed
    webhook.add_embed(embed)

    # Send the webhook notification
    response = webhook.execute()
    logging.info("Sent discord notification")


def get_current_ip(providers: list[str]):
    """Uses Cloudflare trace service to lookup current public IP"""
    for provider in providers:
        res = requests.get(provider, allow_redirects=False)
        if res.status_code == requests.codes.ok:
            info = res.text.split("\n")
            info.pop()  # Removes empty string at end of list
            current_ip = dict(s.split("=") for s in info)["ip"]

            logging.debug(f"Public ip [{current_ip}] grabbed from [{provider}]")
            return current_ip

        logging.warning(f"Provider error: [{provider}] Response: {res.status_code}")
    logging.error("FATAL: All providers unavailable. IP lookup failed")


def get_last_ip(ip_file: str):
    """Read old ip from a file"""
    if not os.path.isfile(ip_file):
        logging.info("No existing ip record found")
        return None
    try:
        with open(ip_file, "r") as f:
            old_ip = f.read()
            return old_ip
    except OSError as e:
        logging.error(f"OSERROR: Reading saved ip file: {e}")


def save_current_ip(ip: str, ip_file: str):
    """Saves the current public IP to a file"""
    try:
        with open(ip_file, "w") as f:
            f.write(ip)
    except OSError as e:
        logger.error(f"OSERROR: Could not save current IP: {e}")


if __name__ == "__main__":
    """Run once to check current IP against old IP and notify if changed"""

    config = get_config()
    setup_logging()

    cache_path = config.ip_cache
    url = config.webhook
    

    if url is None:
        logging.error("Must configure a Discord Webhook endpoint using args or env vars")
        exit(1)

    logging.info(f"Checking for IP changes")
    current = get_current_ip(IP_PROVIDERS)
    old = get_last_ip(cache_path)

    if current is None:
        logging.error("Could not determine public IP. Task failed")

    elif old is None:
        logging.info(f"First time detected. IP is [{current}]")
        send_notification(
            webhook_url=url, current_ip=current, old_ip="Unknown", config=config
        )
        save_current_ip(current, cache_path)

    elif current != old:
        logging.info(f"Public ip changed from {old} to {current}")
        send_notification(
            webhook_url=url, current_ip=current, old_ip=old, config=config
        )
        save_current_ip(current, cache_path)

    else:
        logging.info("No change in public IP")
