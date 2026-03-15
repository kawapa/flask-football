from datetime import date, datetime, timedelta

from .. import db
from ..models import Match, MatchParticipant, MatchResult, User
from .common_services import (
    DEFAULT_AVERAGE_RATING,
    DEFAULT_PLAYMAKING_RATING,
    TEAM_ORANGE,
    TEAM_BLUE,
    build_team_summary,
    count_high_playmakers,
    generate_balanced_teams,
    get_user_rating_summaries,
    get_users_by_ids,
)

MAX_PLAYERS_PER_MATCH = 12
EXTRA_PLAYER_FIELDS = 4


def get_upcoming_mondays(limit=4, from_date=None):
    current_date = from_date or date.today()
    first_monday = current_date + timedelta(days=(7 - current_date.weekday()) % 7)
    return [first_monday + timedelta(days=7 * offset) for offset in range(limit)]


def get_mondays_range(from_date=None):
    current_date = from_date or date.today()
    start_date = current_date - timedelta(weeks=3)
    end_date = current_date + timedelta(weeks=3)
    mondays = []
    while start_date <= end_date:
        if start_date.weekday() == 0:
            mondays.append(start_date)
        start_date += timedelta(days=1)
    return mondays


def parse_match_date(raw_date):
    return datetime.strptime(raw_date, "%Y-%m-%d").date()


def extract_extra_players(form_data, field_count=EXTRA_PLAYER_FIELDS):
    extra_players = []
    for index in range(1, field_count + 1):
        name = form_data.get(f"extra_player_name{index}", "").strip()
        rating_raw = form_data.get(f"extra_player_rating{index}", "").strip()

        if not name and not rating_raw:
            continue

        if not name or not rating_raw:
            raise ValueError("Każdy niezarejestrowany zawodnik musi mieć imię i średnią ocenę.")

        try:
            average_rating = float(rating_raw.replace(",", "."))
        except ValueError as exc:
            raise ValueError("Średnia ocena musi być liczbą od 1 do 5.") from exc

        if average_rating < 1 or average_rating > 5:
            raise ValueError("Średnia ocena musi być w zakresie od 1 do 5.")

        rounded_rating = round(average_rating, 2)
        extra_players.append(
            {
                "name": name,
                "average_rating": rounded_rating,
                "playmaking_rating": rounded_rating,
                "user": None,
                "user_id": None,
                "is_extra": True,
            }
        )

    return extra_players


def build_registered_player_pool(selected_user_ids):
    users = get_users_by_ids(selected_user_ids)
    summaries = get_user_rating_summaries([user.id for user in users])
    player_pool = []

    for user in users:
        summary = summaries.get(
            user.id,
            {
                "average_rating": DEFAULT_AVERAGE_RATING,
                "playmaking_rating": DEFAULT_PLAYMAKING_RATING,
            },
        )
        player_pool.append(
            {
                "name": user.name,
                "average_rating": summary["average_rating"],
                "playmaking_rating": summary["playmaking_rating"],
                "user": user,
                "user_id": user.id,
                "is_extra": False,
            }
        )

    return player_pool


def split_extra_players(raw_names):
    if not raw_names:
        return []
    return [name.strip() for name in raw_names.split(",") if name.strip()]


def build_legacy_extra_players(raw_names):
    return [
        {
            "name": name,
            "average_rating": DEFAULT_AVERAGE_RATING,
            "playmaking_rating": DEFAULT_PLAYMAKING_RATING,
            "user": None,
            "user_id": None,
            "is_extra": True,
        }
        for name in split_extra_players(raw_names)
    ]


def build_match_player_pool(selected_user_ids, extra_players):
    return build_registered_player_pool(selected_user_ids) + extra_players


def save_match(match_date, selected_user_ids, extra_players):
    match = Match.query.filter_by(date=match_date).first()
    is_new_match = match is None

    if is_new_match:
        match = Match(date=match_date)
        db.session.add(match)

    selected_users = get_users_by_ids(selected_user_ids)
    team_summary = generate_balanced_teams(build_match_player_pool(selected_user_ids, extra_players))

    match.players = selected_users
    match.extra_players = ", ".join(player["name"] for player in extra_players)
    match.participants = []

    sort_order = 0
    for team_color, team_players in ((TEAM_ORANGE, team_summary["orange_team"]), (TEAM_BLUE, team_summary["blue_team"])):
        for player in team_players:
            participant = MatchParticipant(
                team_color=team_color,
                average_rating=player["average_rating"],
                playmaking_rating=player["playmaking_rating"],
                sort_order=sort_order,
            )
            if player["user"] is not None:
                participant.user = player["user"]
            else:
                participant.extra_name = player["name"]
            match.participants.append(participant)
            sort_order += 1

    return match, is_new_match, team_summary


def build_match_history_context():
    matches = Match.query.order_by(Match.date.desc()).all()
    history = []
    for match in matches:
        history.append(
            {
                "match": match,
                **get_match_team_summary(match),
                "result": match.result,
            }
        )
    return history


def save_match_result(match, orange_score, blue_score):
    if match.result is None:
        match.result = MatchResult(orange_score=orange_score, blue_score=blue_score)
        return match.result

    match.result.orange_score = orange_score
    match.result.blue_score = blue_score
    return match.result


def serialize_participant(participant):
    return {
        "name": participant.display_name,
        "average_rating": round(participant.average_rating, 2),
        "playmaking_rating": round(participant.playmaking_rating, 2),
        "is_extra": participant.is_extra_player,
    }


def get_match_team_summary(match):
    if match.participants:
        orange_team = [serialize_participant(p) for p in match.participants if p.team_color == TEAM_ORANGE]
        blue_team = [serialize_participant(p) for p in match.participants if p.team_color == TEAM_BLUE]
        return build_team_summary(orange_team, blue_team, count_high_playmakers(orange_team + blue_team) >= 2)

    legacy_pool = build_registered_player_pool([u.id for u in match.players]) + build_legacy_extra_players(match.extra_players)
    return generate_balanced_teams(legacy_pool)


def get_next_match():
    return Match.query.filter(Match.date >= date.today()).order_by(Match.date.asc()).first()


def build_next_match_context():
    next_match = get_next_match()
    if next_match is None:
        return {
            "next_match": None,
            "orange_team": [],
            "blue_team": [],
            "orange_average": None,
            "blue_average": None,
            "playmaker_constraint_applied": False,
            "result": None,
        }

    team_summary = get_match_team_summary(next_match)
    return {
        "next_match": next_match,
        **team_summary,
        "result": next_match.result,
    }
