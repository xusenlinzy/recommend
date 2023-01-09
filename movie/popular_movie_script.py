import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommend.settings")
django.setup()

import re
from movie.models import Movie, Tags

Movie.objects.all().delete()
Tags.objects.all().delete()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
movie_path = os.path.join(BASE_DIR, "data/movie.csv")
with open(movie_path, 'r', encoding='utf-8') as f:
    for line in f.readlines()[1:]:
        _id, name, image_link, country, years, director_description, leader, star, description, tags, flag = tuple(
            line.strip().split(','))
        res = re.match('\d*', star)
        int_d_rate_num = int(res[0]) if res else 0
        movie = Movie.objects.create(
            name=name, pic=name + '.png',
            country=country,
            years=years,
            leader=leader,
            d_rate_nums=int_d_rate_num,
            d_rate=star,
            intro=description,
            director=director_description,
            good='None')

        tags = [tag.strip() for tag in tags.split('/')]
        for tag in tags:
            tag_obj, created = Tags.objects.get_or_create(name=tag)
            movie.tags.add(tag_obj.id)
