from rest_framework import serializers
from movie.models import Movie


class MovieSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField(method_name='get_tags')

    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]

    class Meta:
        model = Movie
        fields = "__all__"
