import requests

import ServiceInterface


# Inspiration from https://stackoverflow.com/questions/59371631/send-automated-messages-to-microsoft-teams-using-python

class TeamsWebhookService(ServiceInterface.WebhookServiceInterface):
    def send_notification(self, url, current_ip, old_ip, config) -> bool:
        jsonData = {
            "text": "IP address change detected: \n Old: %s \n New: %s" % (old_ip, current_ip)
        }
        result = requests.post(url, json=jsonData)
        return result.ok
        # No idea if pass is still needed here... Not a python expert
        pass
