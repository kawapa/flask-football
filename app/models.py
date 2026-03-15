from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    last_login_date = db.Column(db.DateTime)

    ratings_received = db.relationship(
        "Rating", foreign_keys="Rating.rated_id", backref="rated_user", lazy="dynamic")
    ratings_given = db.relationship(
        "Rating", foreign_keys="Rating.rater_id", backref="rater_user", lazy="dynamic")

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


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    players = db.relationship(
        'User', secondary='match_players', backref='matches')
    extra_players = db.Column(db.String(200))
    participants = db.relationship(
        "MatchParticipant",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchParticipant.sort_order",
    )
    result = db.relationship(
        "MatchResult",
        back_populates="match",
        uselist=False,
        cascade="all, delete-orphan",
    )


class MatchParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    extra_name = db.Column(db.String(100), nullable=True)
    average_rating = db.Column(db.Float, nullable=False)
    playmaking_rating = db.Column(db.Float, nullable=False)
    team_color = db.Column(db.String(20), nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    match = db.relationship("Match", back_populates="participants")
    user = db.relationship("User")

    @property
    def display_name(self):
        if self.user is not None:
            return self.user.name
        return self.extra_name

    @property
    def is_extra_player(self):
        return self.user is None


class MatchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False, unique=True)
    orange_score = db.Column(db.Integer, nullable=False)
    blue_score = db.Column(db.Integer, nullable=False)

    match = db.relationship("Match", back_populates="result")


match_players = db.Table('match_players',
                         db.Column('match_id', db.Integer,
                                   db.ForeignKey('match.id')),
                         db.Column('user_id', db.Integer,
                                   db.ForeignKey('user.id'))
                         )
