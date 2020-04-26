from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_restful import abort, Resource
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase, create_session
import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin


def abort_if_users_not_found(users_id):
    session = create_session()
    users = session.query(User).get(users_id)
    if not users:
        abort(404, message=f"User {users_id} not found")


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    login = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def __repr__(self):
        session = create_session()
        for user in session.query(User).all():
            print(user)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class RegisterForm(FlaskForm):
    name = StringField('Ваше имя', validators=[DataRequired()])
    surname = StringField('Ваша фамилия', validators=[DataRequired()])
    login = StringField('Имя пользователя', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class UsersResource(Resource):
    def get(self, users_id):
        abort_if_users_not_found(users_id)
        session = create_session()
        users = session.query(User).get(users_id)
        return jsonify({'users': users.to_dict(only=('name', 'surname', 'about', 'email'))})

    def delete(self, users_id):
        abort_if_users_not_found(users_id)
        session = create_session()
        users = session.query(User).get(users_id)
        session.delete(users)
        session.commit()
        return jsonify({'success': 'OK'})
