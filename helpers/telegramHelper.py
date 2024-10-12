import os
import requests
import json

class TelegramBotHelper:

    def __init__(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        self.logging_chat_id = config['telegram_chat_id_logging']
        self.results_chat_id = config['telegram_chat_id_results']
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')  # Still use .env for the token

    def send_message(self, chat_id, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"  # Enable Markdown formatting
        }
        response = requests.post(url, data=data)
        return response

    def send_log(self, message):
        """Send a log message to the logging chat."""
        self.send_message(self.logging_chat_id, message)

    def send_result(self, message):
        """Send a result message to the results chat."""
        self.send_message(self.results_chat_id, message)
