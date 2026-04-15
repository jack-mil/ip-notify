# [IP Notify](https://codeberg.org/jack-mil/ip-notify)

## Sends a Discord webhook notification when your public IP changes

Explanation: I run a number of services behind a NAT at home which are only 
accessible through a WireGuard VPN. My IP rarely if ever changes, but if it does,
this script will send me a Discord notification so I can update my VPN endpoint
while away from home.

Yes, obviously this problem is solved with a DDNS service, of which there are many.
But, I don't have any public DNS records and only need the IP endpoint for WireGuard.

Runs in a Docker container with `supercronic` on a configurable schedule.

Can just as easily be adapted to run on the host instead.

Makes use of [Mullvad](https://am.i.mullvad.net/ip) or [Proton](https://ip.me) ip-lookup service.

Repo has moved to Codeberg, the Github mirror may not be updated indefinitely. See: [Give up GitHub](https://GiveUpGitHub.org)

## Usage
- The script `ip_notify.py` runs as a oneshot service. It caches the current ip to a file
and checks for differences on next run
- Run as a cron job
- Or run the supplied docker image and/or Compose project (`supercronic` in Docker)

## Args
- `--service` The desired service to send the notification to (`discord | msteams`. Default: `discord`)
- `--webhook` The webhook endpoint (Required)
- `-o | --cache-file` The file to write save the previous ip to (Default: `$XDG_CACHE_HOME/ip_notify_cache`)
- `--test` Send the webhook even if the IP hasn't changed

## Env Vars
Most useful when running in Docker (See `docker-compose.yml`).
```
# The webhook url. Include here or in .env file
WEBHOOK_URL=${WEBHOOK_URL}
# Cron expression used by the container scheduler
SCHEDULE=*/30 * * * *
# The service used to post webhooks to
WEBHOOK_SERVICE=discord
# The color of the Discord Embed in hex
EMBED_COLOR=1bb106
# The link when clicking the Embed author
AUTHOR_URL=https://codeberg.org/jack-mil/ip-notify
# The icon for the Embed and User avatar
ICON_URL=https://1.1.1.1/favicon.ico
# The file (in the container) to store the previous ip
IP_CACHE=/data/ip.txt
# An additional log file (in the container)
LOG_FILE=/data/logs.txt
```

## Service configuration
### Discord
- Select the settings icon of the channel you'd like to receive the webhook in
- Go to "Integrations"
- Click "Webhooks"
- Press the "New Webhook" button
- A new webhook should appear; select this and press the "Copy Webhook URL" button

### Teams
- Press the meatball menu icon (3 dots, horizontal) next to a Teams channel
- Select "Workflows"
- Search for "webhook"
- Select "Send webhook alerts to a channel"
- Configure the desired Teams and channel
- Copy the webhook URL and make sure the workflow is activated

## Developing
- Since this is a simple single-file script, host execution can use any local Python install.
- Dockerfile and an example Docker Compose project are provided if preferred.

> Thanks to these projects for inspiration:
> - https://github.com/timothymiller/cloudflare-ddns
> - https://github.com/teobouvard/turnip

## License
This source code is available for use under the terms of the MIT License. See [LICENSE](./LICENSE)

© Copyright 2023-2026, jack-mil and contributors.
