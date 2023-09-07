import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Group, UserProfile
from .serializers import ChatMessageSerializer, GroupMessagesSerializer


class BaseChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope.get('user').id
        self.rooms = await self.get_rooms()
        for room in self.rooms:
            await self.channel_layer.group_add(
                str(room.id),
                self.channel_name
            )
        await self.accept()

    async def get_rooms(self):
        raise NotImplementedError
    
    def get_serializer(self, *args, **kwargs):
        raise NotImplementedError

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data['text']
        room_id = data['room_id']
        serializer = self.get_serializer(data={'text': text, 'file': None}, context={'user_id': self.user_id, 'room_id': room_id})
        serializer.is_valid(raise_exception=True)
        message = await self.save_data(serializer)
        await self.channel_layer.group_send(
            str(room_id),
            {
                "type": "chat.message",
                "message": message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            "id": message["id"],
            "room_id":message['room_id'],
            "text": message['text'],
            "sender_id": message['sender_id'],
            "username": message['username'],
            "profile_image": message["profile_image"],
            "created_at": message['created_at']
        }))

    async def file_uploaded(self, event):
        file = event['file']
        await self.send(text_data=json.dumps({
            "id": file["id"],
            "room_id": file['room_id'],
            "file_name": file['file_name'],
            "file_size": file['file_size'],
            "file": file["file"],
            "sender_id": file['sender_id'],
            "username": file['username'],
            "profile_image": file["profile_image"],
            "created_at": file['created_at']
        }))

    @database_sync_to_async
    def save_data(self, serializer):
        serializer.save()
        user_data = UserProfile.objects.get(user_id=self.user_id)
        BASE_URL = 'http://127.0.0.1:8000'
        image = f"{BASE_URL}{user_data.profile_image.url}" if user_data.profile_image else None

        return {
            "id": serializer.data['id'],
            "room_id": serializer.data['room_id'],
            "text": serializer.data['text'],
            "sender_id": self.user_id,
            "username": user_data.user.username,
            "profile_image": image,
            "created_at": serializer.data['created_at'],
        }

class ChatConsumer(BaseChatConsumer):
    async def get_rooms(self):
        return await database_sync_to_async(list)(ChatRoom.objects.filter(members=self.user_id))

    def get_serializer(self, *args, **kwargs):
        return ChatMessageSerializer(*args, **kwargs)

class GroupChatConsumer(BaseChatConsumer):
    async def get_rooms(self):
        return await database_sync_to_async(list)(Group.objects.filter(members=self.user_id))

    def get_serializer(self, *args, **kwargs):
        return GroupMessagesSerializer(*args, **kwargs)


