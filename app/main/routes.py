from flask import Blueprint, render_template
from flask_login import current_user

# from ..services import build_next_match_context

main = Blueprint("main", __name__)


@main.route("/")
def index():
    # context = build_next_match_context()
    # return render_template("index.html", user=current_user, **context)
    return render_template("index.html", user=current_user)
