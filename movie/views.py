from django.db.models import Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from movie.models import Movie
from movie.serializers import MovieSerializer
from movie.algorithm import recommend_by_user_cf, recommend_by_item_cf


class SearchMovie(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def list(self, request, *args, **kwargs):
        query = request.query_params.get("query")
        if query:
            self.queryset = self.queryset.filter(
                Q(name__icontains=query) | Q(intro__icontains=query) | Q(director__icontains=query)
            )

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecommedMovie(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def list(self, request, *args, **kwargs):
        user_id = int(request.query_params.get("user_id"))
        method = request.query_params.get("method", "user_cf")

        if method == "user_cf":
            self.queryset = recommend_by_user_cf(user_id)
        else:
            self.queryset = recommend_by_item_cf(user_id)

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
