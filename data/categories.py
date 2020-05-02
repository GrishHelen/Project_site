from pickle import loads, dumps
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from .db_session import SqlAlchemyBase, create_session
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin


def abort_if_category_not_found(categ_id):
    session = create_session()
    categ = session.query(Category).get(categ_id)
    if not categ:
        abort(404, message=f"Category {categ_id} not found")


class Category(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'categories'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    places_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)


class CategoryResource(Resource):
    def get(self, categ_id):
        session = create_session()
        categ = session.query(Category).get(categ_id)
        return categ

    def delete(self, categ_id):
        abort_if_category_not_found(categ_id)
        session = create_session()
        categ = session.query(Category).get(categ_id)
        session.delete(categ)
        session.commit()
        return jsonify({'success': 'OK'})


class CategoryListResource(Resource):
    def get(self):
        session = create_session()
        categs = session.query(Category).all()
        return categs

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True)
        parser.add_argument('name', required=True)
        parser.add_argument('places_id', required=True)

        args = parser.parse_args()
        session = create_session()
        categ = Category(
            id=args['id'],
            name=args['name'],
            places_id=args['places_id']
        )
        session.add(categ)
        session.commit()
        return jsonify({'success': 'OK'})
