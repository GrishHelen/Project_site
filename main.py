from flask import Flask, abort, jsonify, make_response
import sys
import sqlite3
import requests
from data import db_session
from data import __all_models
from data.users import User, RegisterForm, LoginForm
from data.places import Place, PlaceListResource_All, PlaceListResource_ForCateg, PlaceResource
from data.categories import Category, CategoryResource, CategoryListResource
from data.comments import Comm, CommResource, CommListResource_All, CommListResource_ForPlace, AddCommForm
from data.db_session import create_session
from flask import Flask, render_template, redirect, make_response, request
from flask_login import LoginManager, logout_user, login_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def get_coords_for_flace(adres):
    adres = '+'.join(adres.split())
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&" \
                       f"geocode={adres}&format=json"
    response = requests.get(geocoder_request)
    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        coords = ','.join(toponym["Point"]["pos"].split())
        print(coords)
        return coords
    else:
        return ''


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


def main():
    db_session.global_init("db/blogs.sqlite")
    app.run(port=8086, host='127.0.0.1')


@app.route("/")
@app.route("/info")
def info():
    return render_template("info.html", title='Историческая Москва')


@app.route("/main")
@app.route("/index")
def index():
    places = PlaceListResource_All.get(PlaceListResource_All())
    for place in places:
        place.rating = round(float(place.rating))
    # print(places)
    return render_template("index.html", title='Историческая Москва', places=places)


@app.route("/one_place/<place_id>")
def one_place(place_id):
    categs = CategoryListResource.get(CategoryListResource())
    categ_list = []
    for cat in categs:
        if str(place_id) in str(cat.places_id).split(','):
            categ_list.append(cat.name)
    categ_list = '; '.join(categ_list)
    place = PlaceResource.get(PlaceResource(), place_id)
    comments = CommListResource_ForPlace.get(CommListResource_ForPlace(), place_id)
    return render_template('one_place.html', title=place.name, place=place, comms=comments, categ_list=categ_list)


@app.route("/one_category/<categ_id>")
def one_category(categ_id):
    categ = CategoryResource.get(CategoryResource(), categ_id)
    places = PlaceListResource_ForCateg.get(PlaceListResource_ForCateg(), categ_id)
    return render_template('one_category.html', title=categ.name, categ=categ, places=places)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            email=form.email.data,
            name=form.name.data,
            surname=form.surname.data,
            login=form.login.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/search')
def search(places=[]):
    return render_template("search.html", title='Поиск', places=places)


@app.route('/find_it', methods=["POST"])
def find_it():
    field = request.form["stolb"]
    what = request.form["what"]
    session = create_session()
    pls = []
    try:
        if field == 'name':
            places = session.query(Place).all()
            for place in places:
                if what.lower() in place.name.lower():
                    pls.append(place)
        elif field == 'about':
            places = session.query(Place).all()
            what = ''.join(''.join(''.join(what.lower().split(' ')).split(',')).split('.'))
            for place in places:
                about = ''.join(''.join(''.join(place.about.lower().split(' ')).split(',')).split('.'))
                if what in about:
                    pls.append(place)
        elif field == 'address':
            places = session.query(Place).all()
            what = ''.join(''.join(what.lower().split(' ')).split(','))
            for place in places:
                adres = ''.join(''.join(place.address.lower().split(' ')).split(','))
                if what in adres:
                    pls.append(place)
        elif field == 'rating':
            places = session.query(Place).all()
            for place in places:
                if float(what) - 0.5 <= place.rating <= float(what) + 0.5:
                    pls.append(place)
    except Exception:
        return redirect('/search')
    return search(places=pls)


@app.route('/categories')
def categories():
    categs = {}
    ccc = CategoryListResource.get(CategoryListResource())
    for c in ccc:
        categs[c] = PlaceListResource_ForCateg.get(PlaceListResource_ForCateg(), c.id)
    return render_template("categories.html", title='Категории', categs=categs)


@app.route('/find_cat', methods=["POST"])
def find_cat():
    cat = request.form["stolb"]
    session = create_session()
    categ = session.query(Category).filter(Category.name == cat).first()
    return redirect(f"/one_category/{categ.id}")


@app.route('/map')
def map():
    places = PlaceListResource_All.get(PlaceListResource_All())
    for place in places:
        if place.coords in [None, '', ' ', '  ']:
            con = sqlite3.connect("db/blogs.sqlite")
            cur = con.cursor()
            cur.execute(f"UPDATE places SET coords='{get_coords_for_flace(place.address)}' WHERE id={place.id}")
            con.commit()
            con.close()
            return redirect('/map')

    sp = [pl.coords for pl in places]

    pt = '~'.join([i + ',comma' for i in sp])
    map_request = f"https://static-maps.yandex.ru/1.x/?ll=37.622504,55.753215&pt={pt}&l=map,skl&z=9"
    response = requests.get(map_request)
    if response:
        map_file = "static/img/map.jpg"
        with open(map_file, "wb") as file:
            file.write(response.content)

    link = f"https://yandex.ru/maps/?ll=37.622504,55.753215&pt={'~'.join(sp)}&l=map,z=12"
    return render_template("map.html", title='Карта', href=link)


@app.route('/rating')
def rating():
    session = create_session()
    places = session.query(Place).all()
    places.sort(key=lambda pl: -pl.rating)
    return render_template("rating.html", title='Рейтинг', places=places)


@app.route('/add_comm/<place_id>', methods=['GET', 'POST'])  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def add_comm(place_id):
    form = AddCommForm()
    if form.validate_on_submit():
        try:
            rating = float(form.rating.data)
            if not (0 <= rating <= 5):
                raise ValueError
        except Exception:
            return render_template('add_comm.html', title='Добавление комментария', form=form)
        session = db_session.create_session()
        comm = Comm(
            text=form.text.data,
            rating=rating,
            user_id=current_user.id,
            user_name=current_user.login,
            place_id=place_id
        )
        session.add(comm)
        session.commit()
        place = session.query(Place).get(place_id)
        try:
            c = place.comments_list.split(', ')
        except Exception:
            c = [str(place.comments_list)]
        while '' in c:
            c.remove('')
        while ' ' in c:
            c.remove(' ')
        c.append(str(comm.id))
        r = ((float(place.rating) * (len(c) - 1)) + float(comm.rating)) / len(c)
        c = ', '.join(c)
        pl = Place(
            id=place.id,
            address=place.address,
            about=place.about,
            rating=r,
            name=place.name,
            comments_list=c,
            site=place.site
        )
        session.delete(place)
        session.add(pl)
        session.commit()
        next_page = '/one_place/' + str(place_id)
        return redirect(next_page)
    return render_template('add_comm.html', title='Добавление комментария', form=form)


if __name__ == '__main__':
    main()
