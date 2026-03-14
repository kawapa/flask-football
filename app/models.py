from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    last_login_date = db.Column(db.DateTime)

    # ratings_received = db.relationship(
    #     "Rating", foreign_keys="Rating.rated_id", backref="rated_user", lazy="dynamic")
    # ratings_given = db.relationship(
    #     "Rating", foreign_keys="Rating.rater_id", backref="rater_user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rated_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    attack = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Integer, nullable=False)
    return_to_defense = db.Column(db.Integer, nullable=False)
    mobility = db.Column(db.Integer, nullable=False)
    playmaking = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    __table_args__ = (db.UniqueConstraint(
        "rated_id", "rater_id", name="unique_rating"),)