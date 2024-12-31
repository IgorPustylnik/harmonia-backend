import os
import threading

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .service.s3_storage_service import S3Storage
from .service.websocket_service import handle_notification, sock
from app.main.service.database.database_listener import DatabaseListener

app = Flask(__name__)
db = SQLAlchemy()
s3_storage = S3Storage()


def create_app() -> Flask:
    app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    database_listener = DatabaseListener(os.getenv("SQLALCHEMY_DATABASE_URI"))
    sock.init_app(app)
    db.init_app(app)

    threading.Thread(target=database_listener.start_listening, daemon=True).start()

    return app
