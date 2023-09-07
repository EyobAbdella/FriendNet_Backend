from django_filters import rest_framework as filters
from .models import Group, Post

class PostFilter(filters.FilterSet):
    user_id = filters.NumberFilter(field_name='user_id')
    save_post = filters.NumberFilter(field_name='save_post__user_id')

    class Meta:
        model = Post
        fields = {
            'user_id': ['exact'],
            'save_post': ['exact'],
        }

class GroupFilter(filters.FilterSet):
    creator_id = filters.NumberFilter(field_name='creator_id')
    members = filters.NumberFilter(field_name='members')
    class Meta:
        model = Group
        fields = {
            'creator_id': ['exact'],
            'members': ['exact']
        }

