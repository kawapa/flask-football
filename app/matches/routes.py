from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from .. import db
from ..models import Match, User
from ..services.matches_services import (
    build_match_history_context,
    extract_extra_players,
    MAX_PLAYERS_PER_MATCH,
    get_mondays_range,
    get_upcoming_mondays,
    parse_match_date,
    save_match,
    save_match_result,
)
from ..utils import admin_required

matches = Blueprint("matches", __name__)


@matches.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_match():
    users = User.query.order_by(User.name.asc()).all()
    mondays = get_mondays_range()

    if request.method == "POST":
        selected_users = request.form.getlist("players")
        match_date = request.form.get("match_date", "")

        try:
            extra_players = extract_extra_players(request.form)
        except ValueError as exc:
            flash(str(exc))
            return redirect(url_for("matches.add_match"))

        total_players = len(selected_users) + len(extra_players)

        if total_players > MAX_PLAYERS_PER_MATCH:
            flash(f"Możesz dodać maksymalnie {MAX_PLAYERS_PER_MATCH} zawodników łącznie.")
            return redirect(url_for("matches.add_match"))

        if total_players < 2 or not match_date:
            flash("Wybierz zawodników i datę meczu!")
            return redirect(url_for("matches.add_match"))

        match_date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()

        _, is_new_match, _ = save_match(match_date_obj, selected_users, extra_players)

        db.session.commit()
        flash("Mecz dodany!" if is_new_match else "Skład meczu zaktualizowany!")
        return redirect(url_for("main.index"))

    return render_template("matches/add.html", users=users, mondays=mondays)


@matches.route("/history")
def history():
    matches = build_match_history_context()
    return render_template("matches/history.html", user=current_user, matches=matches)


@matches.route("/<int:match_id>/result", methods=["POST"])
@login_required
@admin_required
def update_result(match_id):
    match = db.session.get(Match, match_id)
    if match is None:
        flash("Nie znaleziono meczu.")
        return redirect(url_for("matches.history"))

    try:
        orange_score = int(request.form.get("orange_score", ""))
        blue_score = int(request.form.get("blue_score", ""))
    except ValueError:
        flash("Wynik musi składać się z liczb całkowitych.")
        return redirect(url_for("matches.history"))

    if orange_score < 0 or blue_score < 0:
        flash("Wynik nie może być ujemny.")
        return redirect(url_for("matches.history"))

    save_match_result(match, orange_score, blue_score)
    db.session.commit()
    flash("Wynik został zapisany.")
    return redirect(url_for("matches.history"))


@matches.route("/delete/<int:match_id>", methods=["POST"])
@login_required
@admin_required
def delete_match(match_id):
    match = db.session.get(Match, match_id)
    if match is None:
        flash("Nie znaleziono meczu.")
        return redirect(url_for("matches.history"))
    db.session.delete(match)
    db.session.commit()
    flash("Mecz został usunięty.")
    return redirect(url_for("matches.history"))