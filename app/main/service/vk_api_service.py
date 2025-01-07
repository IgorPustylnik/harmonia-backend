import os

import requests

client_id = os.getenv('VK_CLIENT_ID')


def get_user_id(access_token: str) -> int:
    url = "https://id.vk.com/oauth2/user_info"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "access_token": access_token,
        "client_id": client_id
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        user_info = response.json()

        if "user" in user_info and "user_id" in user_info["user"]:
            return int(user_info["user"]["user_id"])
        else:
            raise Exception("Token is invalid")
    except requests.RequestException as e:
        raise Exception(f"VK API request error: {e}")
