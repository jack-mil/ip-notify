# IP Notify

## Sends a Discord webhook notification when your public IP changes

Explanation: I run a number of services behind a NAT at home which are only 
accessible through a WireGuard VPN. My IP rarely if ever changes, but it it does,
this script will send me a Discord notification so I can update my VPN endpoint
while away from home.

Yes, obviously this problem is solved with a DDNS service, of which there are many.
But, I don't have any public DNS records and only need the IP endpoint for WireGaurd.

Runs in a Docker container running cron every 30 minutes.

Can just as easily be adapted to run on the host instead.

## Usage
- The script `ip_notify.py` runs as a oneshot service. It caches the current ip to a file
and checks for differences on next run
- Run as a cron job
- Or run the supplied docker image and compose project (cron in docker)

## Developing
- Install python requirements with pip from requirements.txt

- Alternatively, a VS Code Dev container config is supplied

- Dockerfile and an example Docker Compose project are provided if preferred

> Thanks to these projects for inspiration:
> - https://github.com/timothymiller/cloudflare-ddns
> - https://github.com/teobouvard/turnip