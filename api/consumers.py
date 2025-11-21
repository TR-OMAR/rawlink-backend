import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Message, User

class ChatConsumer(WebsocketConsumer):
    
    def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            print("🔴 WebSocket Rejected: User not authenticated")
            self.close()
            return

        self.room_group_name = f"chat_{self.user.id}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        print(f"🟢 WebSocket Accepted: {self.user.username}")

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
        print(f"⚪ WebSocket Disconnected: {close_code}")

    def receive(self, text_data):
        print(f"📩 WS Received: {text_data}")
        try:
            data = json.loads(text_data)
            message_content = data.get('message')
            receiver_id = data.get('receiver_id')

            if not message_content or not receiver_id:
                return

            receiver = User.objects.get(id=receiver_id)
            
            # 1. Save to DB (CRITICAL for persistence)
            message = Message.objects.create(
                sender=self.user,
                receiver=receiver,
                content=message_content
            )
            print(f"💾 Message Saved ID: {message.id}")
            
            # 2. Send to Receiver & Sender
            message_data = {
                'id': message.id,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'receiver_id': receiver.id,
                'receiver_username': receiver.username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat()
            }

            async_to_sync(self.channel_layer.group_send)(
                f"chat_{receiver_id}", {'type': 'chat_message', 'message': message_data}
            )
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.user.id}", {'type': 'chat_message', 'message': message_data}
            )

        except Exception as e:
            print(f"❌ WS Receive Error: {e}")

    def chat_message(self, event):
        self.send(text_data=json.dumps(event['message']))