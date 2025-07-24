from channels.generic.websocket import AsyncJsonWebsocketConsumer

from core.consts import LIVE_UPDATES_PREFIX


class LiveUpdatesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.client_id = self.scope['url_route']['kwargs']['client_id']
        self.group_name = f"{LIVE_UPDATES_PREFIX}_{self.client_id}"

        if not self.client_id:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        pass

    async def send_message(self, event):
        await self.send_json({
            "type": "message",
            "data": event["message"],
        })

    async def send_kb_updates(self, event):
        await self.send_json({
            "type": "kb_updates",
            "data": event["data"],
        })