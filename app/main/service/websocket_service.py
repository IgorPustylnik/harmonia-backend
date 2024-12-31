import json
import logging

from flask_sock import Sock

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

            if 'user_id' in message:
                user_id = message['user_id']
                if user_id not in clients:
                    clients[user_id] = ws
                    logger.info(f"User {user_id} connected and registered.")

            else:
                ws.send(json.dumps({'error': 'Missing user_id in message'}))

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if user_id in clients:
            clients.pop(user_id, None)
            logger.info(f"User {user_id} disconnected.")


def handle_notification(payload):
    data = json.loads(payload)
    user_id = data.get('user_id')
    if user_id in clients:
        ws = clients[user_id]
        try:
            ws.send(json.dumps({"message": "Data updated", "user_id": user_id}))
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
