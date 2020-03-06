from django.db import connection
from asgiref.sync import async_to_sync 
from channels.generic.websocket import WebsocketConsumer 

from OrderTangoApp.models import User
from .models import Thread, ThreadMessage, ThreadMember
import json 


class ChatConsumer(WebsocketConsumer):

    def fetch_messages(self, text_data):
        connection.schema_name = 'otfe5e60d1'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('fetch_message 1: ', currentSchema)
        sender_user = text_data['from']
        thread = Thread.objects.get(id=self.thread_id).id
      
        messages = ThreadMessage.objects.filter(sender=sender_user, thread=thread)
        content = {
            'command': 'fetch_message',
            'message': self.messages_to_json(messages)
        }

        print('HERE', messages)

        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('fetch_message 2: ', currentSchema)
        self.send_chat_message(content)


    def new_message(self, text_data):
        connection.schema_name = 'otfe5e60d1'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('new_message 1: ', currentSchema)

        sender = text_data['from']
        sender_user = User.objects.filter(userId=sender)[0]
        thread = Thread.objects.get(id=self.thread_id)
        ThreadMember.objects.get_or_create(member=sender_user, thread=thread)
        message = ThreadMessage.objects.create(
            thread=thread,
            sender=sender_user, 
            message=text_data['message'])
        
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message)
        }

        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('new_message 2: ', currentSchema)
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
            'thread': message.thread.name,
            'sender': message.sender.email,
            'message': message.message,
            'date_created': str(message.date_created)
        }

    commands = {
        'fetch_message': fetch_messages,
        'new_message': new_message
    }

    def connect(self):
        connection.schema_name = 'otfe5e60d1'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('connect 1: ', currentSchema)

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name 

        thread_name = Thread.objects.get_or_create(name=self.room_name)
        self.thread_id = thread_name[0].id

        # Join room group 
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name 
        )

        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)

        print('connect 2: ', currentSchema)
        self.accept() 

    def disconnect(self, close_code):
        # Leave room group 
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, 
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data = json.loads(text_data)
        self.commands[text_data['command']](self, text_data)

    def send_chat_message(self, message):
        # message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))

        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        