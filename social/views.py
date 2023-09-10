import os
from itertools import chain
from django.db.models import Q
from django.db.models import Prefetch
from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from .utils import NotificationUtility
from .filters import GroupFilter, PostFilter
from .permissions import IsChatRoomMember
from .models import (
    ChatMessage,
    ChatRoom,
    Comment,
    Friend,
    Group,
    GroupMessages,
    Post,
    Like,
    Save,
    UserProfile,
    FriendRequest,
)
from .serializers import (
    AddMembersSerializer,
    ChatMessageSerializer,
    ChatRoomSerializer,
    CommentSerializer,
    GroupMessagesSerializer,
    GroupSerializer,
    FriendRequestSerializer,
    LikePostSerializer,
    ListPostSerializer,
    PostSerializer,
    FriendRequestDecisionSerializer,
    SavePostSerializer,
    UpdatePostSerializer,
    UserProfileSerializer,
    UserSerializer,
)


class PeopleViewSet(ModelViewSet):
    http_method_names = ["get", "put", "delete", "head", "options"]
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["user__username"]

    def get_queryset(self):
        user_id = self.request.user.id
        friend_id = FriendRequest.objects.filter(
            Q(sender_id=user_id) | Q(receiver_id=user_id)
        ).values_list("receiver_id", "sender_id")
        friend_id = list(chain(*friend_id))
        queryset = UserProfile.objects.all().select_related("user")
        return queryset.exclude(Q(user_id__in=friend_id) | Q(user_id=user_id))

    def get_permissions(self):
        if self.action != "me":
            return [DjangoModelPermissionsOrAnonReadOnly()]
        return super().get_permissions()

    def get_serializer_context(self):
        return {"request": self.request}

    @action(detail=False, methods=["GET", "PUT", "DELETE"])
    def me(self, request):
        user = UserProfile.objects.select_related("user").get(user_id=request.user.id)
        if request.method == "GET":
            serializer = UserProfileSerializer(user, context={"request": request})
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = UserProfileSerializer(
                user, data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class UserFriendViewSet(ModelViewSet):
    http_method_names = ["get", "delete"]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id is not None:
            friends_ids = (
                Friend.objects.select_related("user")
                .filter(user_id=user_id)
                .values_list("friends", flat=True)
            )
            return UserProfile.objects.filter(user_id__in=friends_ids).select_related(
                "user"
            )
        return self.request.user.profile.friend.friends.all().select_related("user")

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "request": self.request}

    def destroy(self, request, *args, **kwargs):
        my_friend = self.get_object()
        user_profile = request.user.profile
        my_friend.friend.friends.remove(user_profile)
        user_profile.friend.friends.remove(my_friend)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FriendRequestViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete"]

    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        return FriendRequest.objects.filter(
            Q(sender_id=user_id, is_accepted=False)
            | Q(receiver_id=user_id, is_accepted=False)
        )

    def get_serializer_context(self):
        return {"sender_id": self.request.user.id, "request": self.request}


