# IP Notify

## Sends a webhook notification when your public IP changes

Explanation: I run a number of services behind a NAT at home which are only 
accessible through a WireGuard VPN. My IP rarely if ever changes, but if it does,
this script will send me a Discord notification so I can update my VPN endpoint
while away from home.

Yes, obviously this problem is solved with a DDNS service, of which there are many.
But, I don't have any public DNS records and only need the IP endpoint for WireGaurd.

Runs in a Docker container running cron every 30 minutes.

Can just as easily be adapted to run on the host instead.

Uses Cloudflare's zero-log ip lookup (https://1.1.1.1/cdn-cgi/trace)

## Usage
- The script `ip_notify.py` runs as a oneshot service. It caches the current ip to a file
and checks for differences on next run
- Run as a cron job
- Or run the supplied docker image and compose project (cron in docker)

## Args
- `--service` The desired service to send the notification to. Currently, `discord` and `msteams` are possible options.
- `--webhook` The webhook endpoint (Required)
- `-o | --cache-dir` The file to write save the previous ip to (Default: `$XDG_CONFIG_HOME/ip-notify/old_ip`)
- `--test` Send the webhook even if the IP hasn't changed

## Env Vars
Most useful when running in Docker (See `docker-compose.yml`).
```
# The desired webhook service to use.
WEBHOOK_SERVICE=discord
# The webhook url. Include here or in .env file
WEBHOOK_URL=${WEBHOOK_URL}
# The color of the Discord Embed in hex
EMBED_COLOR=1bb106
# The link when clicking the Embed author
AUTHOR_URL=https://github.com/jack-mil/ip-notify
# The icon for the Embed and User avatar
ICON_URL=https://1.1.1.1/favicon.ico
# The file (in the container) to store the previous ip
IP_CACHE=/data/ip.txt
# An additional log file (in the container)
LOG_FILE=/data/logs.txt
```
## Developing
- Install python requirements with pip from requirements.txt

- Alternatively, a VS Code Dev container config is supplied

- Dockerfile and an example Docker Compose project are provided if preferred

> Thanks to these projects for inspiration:
> - https://github.com/timothymiller/cloudflare-ddns
> - https://github.com/teobouvard/turnip