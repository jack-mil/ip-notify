# IP Notify

## Sends a Discord webhook notification when your public IP changes

Explaination: I run a number of services behind a NAT at home which are only 
accessable through a WireGuard VPN. My IP rarely if ever changes, but it it does,
this script will send me a Discord notification so I can update my VPN endpoint
while away from home.

Yes, obviously this problem is solved with a DDNS service, of which there are many.
But, I don't have any public DNS records and only need the IP endpoint for WireGaurd.

Runs in a Docker container running cron every 30 minutes.

Can just as easily be adapted to run on the host instead.


> Thanks to these projects for inspiration:
> - https://github.com/timothymiller/cloudflare-ddns
> - https://github.com/teobouvard/turnip