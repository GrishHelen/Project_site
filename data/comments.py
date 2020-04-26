from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, FloatField
from wtforms.validators import DataRequired
from pickle import loads, dumps
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from .db_session import SqlAlchemyBase, create_session
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin


def abort_if_comm_not_found(comm_id):
    session = create_session()
    comm = session.query(Comm).get(comm_id)
    if not comm:
        abort(404, message=f"Comm {comm_id} not found")


class Comm(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    text = sqlalchemy.Column(sqlalchemy.String)
    rating = sqlalchemy.Column(sqlalchemy.Float)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    user_name = sqlalchemy.Column(sqlalchemy.String)
    place_id = sqlalchemy.Column(sqlalchemy.Integer)


class AddCommForm(FlaskForm):
    text = TextAreaField('Ваш комментарий', validators=[DataRequired()])
    rating = FloatField('Выставьте оценку (целое число от 0 до 5)')
    submit = SubmitField('Добавить')


class CommResource(Resource):
    def get(self, comm_id):
        abort_if_comm_not_found(comm_id)
        session = create_session()
        comm = session.query(Comm).get(comm_id)
        return comm

    def delete(self, comm_id):
        abort_if_comm_not_found(comm_id)
        session = create_session()
        comm = session.query(Comm).get(comm_id)
        session.delete(comm)
        session.commit()
        return jsonify({'success': 'OK'})


class CommListResource_All(Resource):
    def get(self):
        session = create_session()
        comms = session.query(Comm).all()
        return comms

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True)
        parser.add_argument('text', required=True)
        parser.add_argument('rating', required=True, type=float)

        args = parser.parse_args()
        session = create_session()
        comm = Comm(
            id=args['id'],
            address=args['text'],
            rating=args['rating']
        )
        session.add(comm)
        session.commit()
        return jsonify({'success': 'OK'})


class CommListResource_ForPlace(Resource):
    def get(self, place_id):
        session = create_session()
        comms = session.query(Comm).filter(Comm.place_id == place_id).all()
        return comms

    def delete(self, place_id):
        session = create_session()
        comms = session.query(Comm).filter(Comm.place_id == place_id).all()
        for comm in comms:
            CommResource.delete(self, comm.id)
