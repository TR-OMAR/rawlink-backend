import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Message, User


class ChatConsumer(WebsocketConsumer):
    """
    WebSocket consumer used for real-time private messaging.

    Each user is placed in their own group (chat_<user_id>) so messages can be
    delivered instantly to both sender and receiver. The consumer uses a
    synchronous interface, so async channel operations are wrapped with
    async_to_sync.
    """

    def connect(self):
        """
        Called when a client opens a WebSocket connection.

        - Reject connection if the user is not authenticated.
        - Create a room group based on the user's ID.
        - Add the user to that group so they can receive real-time messages.
        """
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            print("WebSocket rejected: user not authenticated")
            self.close()
            return

        self.room_group_name = f"chat_{self.user.id}"

        # Add this connection to the user's private group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        print(f"WebSocket connected: {self.user.username}")

    def disconnect(self, close_code):
        """
        Remove the WebSocket from its group when the client disconnects.
        """
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

        print(f"WebSocket disconnected: code={close_code}")

    def receive(self, text_data):
        """
        Called whenever the WebSocket receives data from the client.

        Expected payload:
            {
                "message": "...",
                "receiver_id": <int>
            }

        Steps:
        1. Validate the data.
        2. Save the message to the database.
        3. Broadcast the message to both sender and receiver groups.
        """
        try:
            data = json.loads(text_data)
            message_text = data.get("message")
            receiver_id = data.get("receiver_id")

            # Ignore empty or malformed messages
            if not message_text or not receiver_id:
                return

            receiver = User.objects.get(id=receiver_id)

            # Save to database so messages persist
            message = Message.objects.create(
                sender=self.user,
                receiver=receiver,
                content=message_text
            )

            # Prepare message payload for frontend clients
            message_data = {
                "id": message.id,
                "sender_id": self.user.id,
                "sender_username": self.user.username,
                "receiver_id": receiver.id,
                "receiver_username": receiver.username,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            }

            # Broadcast to receiver and sender groups
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{receiver.id}",
                {"type": "chat_message", "message": message_data}
            )

            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.user.id}",
                {"type": "chat_message", "message": message_data}
            )

        except Exception as e:
            # Avoid crashing the consumer — log errors instead
            print(f"WebSocket receive error: {e}")

    def chat_message(self, event):
        """
        Handler for messages sent to the group.

        Sends the message directly to the WebSocket client.
        """
        self.send(text_data=json.dumps(event["message"]))
