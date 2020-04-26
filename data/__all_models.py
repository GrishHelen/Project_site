from .users import User, UsersResource
from .places import Place, PlaceResource, PlaceListResource
from .db_session import create_session, global_init

global_init("db/blogs.sqlite")


'''
user = User()
user.name = "Пользователь 1"
user.about = "биография пользователя 1"
user.email = "email@email.ru"
session = create_session()
session.add(user)
session.commit()

news = News(title="Первая новость", content="Привет блог!",
            user_id=1, is_private=False)
session.add(news)
session.commit()

user = session.query(User).filter(User.id == 1).first()
news = News(title="Вторая новость", content="Уже вторая запись!",
            user=user, is_private=False)
session.add(news)
session.commit()

for news in user.news:
    print(news)
'''
