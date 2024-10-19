from discord_webhook import DiscordWebhook, DiscordEmbed
from services.ServiceInterface import WebhookServiceInterface


class DiscordWebhookService(WebhookServiceInterface):
    @staticmethod
    def send_notification(url, current_ip, old_ip, config) -> bool:
        webhook = DiscordWebhook(
            url=url, username="IP Notify", avatar_url=config.author_url
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
        return response.ok
        # No idea if pass is still needed here... Not a python expert
        pass
