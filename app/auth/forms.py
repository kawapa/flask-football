from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Nazwa użytkownika", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Hasło", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Zaloguj się")
