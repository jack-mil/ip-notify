import requests
from services.ServiceInterface import WebhookServiceInterface


# Inspiration from https://stackoverflow.com/questions/59371631/send-automated-messages-to-microsoft-teams-using-python

class TeamsWebhookService(WebhookServiceInterface):
    @staticmethod
    def send_notification(url, current_ip, old_ip, config) -> bool:
        json_data = TeamsWebhookService.get_card_data(current_ip, old_ip)
        result = requests.post(url, json=json_data)
        return result.ok
        # No idea if pass is still needed here... Not a python expert
        pass

    @staticmethod
    def get_card_data(current_ip, old_ip):
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType":"application/vnd.microsoft.card.adaptive",
                    "contentUrl": "null",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "version": "1.6",
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Medium",
                                "weight": "Bolder",
                                "text": "IP change detected"
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Old:",
                                        "value": old_ip
                                    },
                                    {
                                        "title": "New:",
                                        "value": current_ip
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
