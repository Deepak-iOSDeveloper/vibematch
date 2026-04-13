import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.connection_id = self.scope['url_route']['kwargs']['connection_id']
        self.room_group_name = f'chat_{self.connection_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Verify user belongs to this connection
        if not await self.user_in_connection():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content or len(content) > 1000:
                return
            message = await self.save_message(content)
            if message:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': message['id'],
                        'content': message['content'],
                        'sender_id': message['sender_id'],
                        'sender_name': message['sender_name'],
                        'sender_initials': message['sender_initials'],
                        'sender_color': message['sender_color'],
                        'created_at': message['created_at'],
                        'message_type': 'text',
                    }
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def user_in_connection(self):
        from .models import Connection
        try:
            conn = Connection.objects.get(id=self.connection_id)
            return conn.user_a == self.user or conn.user_b == self.user
        except Connection.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        from .models import Connection, Message, Notification
        try:
            conn = Connection.objects.get(id=self.connection_id, status__in=['chatting','vibe_check','matched','friends'])
            msg = Message.objects.create(
                connection=conn, sender=self.user, content=content
            )
            # Update connection cache
            conn.last_message_at = timezone.now()
            conn.last_message_preview = content[:60]
            conn.message_count += 1
            conn.save()

            # Notify other user
            other = conn.get_other_user(self.user)
            Notification.objects.create(
                user=other, notif_type='new_message',
                title=f'New message from {self.user.full_name}',
                body=content[:60], connection=conn
            )

            return {
                'id': msg.id,
                'content': msg.content,
                'sender_id': self.user.id,
                'sender_name': self.user.full_name,
                'sender_initials': self.user.avatar_initials or self.user.full_name[0],
                'sender_color': self.user.avatar_color,
                'created_at': msg.created_at.isoformat(),
            }
        except Connection.DoesNotExist:
            return None
