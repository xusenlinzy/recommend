import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommend.settings")
django.setup()

import random
from movie.models import Movie, User, Rate

strs = 'abcdefghijk_mnopqrstuvwxyz'


# 随机生成username
def random_user_name(length=5):
    return ''.join(random.choices(strs, k=length))


def random_phone():
    res = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    return res


def random_movie_id(num=5):
    movie_nums = Movie.objects.all().order_by('?').values('id')[:num]
    print(movie_nums)
    return [movie['id'] for movie in movie_nums]


def random_mark():
    return random.randint(1, 10)


def popular_user_rating(user_numbers):
    for i in range(user_numbers):
        user_name = random_user_name()
        print(user_name)
        try:
            user, created = User.objects.get_or_create(
                username=user_name,
                name=user_name,
                defaults={'password': user_name, "phone": random_phone(),
                          "address": random_user_name(),
                          "email": random_user_name() + '@163.com'}
            )
            for movie_id in random_movie_id():
                Rate.objects.get_or_create(user=user, movie_id=movie_id, defaults={"mark": random_mark()})
        except Exception as e:
            raise e


if __name__ == '__main__':
    popular_user_rating(100)  # 随机生成用户打分 参数为生成数量
