from sqlalchemy import text
from sqlalchemy.orm import relationship

from .arrangement_status import ArrangementStatus
from .users import User
from app.main import db


class Arrangement(db.Model):
    __tablename__ = "arrangements"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    bpm = db.Column(db.Integer, nullable=False)
    tags = db.Column(db.String(1000), nullable=False)
    file_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=text('CURRENT_TIMESTAMP'))
    status = db.Column(db.Enum(ArrangementStatus), default=ArrangementStatus.PENDING, nullable=False)

    user = relationship(User, back_populates="arrangements")
