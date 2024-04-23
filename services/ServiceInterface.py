class WebhookServiceInterface:
    def send_notification(self, url, current_ip, old_ip, config) -> bool:
        pass