from rest_framework import permissions
from .models import ChatRoom

class IsChatRoomMember(permissions.BasePermission):
    def has_permission(self, request, view):
        room_id = view.kwargs['chatroom_pk']
        user_id = request.user.id
        return ChatRoom.objects.filter(id=room_id, members=user_id).exists()

