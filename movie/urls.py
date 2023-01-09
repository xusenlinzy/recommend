from django.urls import path

from movie.views import (
    SearchMovie,
    RecommedMovie,
)

urlpatterns = [
    path(route="search/", view=SearchMovie.as_view(), name='SearchMovie'),
    path(route="recommend/", view=RecommedMovie.as_view(), name='RecommedMovie'),
]
