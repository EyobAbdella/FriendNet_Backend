from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationUtility:
    @staticmethod
    def file_uploaded(file_info):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(file_info['room_id'],  {
            "type": "file_uploaded",
            "file": file_info
        })
