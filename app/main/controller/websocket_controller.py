import json
import logging

from flask_sock import Sock
from ..service import vk_api_service

sock = Sock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('websocket')

clients = {}


@sock.route('/websocket')
def websocket_route(ws):
    user_id = None
    try:
        while True:
            data = ws.receive()
            if not data:
                break

            message = json.loads(data)

            if 'access_token' in message:
                access_token = message['access_token']

                try:
                    user_id = vk_api_service.get_user_id(access_token)
                except Exception as e:
                    ws.send(json.dumps({'status': 'fail', 'message': f'{e}'}))
                    return

                if user_id is None:
                    ws.send(json.dumps({'status': 'fail', 'message': 'Missing or invalid Authorization header'}))

                if user_id not in clients:
                    clients[user_id] = ws
                    logger.info(f"User {user_id} connected and registered.")
                    ws.send(json.dumps({'status': 'success', 'message': f'Successfully connected'}))

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws.send(json.dumps({'status': 'fail', 'message': f'{e}'}))
    finally:
        if user_id in clients:
            clients.pop(user_id, None)
            logger.info(f"User {user_id} disconnected.")


def data_updated(user_id):
    if user_id in clients:
        ws = clients[user_id]
        try:
            ws.send(json.dumps({"status": "success", "message": "Data updated"}))
        except Exception as e:
            logger.info(f"Error sending WebSocket message: {e}")
