from datetime import date, datetime, timedelta
from itertools import combinations

from sqlalchemy import func

from .. import db
from ..models import Rating, User

RATING_FIELDS = (
    "attack",
    "defense",
    "return_to_defense",
    "mobility",
    "playmaking",
)

def build_user_list_context(rater_id):
    users = User.query.order_by(User.name.asc()).all()
    my_ratings = _get_existing_ratings_by_rater(rater_id)
    for user in users:
        my_ratings.setdefault(user.id, None)

    return {
        "users": users,
        "rankings": _get_user_rankings(users),
        "my_ratings": my_ratings,
    }

def parse_rating_values(form_data):
    values = {field: int(form_data[field]) for field in RATING_FIELDS}
    for field, value in values.items():
        if value < 1 or value > 5:
            raise ValueError(f"Pole {field} musi mieć wartość od 1 do 5.")
    return values


def save_user_rating(rated_id, rater_id, values):
    rating = Rating.query.filter_by(rated_id=rated_id, rater_id=rater_id).first()
    if rating is None:
        rating = Rating(rated_id=rated_id, rater_id=rater_id, **values)
        db.session.add(rating)
        return rating, True

    for field, value in values.items():
        setattr(rating, field, value)
    return rating, False

def _get_existing_ratings_by_rater(rater_id):
    ratings = Rating.query.filter_by(rater_id=rater_id).all()
    return {
        rating.rated_id: {field: getattr(rating, field) for field in RATING_FIELDS}
        for rating in ratings
    }

def _get_user_rankings(users):
    ranking_rows = db.session.query(
        Rating.rated_id,
        func.avg(
            (
                Rating.attack
                + Rating.defense
                + Rating.return_to_defense
                + Rating.mobility
                + Rating.playmaking
            )
            / 5
        ),
    ).group_by(Rating.rated_id).all()

    rankings = {rated_id: round(average, 2) for rated_id, average in ranking_rows}
    for user in users:
        rankings.setdefault(user.id, None)

    return rankings