from sqlalchemy.orm import relationship

from app.main import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    arrangements = relationship("Arrangement", back_populates="user")
