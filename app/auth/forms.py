from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from ..models import User


class LoginForm(FlaskForm):
    username = StringField("Nazwa użytkownika", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Hasło", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Zaloguj się")


class RegisterForm(FlaskForm):
    username = StringField(
        "Nazwa użytkownika (do logowania)",
        validators=[DataRequired(), Length(min=3, max=50)],
    )
    name = StringField("Imię i nazwisko ", validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField("Hasło", validators=[DataRequired(), Length(min=3, max=128)])
    submit = SubmitField("Zarejestruj się")

    def validate_username(self, field):
        existing_user = User.query.filter_by(username=field.data.strip()).first()
        if existing_user is not None:
            raise ValidationError("Użytkownik o takiej nazwie już istnieje.")
