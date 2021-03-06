from pickle import loads, dumps
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from .db_session import SqlAlchemyBase, create_session
from .categories import Category, CategoryResource
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin


def abort_if_place_not_found(place_id):
    session = create_session()
    place = session.query(Place).get(place_id)
    if not place:
        abort(404, message=f"Place {place_id} not found")


class Place(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'places'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    coords = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    picture = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rating = sqlalchemy.Column(sqlalchemy.Float, default=0.0)
    comments_list = sqlalchemy.Column(sqlalchemy.String, default='')
    site = sqlalchemy.Column(sqlalchemy.String, nullable=True)


class PlaceResource(Resource):
    def get(self, place_id):
        session = create_session()
        place = session.query(Place).get(place_id)
        return place

    def delete(self, place_id):
        abort_if_place_not_found(place_id)
        session = create_session()
        place = session.query(Place).get(place_id)
        session.delete(place)
        session.commit()
        return jsonify({'success': 'OK'})


class PlaceListResource_All(Resource):
    def get(self):
        session = create_session()
        places = session.query(Place).all()
        return places

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', required=True)
        parser.add_argument('name', required=True)
        parser.add_argument('address', required=True)
        parser.add_argument('about', required=True)
        parser.add_argument('rating', required=True, type=float)

        args = parser.parse_args()
        session = create_session()
        place = Place(
            id=args['id'],
            address=args['address'],
            about=args['about'],
            rating=args['rating'],
            name=args['name']
        )
        session.add(place)
        session.commit()
        return jsonify({'success': 'OK'})


class PlaceListResource_ForCateg(Resource):
    def get(self, categ_id):
        session = create_session()
        categ = CategoryResource.get(CategoryResource(), categ_id=categ_id)
        ids = list(map(int, str(categ.places_id).split(',')))
        places = session.query(Place).filter(Place.id.in_(ids)).all()
        return places

    def delete(self, categ_id):
        session = create_session()
        categ = CategoryResource.get(CategoryResource(), categ_id=categ_id)
        ids = list(map(int, str(categ.places_id).split(',')))
        places = session.query(Place).filter(Place.id.in_(ids)).all()
        for place in places:
            PlaceResource.delete(PlaceResource(), place.id)