class FriendRequestDecisionViewSet(ModelViewSet):
    http_method_names = ["get", "put", "delete"]

    serializer_class = FriendRequestDecisionSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(
            receiver_id=self.request.user.id, is_accepted=False
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        receiver = instance.receiver
        sender = instance.sender

        receiver.friend.friends.add(sender)
        sender.friend.friends.add(receiver)
        instance.is_accepted = True
        instance.save()

        # Create a chat room for the two friends
        chat_room = ChatRoom.objects.create()
        chat_room.members.set([receiver, sender])

        return Response(
            {"detail": "Friend request accepted successfully."},
            status=status.HTTP_200_OK,
        )


class ListPostViewSet(ModelViewSet):
    queryset = Post.objects.with_counts()
    serializer_class = ListPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = PostFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostSerializer
        elif self.request.method == "PUT":
            return UpdatePostSerializer
        return ListPostSerializer

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "request": self.request}

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if request.user.id != post.user_id:
            return Response(
                {"detail": "you don't have permission to update this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if request.user.id != post.user_id:
            return Response(
                {"detail": "you don't have permission to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
        file_path = post.media_file.path
        if os.path.exists(file_path):
            os.remove(file_path)
        Post.objects.filter(id=post.id).delete()
        return Response(
            {"detail": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT
        )


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs["post_pk"]).select_related(
            "user__user"
        )

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "post_id": self.kwargs["post_pk"]}

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if request.user.id != comment.user_id:
            return Response(
                {"detail": "you don't have permission to update this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if request.user.id != comment.user_id:
            return Response(
                {"detail": "you don't have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class LikePostViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    serializer_class = LikePostSerializer
    lookup_field = "user_id"

    def get_queryset(self):
        return Like.objects.filter(post_id=self.kwargs["post_pk"]).select_related(
            "user__user"
        )

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "post_id": self.kwargs["post_pk"]}

    def destroy(self, request, *args, **kwargs):
        like = self.get_object()
        if request.user.id != like.user_id:
            return Response(
                {"detail": "you don't have permission to delete this like."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class SavePostViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete"]
    serializer_class = SavePostSerializer
    lookup_field = "user_id"

    def get_queryset(self):
        return Save.objects.filter(post_id=self.kwargs["post_pk"]).select_related(
            "user__user"
        )

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "post_id": self.kwargs["post_pk"]}

    def destroy(self, request, *args, **kwargs):
        save = self.get_object()
        if request.user.id != save.user_id:
            return Response(
                {"detail": "you don't have permission to delete this save."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class ListSavedPostViewSet(ModelViewSet):
    http_method_names = ["get", "delete"]
    serializer_class = ListPostSerializer

    def get_queryset(self):
        return Post.objects.filter(save_post__user_id=self.request.user.id)


class ChatRoomViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        user_profile_qs = UserProfile.objects.select_related("user")
        return ChatRoom.objects.filter(members=self.request.user.id).prefetch_related(
            Prefetch("members", queryset=user_profile_qs),
            Prefetch(
                "message", queryset=ChatMessage.objects.select_related("sender__user")
            ),
        )

    def get_serializer_context(self):
        return {"request": self.request}


class ChatMessagesViewSet(ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsChatRoomMember]

    def get_queryset(self):
        room_id = self.kwargs["chatroom_pk"]
        return ChatMessage.objects.filter(room_id=room_id).select_related(
            "sender__user"
        )

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "request": self.request}

    def create(self, request, *args, **kwargs):
        room_id = self.kwargs["chatroom_pk"]
        user_id = request.user.id
        serializer = ChatMessageSerializer(
            data=request.data,
            context={"user_id": user_id, "request": request, "room_id": room_id},
        )
        serializer.is_valid(raise_exception=True)
        file_info = serializer.save()

        file_info = {
            "id": serializer.data["id"],
            "room_id": serializer.data["room_id"],
            "sender_id": serializer.data["sender_id"],
            "username": serializer.data["username"],
            "file_name": serializer.data["file_name"],
            "file_size": serializer.data["file_size"],
            "file": serializer.data["file"],
            "profile_image": serializer.data["profile_image"],
            "created_at": serializer.data["created_at"],
        }
        NotificationUtility.file_uploaded(file_info)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    queryset = (
        Group.objects.all()
        .prefetch_related("members__user")
        .select_related("creator__user")
    )
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = GroupFilter
    search_fields = ["name", "description"]

    def get_queryset(self):
        user_id = self.request.query_params.get("not_joined")
        queryset = super().get_queryset()
        if user_id:
            queryset = queryset.exclude(members__user_id=user_id)
        return queryset

    def get_serializer_context(self):
        return {"user_id": self.request.user.id, "request": self.request}

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator_id != request.user.id:
            return Response(
                {"detail": "You don't have permission to delete the group."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator_id != request.user.id:
            return Response(
                {"detail": "You don't have permission to update the group."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().update(request, *args, **kwargs)


class GroupMemberViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        group_id = self.kwargs["group_pk"]
        user_profile_qs = UserProfile.objects.select_related("user")
        return (
            Group.objects.prefetch_related(
                Prefetch("members", queryset=user_profile_qs)
            )
            .get(id=group_id)
            .members.all()
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddMembersSerializer
        return UserSerializer

    def get_serializer_context(self):
        return {"group_id": self.kwargs["group_pk"], "request": self.request}

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.user.id
        group = Group.objects.get(id=kwargs["group_pk"])

        if instance.user_id == user_id:
            if group.creator_id == instance.user_id:
                group.delete()
                return Response(
                    {"detail": "Group Successfully deleted"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            group.members.remove(user_id)
            return Response(
                {"detail": f"{instance.user} Successfully removed from group."},
                status=status.HTTP_204_NO_CONTENT,
            )

        elif group.creator_id != user_id:
            return Response(
                {"detail": "You don't have permission to perform this action."}
            )

        group.members.remove(instance.user_id)
        return Response(
            {"detail": f"{instance.user} Successfully removed from group."},
            status=status.HTTP_204_NO_CONTENT,
        )


class GroupMessageViewSet(ModelViewSet):
    serializer_class = GroupMessagesSerializer

    def get_queryset(self):
        return GroupMessages.objects.filter(
            room_id=self.kwargs["group_pk"]
        ).select_related("room", "sender__user")

    def get_serializer_context(self):
        return {"request": self.request}

    def create(self, request, *args, **kwargs):
        room_id = kwargs["group_pk"]
        user_id = request.user.id
        file_size = request.FILES.get("file").size

        serializer = GroupMessagesSerializer(
            data=request.data,
            context={
                "user_id": user_id,
                "room_id": room_id,
                "request": self.request,
                "file_size": file_size,
            },
        )
        serializer.is_valid(raise_exception=True)
        file_info = serializer.save()

        file_info = {
            "id": serializer.data["id"],
            "room_id": serializer.data["room_id"],
            "sender_id": serializer.data["sender_id"],
            "username": serializer.data["username"],
            "file_name": serializer.data["file_name"],
            "file_size": file_size,
            "file": serializer.data["file"],
            "profile_image": serializer.data["profile_image"],
            "created_at": serializer.data["created_at"],
        }
        NotificationUtility.file_uploaded(file_info)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
