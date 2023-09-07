from rest_framework import serializers
from .models import ChatMessage, ChatRoom, Comment, FriendRequest, Friend, Post, Like, Save, UserProfile, Group, GroupMessages


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source="user")

    class Meta:
        model = UserProfile
        fields = ['user_id', 'username', 'gender', 'profile_image', 'bio', 'birthdate']


class UserSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user')
    class Meta:
        model = UserProfile
        fields = ['user_id', 'username', 'profile_image']

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)
        if request is not None and data['profile_image']:
            data['profile_image'] = request.build_absolute_uri(data['profile_image'])
        return data
    
class FriendRequestDecisionSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    is_accepted = serializers.BooleanField(read_only=True)
    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'is_accepted', 'created_at']


class FriendRequestSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(write_only=True)
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'receiver_id', 'is_accepted', 'created_at']
        read_only_fields = ['is_accepted']

    def validate_receiver_id(self, data):
        sender_id = self.context['sender_id']

        if Friend.objects.filter(user_id=sender_id, friends=data).exists():
            raise serializers.ValidationError("You're already friends with this user.")
        elif sender_id == data:
            raise serializers.ValidationError(
                "You cannot send friend request to yourself.")
        elif FriendRequest.objects.filter(sender_id=sender_id, receiver_id=data).exists():
            raise serializers.ValidationError('Friend request already sent.')
        elif FriendRequest.objects.filter(sender_id=data, receiver_id=sender_id).exists():
            raise serializers.ValidationError('User already send friend request to you')
        return data

    def create(self, validated_data):
        sender_id = self.context['sender_id']
        receiver_id = validated_data['receiver_id']
        return FriendRequest.objects.create(sender_id=sender_id, receiver_id=receiver_id)


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.user', read_only=True)
    profile_image = serializers.SerializerMethodField()

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.user.profile_image:
            return request.build_absolute_uri(obj.user.profile_image.url)
        return None

    class Meta:
        model = Comment
        fields = ['id', 'user_id', 'username', 'profile_image', 'text', 'created_at']

    def create(self, validated_data):
        post_id = self.context['post_id']
        user_id = self.context['user_id']
        return Comment.objects.create(post_id=post_id, user_id=user_id, **validated_data)


class LikePostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.user', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user_id', 'username', 'created_at']

    def create(self, validated_data):
        user_id = self.context['user_id']
        post_id = self.context['post_id']
        if Like.objects.filter(user_id=user_id, post_id=post_id).exists():
            raise serializers.ValidationError("You can't like one post twice.")
        return Like.objects.create(user_id=user_id, post_id=post_id)


class SavePostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.user', read_only=True)

    class Meta:
        model = Save
        fields = ['id', 'user_id', 'username','created_at']

    def create(self, validated_data):
        user_id = self.context['user_id']
        post_id = self.context['post_id']
        if Save.objects.filter(user_id=user_id, post_id=post_id).exists():
            raise serializers.ValidationError("You can't save one post twice.")
        return Save.objects.create(user_id=user_id, post_id=post_id)

       
class ListPostSerializer(serializers.ModelSerializer):
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    save_count = serializers.IntegerField(read_only=True)
    post_comments = CommentSerializer(read_only=True, many=True)
    username = serializers.CharField(source='user.user', read_only=True)
    profile_image = serializers.SerializerMethodField()
    media_file = serializers.SerializerMethodField()
    post_likes = LikePostSerializer(read_only=True, many=True)
    save_post = SavePostSerializer(read_only=True, many=True)

    def get_media_file(self, obj):
        request = self.context['request']
        if obj.media_file:
            return request.build_absolute_uri(obj.media_file.url)
        return None

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.user.profile_image:
            return request.build_absolute_uri(obj.user.profile_image.url)
        return None

    class Meta:
        model = Post
        fields = ['id', 'username', 'profile_image', 'text', 'media_file', 'created_at', 'like_count',
                   'comment_count', 'save_count', 'post_likes', 'post_comments', 'save_post']


class UpdatePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'text', 'media_file']


class PostSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Post
        fields = ['user_id', 'text', 'media_file', 'created_at']

    def create(self, validated_data):
        user_id = self.context['user_id']
        return Post.objects.create(user_id=user_id, **validated_data)
     

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.user_id', read_only=True)
    username = serializers.StringRelatedField(source='sender.user', read_only=True)
    profile_image = serializers.StringRelatedField(source='sender.profile_image', read_only=True)
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)
        if request is not None and data['profile_image']:
            data['profile_image'] = request.build_absolute_uri(data['profile_image'])
        return data

    class Meta:
        model = ChatMessage
        fields = ['id', 'room_id', 'text', 'file', 'file_name', 'file_size', 'sender_id', 'username', 'profile_image', 'created_at']

    def create(self, validated_data):
        room_id = self.context['room_id']
        sender_id = self.context['user_id']
        file = validated_data['file']
        text = validated_data['text'] if 'text' in validated_data else None
        return ChatMessage.objects.create(room_id=room_id, sender_id=sender_id, text=text, file=file)


class ChatRoomSerializer(serializers.ModelSerializer):
    friend = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()

    def get_friend(self, obj):
            request = self.context.get('request')
            user_id = request.user.id
            friend = next((member for member in obj.members.all() if member.user_id != user_id), None)
            return UserSerializer(friend).data

    def get_message(self, obj):
        first_message = obj.message.first()
        if first_message:
            return ChatMessageSerializer(first_message).data
        else:
            return None

    def to_representation(self, instance):
        request = self.context.get('request')
        data = super().to_representation(instance)
        if request is not None and data['friend']['profile_image']:
            data['friend']['profile_image'] = request.build_absolute_uri(data['friend']['profile_image'])
        return data

    class Meta:
        model = ChatRoom
        fields = ['id', 'friend', 'message']


class GroupSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    class Meta:
        model = Group
        fields = ['id', 'name', 'creator', 'members', 'description', 'image', 'created_at']

    def create(self, validated_data):
        creator_id = self.context['user_id']
        group = Group.objects.create(creator_id=creator_id, **validated_data)
        group.members.set([creator_id])
        return group


class AddMembersSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def save(self, **kwargs):
        user_id = self.validated_data['user_id']
        group_id = self.context['group_id']
        return Group.objects.get(id=group_id).members.add(user_id)
    
    def validate_user_id(self, value):
        if Group.objects.filter(id=self.context['group_id'], members=value).exists():
            raise serializers.ValidationError("User already group member.")
        return value

    
class GroupMessagesSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='sender.user', read_only=True)
    profile_image = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    def get_profile_image(self, obj):
        if obj.sender.profile_image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.sender.profile_image.url)
        return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None

    class Meta:
        model = GroupMessages
        fields = ['id', 'room_id', 'sender_id', 'username', 'profile_image', 'text', 'file', 'file_name', 'file_size', 'created_at']

    def create(self, validated_data):
        user_id = self.context['user_id']
        room_id = self.context['room_id']
        return GroupMessages.objects.create(room_id=room_id, sender_id=user_id, **validated_data)
