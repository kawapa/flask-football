from itertools import combinations

from sqlalchemy import func

from .. import db
from ..models import Rating, User

TEAM_ORANGE = "orange"
TEAM_BLUE = "blue"
DEFAULT_AVERAGE_RATING = 3.0
DEFAULT_PLAYMAKING_RATING = 3.0
HIGH_PLAYMAKER_THRESHOLD = 4.0
RATING_FIELDS = (
    "attack",
    "defense",
    "return_to_defense",
    "mobility",
    "playmaking",
)


def get_users_by_ids(user_ids):
    normalized_ids = [int(user_id) for user_id in user_ids]
    if not normalized_ids:
        return []

    users = User.query.filter(User.id.in_(normalized_ids)).all()
    user_map = {user.id: user for user in users}
    return [user_map[user_id] for user_id in normalized_ids if user_id in user_map]


def get_user_rating_summaries(user_ids=None):
    query = db.session.query(
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
        func.avg(Rating.playmaking),
    ).group_by(Rating.rated_id)

    if user_ids:
        query = query.filter(Rating.rated_id.in_(user_ids))

    return {
        rated_id: {
            "average_rating": round(average_rating, 2),
            "playmaking_rating": round(playmaking_rating, 2),
        }
        for rated_id, average_rating, playmaking_rating in query.all()
    }


def team_average(players):
    if not players:
        return 0.0
    return round(sum(player["average_rating"] for player in players) / len(players), 2)


def team_playmaking_average(players):
    if not players:
        return 0.0
    return round(sum(player["playmaking_rating"] for player in players) / len(players), 2)


def count_high_playmakers(players):
    return sum(player["playmaking_rating"] >= HIGH_PLAYMAKER_THRESHOLD for player in players)


def build_team_summary(orange_team, blue_team, playmaker_constraint_applied):
    return {
        "orange_team": orange_team,
        "blue_team": blue_team,
        "orange_average": team_average(orange_team),
        "blue_average": team_average(blue_team),
        "orange_playmaking_average": team_playmaking_average(orange_team),
        "blue_playmaking_average": team_playmaking_average(blue_team),
        "playmaker_constraint_applied": playmaker_constraint_applied,
    }


def generate_balanced_teams(player_pool):
    if not player_pool:
        return build_team_summary([], [], False)

    if len(player_pool) == 1:
        return build_team_summary(player_pool, [], False)

    player_count = len(player_pool)
    playmaker_constraint_applied = count_high_playmakers(player_pool) >= 2
    candidate_sizes = {player_count // 2, player_count - (player_count // 2)}
    all_indices = list(range(player_count))
    fixed_index = 0
    remaining_indices = all_indices[1:]
    best_choice = None
    best_score = None

    for orange_size in candidate_sizes:
        if orange_size < 1 or orange_size >= player_count:
            continue

        for combo in combinations(remaining_indices, orange_size - 1):
            orange_indices = {fixed_index, *combo}
            blue_indices = [index for index in all_indices if index not in orange_indices]
            orange_team = [player_pool[index] for index in sorted(orange_indices)]
            blue_team = [player_pool[index] for index in blue_indices]

            orange_average = team_average(orange_team)
            blue_average = team_average(blue_team)
            orange_playmakers = count_high_playmakers(orange_team)
            blue_playmakers = count_high_playmakers(blue_team)
            orange_playmaking_average = team_playmaking_average(orange_team)
            blue_playmaking_average = team_playmaking_average(blue_team)

            violates_playmaker_rule = (
                playmaker_constraint_applied and (orange_playmakers == 0 or blue_playmakers == 0)
            )

            score = (
                1 if violates_playmaker_rule else 0,
                abs(orange_average - blue_average),
                abs(orange_playmaking_average - blue_playmaking_average),
                abs(
                    sum(player["average_rating"] for player in orange_team)
                    - sum(player["average_rating"] for player in blue_team)
                ),
            )

            if best_score is None or score < best_score:
                best_score = score
                best_choice = (orange_team, blue_team)

    orange_team, blue_team = best_choice
    return build_team_summary(orange_team, blue_team, playmaker_constraint_applied)
