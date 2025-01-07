import logging
from typing import Dict, Tuple

from app.main import db
from app.main.model.users import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('user_service')


def register_user(user_id: int) -> Tuple[Dict[str, str], int]:
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            new_user = User(id=user_id)
            save_changes(new_user)
            return {"status": "success", "message": "User registered successfully."}, 201
        else:
            return {"status": "fail", "message": "User already exists."}, 403
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        return {"status": "fail", "message": "Error during registration."}, 500


def get_user(user_id: int) -> User:
    try:
        return User.query.filter_by(id=user_id).first()
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return None


def delete_user(user_id: int) -> Tuple[Dict[str, str], int]:
    try:
        user = User.query.filter_by(id=user_id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            return {"status": "success", "message": "User deleted successfully."}, 200
        else:
            return {"status": "fail", "message": "User not found."}, 404
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.session.rollback()
        return {"status": "fail", "message": "Error deleting user."}, 500


def save_changes(data) -> None:
    try:
        db.session.add(data)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error saving changes: {e}")
        db.session.rollback()
