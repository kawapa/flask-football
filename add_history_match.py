
from app import create_app, db
from app.models import User
from app.services.matches_services import save_match
from datetime import date

app = create_app()

with app.app_context():

    # Dodaj mecz z 9.03 z zawodnikami o id od 1 do 12
    match_date = date(date.today().year, 3, 9)
    player_ids = [1, 3, 16, 15, 18, 19, 21, 12, 6, 20, 8, 14]
    extra_players = []
    match, is_new_match, team_summary = save_match(match_date, player_ids, extra_players, assign_sequentially=True)
    db.session.commit()
    print(f"Dodano mecz z {match_date} (nowy: {is_new_match}) z zawodnikami o id: {player_ids}")

