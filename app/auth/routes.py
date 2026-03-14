from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required

from ..models import User
from .forms import LoginForm

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower().strip()).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.index"))

        flash("Nieprawidłowa nazwa użytkownika lub hasło")

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
