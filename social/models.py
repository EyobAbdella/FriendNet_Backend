from django.db import models
from django.db.models import Prefetch
from django.conf import settings
from django.core.validators import FileExtensionValidator
from .validators import validate_file_size, validate_image_size


class UserProfile(models.Model):
    MALE = "M"
    FEMALE = "F"

    USER_GENDER = [(MALE, "Male"), (FEMALE, "Female")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        editable=False,
        related_name="profile",
    )
    gender = models.CharField(max_length=1, choices=USER_GENDER, null=True)
    profile_image = models.ImageField(
        upload_to="image/user_profile", null=True, validators=[validate_image_size]
    )
    birthdate = models.DateField(null=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class Friend(models.Model):
    user = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="friend"
    )
    friends = models.ManyToManyField(UserProfile, related_name="friends")


class FriendRequest(models.Model):
    sender = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="friend_request_send"
    )
    receiver = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="friend_request_receive"
    )
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["sender", "receiver"]]


class PostQuerySet(models.QuerySet):
    def with_counts(self):
        return (
            self.annotate(
                like_count=models.Count("post_likes", distinct=True),
                comment_count=models.Count("post_comments", distinct=True),
                save_count=models.Count("save_post", distinct=True),
            )
            .prefetch_related(
                Prefetch(
                    "post_likes", queryset=Like.objects.select_related("user__user")
                ),
                Prefetch(
                    "post_comments",
                    queryset=Comment.objects.select_related("user__user"),
                ),
                Prefetch(
                    "save_post", queryset=Save.objects.select_related("user__user")
                ),
            )
            .select_related("user__user")
        )


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def with_counts(self):
        return self.get_queryset().with_counts()


class Post(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="my_post"
    )
    text = models.TextField(blank=True, null=True)
    media_file = models.FileField(
        upload_to="file/post_files",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "gif", "mp4", "mov", "avi"]),
            validate_file_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = PostManager()

    class Meta:
        ordering = ["-created_at"]


class Like(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "post"]]


class Comment(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="post_comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Save(models.Model):
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="saved_posts"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="save_post")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "post"]]


class ChatRoom(models.Model):
    members = models.ManyToManyField(UserProfile)


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="message")
    sender = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="sent_message"
    )
    text = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to="file/chat_files",
        blank=True,
        null=True,
        validators=[validate_file_size],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Group(models.Model):
    members = models.ManyToManyField(UserProfile)
    creator = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="created_group"
    )
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="image/group_profile", null=True, validators=[validate_image_size]
    )
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GroupMessages(models.Model):
    room = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="message")
    sender = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="group_message_sent"
    )
    text = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to="file/group_file",
        blank=True,
        null=True,
        validators=[validate_file_size],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
