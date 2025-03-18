import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async  # Verifica que esta línea esté correcta
from .models import ChatMessage


User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Attempting to connect...")
        self.room_group_name = "single_room"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Connection accepted, added to group: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        print(f"Raw text data received: {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        sender_username = text_data_json.get("username", "Anonymous")
        recipient_username = text_data_json.get("recipient", None)  # Si existe, es un mensaje privado

        # Add logging for debugging
        print(f"Parsed message data: message={message} from sender={sender_username}")

        try:
            sender = await database_sync_to_async(User.objects.get)(username=sender_username)
            print(f"Found sender user: {sender}")
            
            if recipient_username:
                recipient = await database_sync_to_async(User.objects.get)(username=recipient_username)
                print(f"Found recipient user: {recipient}")
                await self.send_private_message(sender, recipient, message)
            else:
                await self.save_message(sender, message)  # Guarda mensaje público
                print("Message saved, attempting to send to group")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "username": sender.username,
                        "private": False
                    }
                )
                print("Group send completed")
        except Exception as e:
            print(f"Error in receive method {str(e)}")
            raise

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                    "private": False
                }
            )
        )

    async def send_private_message(self, sender, recipient, message):
        private_channel = f"private_{sender.id}_{recipient.id}"

        await self.save_message(sender, message, recipient)  # Guarda el mensaje en la BD
        await self.channel_layer.group_send(
            private_channel,
            {
                "type": "private_message",
                "message": message,
                "username": sender.username,
                "private": True
            }
        )

    async def private_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "username": event["username"],
            "private": True
        }))

    @database_sync_to_async
    def save_message(self, sender, message, recipient=None):
        ChatMessage.objects.create(
            sender=sender,
            recipient=recipient,
            message=message,  # Corregido a 'content'
            channel="general" if recipient is None else f"private_{sender.id}_{recipient.id}"
        )

    def recover_messages(self, sender):
        ChatMessage.objects.all()