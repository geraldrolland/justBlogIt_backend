import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class BroadCastConsumer(WebsocketConsumer):
    def connect(self):
        self.post_room = "broadcastPost"
        self.notification_room = "broadcastNotification"
        self.comment_room = "broadcastPostComment"

        #Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.post_room, self.channel_name
        )

        async_to_sync(self.channel_layer.group_add)(
            self.notification_room, self.channel_name
        )
        async_to_sync(self.channel_layer.group_add)(
            self.comment_room, self.channel_name
        )
        print("connected")

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
    
        async_to_sync(self.channel_layer.group_discard)(
            self.post_room, self.channel_name
        )
        async_to_sync(self.channel_layer.group_discard)(
            self.notification_room, self.channel_name
        )
        


    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print(message)

    # Receive message from room group
    def handle_post(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
    
    def handle_notification(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"message": message}))
    
    def handle_postcomment(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"message": message}))