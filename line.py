import logging
import os
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/push'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("LINE_ACCESS_TOKEN")}'
    }

    data = {
        'to': os.getenv("LINE_USERID"),
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        logger.info("Message sent successfully")
    else:
        logger.info(f"Failed to send message. Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
