import datetime
import logging
import os
import uuid

from sqlalchemy import or_, and_

from app.main import db, app, s3_storage
from app.main.model.arrangement_status import ArrangementStatus
from app.main.model.arrangements import Arrangement
from typing import Dict, Tuple

from app.main.service import music_gen_service
from app.main.util import converter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('arrangement_service')

per_page = int(os.getenv('ARRANGEMENTS_PER_PAGE'))
host_url = os.getenv("HOST_URL")


def generate_music(arrangement_id: int, drums_file: bytes, bpm: int, tags: str, completion):
    arrangement = None
    try:
        file_response, file_status = music_gen_service.create(drums_file=drums_file, bpm=bpm, tags=tags)

        arrangement = get_arrangement(arrangement_id)

        if file_status != 200:
            arrangement.status = ArrangementStatus.FAILED
        elif arrangement:
            arrangement.status = ArrangementStatus.COMPLETED
            arrangement.file_name = uuid.uuid4().hex
            s3_storage.upload(file_response, arrangement.file_name)

        update_arrangement(arrangement)
        completion()
    except Exception as e:
        if arrangement:
            arrangement.status = ArrangementStatus.FAILED
            update_arrangement(arrangement)
            completion()
        logger.error(f"Error generating music or updating arrangement: {e}")


def add_arrangement(data: Dict[str, str]) -> Tuple[Dict[str, str], int]:
    try:
        new_arrangement = Arrangement(
            user_id=data["user_id"],
            name=data["name"],
            bpm=data["bpm"],
            tags=data["tags"],
            file_name=data.get("file_name"),
            status=ArrangementStatus(data.get("status", "PENDING")),
            created_at=datetime.datetime.utcnow()
        )
        if _save_changes(new_arrangement):
            return {"status": "success",
                    "message": "Arrangement added successfully.",
                    "id": new_arrangement.id}, 201
        return {"status": "fail", "message": "Error adding arrangement."}, 500
    except Exception as e:
        logger.error(f"Error adding arrangement: {e}")
        return {"status": "fail", "message": "Error adding arrangement."}, 500


def get_arrangement(arrangement_id: int) -> Arrangement:
    with app.app_context():
        try:
            return Arrangement.query.filter_by(id=arrangement_id).first()
        except Exception as e:
            logger.error(f"Error fetching arrangement: {e}")
            return None


def update_arrangement(arrangement: Arrangement) -> Tuple[Dict[str, str], int]:
    with app.app_context():
        try:
            arrangement_in_db = Arrangement.query.filter_by(id=arrangement.id).first()
            if arrangement_in_db:
                arrangement_in_db.name = arrangement.name
                arrangement_in_db.status = arrangement.status
                arrangement_in_db.file_name = arrangement.file_name

                if _save_changes(arrangement_in_db):
                    return {"status": "success", "message": "Arrangement updated successfully."}, 200
            return {"status": "fail", "message": "Arrangement not found."}, 404
        except Exception as e:
            logger.error(f"Error updating arrangement: {e}")
            return {"status": "fail", "message": "Error updating arrangement."}, 500


def delete_arrangement(arrangement_id: int) -> Tuple[Dict[str, str], int]:
    try:
        arrangement = Arrangement.query.filter_by(id=arrangement_id).first()
        if arrangement:
            db.session.delete(arrangement)
            db.session.commit()
            return {"status": "success", "message": "Arrangement deleted successfully."}, 200
        else:
            return {"status": "fail", "message": "Arrangement not found."}, 404
    except Exception as e:
        logger.error(f"Error deleting arrangement: {e}")
        db.session.rollback()
        return {"status": "fail", "message": "Error deleting arrangement."}, 500


def get_user_arrangements(user_id: int, page: int, search_query: str) -> Tuple[Dict, int]:
    try:
        search_terms = [f"%{word}%" for word in search_query.split()] if search_query else []

        arrangements_query = Arrangement.query.filter(
            Arrangement.user_id == user_id
        )

        if search_terms:
            search_conditions = [
                or_(
                    Arrangement.name.ilike(term),
                    Arrangement.tags.ilike(term)
                ) for term in search_terms
            ]
            arrangements_query = (arrangements_query
                                  .filter(and_(*search_conditions))
                                  .order_by(Arrangement.created_at.desc())
                                  )

        paginated_arrangements = arrangements_query.paginate(page=page, per_page=per_page, error_out=False)
        arrangements = list(map(lambda a: converter.arrangement_to_dict(a), paginated_arrangements.items))

        if len(arrangements) == 0:
            return {"error": "Nothing found"}, 404

        next_page_url = f"{host_url}/api/arrangements/?page={page + 1 if paginated_arrangements.has_next else None}"
        prev_page_url = f"{host_url}/api/arrangements/?page={page - 1 if paginated_arrangements.has_prev else None}"

        if search_query:
            next_page_url += f"&search_query={search_query}"
            prev_page_url += f"&search_query={search_query}"

        result = {
            'count': paginated_arrangements.total,
            'pages': paginated_arrangements.pages,
            'next': next_page_url if paginated_arrangements.has_next else None,
            'prev': prev_page_url if paginated_arrangements.has_prev else None,
            'results': arrangements
        }

        return result, 200

    except Exception as e:
        logger.error(f"Error fetching user arrangements: {e}")
        return {'error': 'An error occurred while fetching arrangements.'}, 500


def _save_changes(data) -> bool:
    try:
        db.session.add(data)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {e}")
        db.session.rollback()
        return False
