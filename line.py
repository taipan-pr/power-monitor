import os
import requests


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
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
