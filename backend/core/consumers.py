from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        from core.models.chatroom import ChatRoom

        self.chatroom_uuid = self.scope['url_route']['kwargs']['chatroom_uuid']
        self.group_name = f"chatroom_{self.chatroom_uuid}"

        try:
            self.chatroom = await self.get_chatroom(self.chatroom_uuid)
        except ChatRoom.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        pass

    async def send_message(self, event):
        await self.send_json(event["message"])

    @staticmethod
    async def get_chatroom(uuid):
        from core.models.chatroom import ChatRoom
        return await ChatRoom.objects.aget(uuid=uuid)
