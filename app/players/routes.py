from flask import Blueprint, flash, redirect, request, url_for, render_template, Response
from flask_login import login_required, current_user
from .. import db
# from ..models import User, Rating
# from ..utils import admin_required
from ..services.players_services import build_user_list_context, parse_rating_values, save_user_rating

players = Blueprint("players", __name__)


@players.route("/players")
@login_required
def list_players():
    context = build_user_list_context(current_user.id)
    return render_template("players/players.html", **context)


@players.route("/players/rate/<int:user_id>", methods=["POST"])
@login_required
def rate_user(user_id):
    if user_id == current_user.id:
        flash("Nie możesz ocenić siebie!")
        return redirect(url_for("players.list_players"))

    try:
        values = parse_rating_values(request.form)
    except (KeyError, ValueError):
        flash("Ocena musi zawierać wartości od 1 do 5 dla każdej kategorii.")
        return redirect(url_for("players.list_players"))

    save_user_rating(user_id, current_user.id, values)
    db.session.commit()
    flash("Ocena zapisana!")
    return redirect(url_for("players.list_players"))


# @players.route("/players/delete/<int:user_id>", methods=["POST"])
# @login_required
# @admin_required
# def delete_user(user_id):
#     user = User.query.get_or_404(user_id)

#     # Delete all ratings where the user is the rater or rated
#     Rating.query.filter((Rating.rater_id == user_id) | (Rating.rated_id == user_id)).delete()

#     db.session.delete(user)
#     db.session.commit()
#     flash("Zawodnik oraz powiązane oceny zostały usunięte.")
#     return redirect(url_for("players.list_players"))


