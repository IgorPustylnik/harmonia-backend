import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.main.service.websocket_service import handle_notification


class DatabaseListener:
    def __init__(self, db_url, poll_interval=0.5):
        self.db_url = db_url
        self.poll_interval = poll_interval
        self.connection = None
        self.cursor = None
        self.running = True
        self.handle_notification = handle_notification

    def start_listening(self):
        self.connection = psycopg2.connect(self.db_url)
        self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.connection.cursor()
        self.cursor.execute("LISTEN arrangement_changes;")

        try:
            while self.running:
                self.connection.poll()
                while self.connection.notifies:
                    notify = self.connection.notifies.pop(0)
                    self.handle_notification(notify.payload)
                time.sleep(self.poll_interval)
        except (Exception, psycopg2.Error) as e:
            print(f"Error in listener: {e}")
        finally:
            self.stop_listening()

    def stop_listening(self):
        self.running = False
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
