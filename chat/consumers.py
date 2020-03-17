import re
import json 
import functools

from django.db import connection
from django.http import HttpResponse

from asgiref.sync import async_to_sync 
from channels.generic.websocket import WebsocketConsumer 
from channels.exceptions import StopConsumer

from OrderTangoApp.models import User
from OrderTangoSubDomainApp.models import Subuser
from .models import Thread, ThreadMessage, ThreadMember


class ChatConsumer(WebsocketConsumer):

    def new_member(self, text_data):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print('new_member: ', connection.schema_name)
        member_user = text_data['members']
        
        members = []

        for member in member_user:
            print('MKE', member)
            try:
                user = User.objects.get(userId=member['id'], email=member['email'])
                thread = Thread.objects.get(id=self.thread_id)
                member = ThreadMember.objects.get_or_create(user_member=user, thread=thread)
                print('New Member', member)
                members.append({
                    'member_id': member.user_member.userId,
                    'member_email': member.user_member.email,
                    'thread': member.thread,
                })
            except:
                try:
                    subuser = Subuser.objects.get(subUserId=member['id'], email=member['email'])
                    thread = Thread.objects.get(id=self.thread_id)
                    m = ThreadMember.objects.get_or_create(subuser_member=subuser, thread=thread)

                    members.append({
                        'member_id': m.subuser_member.subUserId,
                        'member_email': m.subuser_member.email,
                        'thread': thread.name,
                    })
                except:
                    return HttpResponse("No members.")

        print('MMM', members)
        content = {
            'command': 'new_member',
            'members': self.new_members_to_json(members)
        }

        self.send_chat_message(content)     

    def delete_thread(self, text_data):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print('delete_message: ', connection.schema_name)

        sender = text_data['from']
        print(sender)

        try: 
            user = User.objects.get(userId=sender['id'], email=sender['email'])
            thread = Thread.objects.get(id=text_data['thread'])
            thread.delete() 
            threads = Thread.objects.filter(is_archived=False, threadmember__user_member=user)

            content = {
                'command': 'delete_thread',
                'threads': self.threads_to_json(threads)
            }

            self.send_chat_message(content)

        except:
            try:
                subuser = Subuser.objects.get(subUserId=sender['id'], email=sender['email'])
                thread = Thread.objects.get(id=text_data['thread'])
                thread.delete() 
                threads = Thread.objects.filter(is_archived=False, threadmember__subuser_member=subuser)
                
                content = {
                    'command': 'delete_thread',
                    'threads': self.threads_to_json(threads)
                }

                self.send_chat_message(content)
            except:
                return HttpResponse("No threads found.")

    def delete_message(self, text_data):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        print('delete_message: ', connection.schema_name)
        print(text_data['thread'], text_data['message_id'])

        thread = Thread.objects.get(name=text_data['thread']).id
        message = ThreadMessage.objects.get(id=text_data['message_id'], thread=thread)
        message.delete()

        content = {
            'command': 'delete_message'
        }

        self.send_chat_message(content)
        

    def fetch_messages(self, text_data):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name
        connection.set_schema(schema_name=currentSchema)

        sender = text_data['from']

        try: 
            user = User.objects.get(userId=sender['id'], email=sender['email'])
            threads = Thread.objects.filter(is_archived=False, threadmember__user_member=user)
            thread = Thread.objects.get(id=self.thread_id)
            members = ThreadMember.objects.filter(thread=thread.id)
            messages = ThreadMessage.objects.filter(thread=thread)

            content = {
                'command': 'fetch_message',
                'thread': thread.name, 
                'thread_id': thread.id, 
                'threads': self.threads_to_json(threads),
                'message': self.fetches_to_json(messages),
                'members': self.members_to_json(members)
            }

            self.send_chat_message(content)

        except:
            try:
                subuser = Subuser.objects.get(subUserId=sender['id'], email=sender['email'])
                threads = Thread.objects.filter(is_archived=False, threadmember__subuser_member=subuser)

                thread = Thread.objects.get(id=self.thread_id)
                members = ThreadMember.objects.filter(thread=thread.id)
                messages = ThreadMessage.objects.filter(thread=thread)

                content = {
                    'command': 'fetch_message',
                    'thread': thread.name, 
                    'thread_id': thread.id, 
                    'threads': self.threads_to_json(threads),
                    'message': self.fetches_to_json(messages),
                    'members': self.members_to_json(members)
                }

                self.send_chat_message(content)
            except:
                return HttpResponse("No threads found.")

    def new_message(self, text_data):
            connection.schema_name = 'ot385ee74d'
            currentSchema = connection.schema_name 
            connection.set_schema(schema_name=currentSchema)

            print('new_message 1: ', currentSchema)

            thread = Thread.objects.get(id=self.thread_id)
            room = self.scope['url_route']['kwargs']['room_name']

            self.get_or_create_sender(text_data, thread)

            # if(any(x.isupper() for x in room)):
            #     member_name = re.sub(r"(?<=\w)([A-Z])", r" \1", room).split()

            #     try: 
            #         member_user = User.objects.get(firstName=member_name[0], lastName=member[1]) # Here
            #         ThreadMember.objects.get_or_create(user_member=member_user, thread=thread)

            #         self.get_or_create_sender(text_data, thread)

            #     except:
            #         member_subuser = Subuser.objects.get(firstName=member_name[0], lastName=member_name[1]) #Here
            #         ThreadMember.objects.get_or_create(subuser_member=member_subuser, thread=thread)

            #         self.get_or_create_sender(text_data, thread)
            # else:
            #     self.get_or_create_sender(text_data, thread)

    def get_or_create_sender(self, text_data, thread):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name 
        connection.set_schema(schema_name=currentSchema)
        sender = text_data['from']

        try: 
            user = User.objects.get(userId=sender['id'], email=sender['email'])
            ThreadMember.objects.get_or_create(user_member=user, thread=thread)

            message = ThreadMessage.objects.create(
                thread=thread,
                user_sender=user, 
                message=text_data['message']
            )
            
            content = {
                'command': 'new_message',
                'message': self.message_to_json(message)
            }

            return self.send_chat_message(content)

        except:
            subuser = Subuser.objects.get(subUserId=sender['id'], email=sender['email'])
            ThreadMember.objects.get_or_create(subuser_member=subuser, thread=thread)

            message = ThreadMessage.objects.create(
                thread=thread,
                subuser_sender=subuser,
                message=text_data['message']
            )

            content = {
                'command': 'new_message',
                'message': self.message_to_json(message)
            }

            return self.send_chat_message(content)

    def threads_to_json(self, threads):
        result = [] 
        for thread in threads:
            result.append(self.thread_to_json(thread))
        return result 

    def thread_to_json(self, thread):
        return {
            'thread': thread.name,
            'thread_id': thread.id,
            'date_created': str(thread.date_created)
        }

    def fetches_to_json(self, messages):
        result = [] 
        for messages in messages:
            result.append(self.fetch_to_json(messages))
        return result 

    def fetch_to_json(self, message):
        if message.user_sender is not None:
            return {
                'thread': message.thread.name, 
                'thread_id': message.thread.id,
                'user_sender': message.user_sender.email,
                'message': message.message,
                'message_id': message.id,
                'date_created': str(message.date_created)
            }

        if message.subuser_sender is not None:
            return {
                'thread': message.thread.name, 
                'thread_id': message.thread.id,
                'subuser_sender': message.subuser_sender.email, 
                'message': message.message,
                'message_id': message.id,
                'date_created': str(message.date_created)
            }

    def members_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.member_to_json(message))
        return result 

    def member_to_json(self, message):
        if message.user_member is not None:
            return {
            'thread': message.thread.name, 
            'user_member_id': message.user_member.userId,
            'user_member': message.user_member.email,
            'date_added': str(message.date_added)
        }

        if message.subuser_member is not None:
            return {
            'thread': message.thread.name, 
            'subuser_member_id': message.subuser_member.subUserId,
            'subuser_member': message.subuser_member.email,
            'date_added': str(message.date_added)
        }

    def new_members_to_json(self, members):
        result = []
        for member in members:
            result.append(self.new_member_to_json(member))
        return result 

    def new_member_to_json(self, member):
        return {
            'thread': member.thread,
            'member_id': member.member_id,
            'member_email': member.member_email
        }

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        if message.subuser_sender is not None:
            return {
            'thread': message.thread.name,
            'user_sender': message.user_sender.email,
            'message': message.message,
            'date_created': str(message.date_created)
        }

        if message.user_sender is not None:
            return {
            'thread': message.thread.name,
            'subuser_sender': message.subuser_sender.email,
            'message': message.message,
            'date_created': str(message.date_created)
        }

    commands = {
        'fetch_message': fetch_messages,
        'new_message': new_message,
        'delete_message': delete_message,
        'delete_thread': delete_thread,
        'new_member': new_member,
    }

    def connect(self):
        connection.schema_name = 'ot385ee74d'
        currentSchema = connection.schema_name 
        self.schema_used = currentSchema
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

        raise StopConsumer()

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data = json.loads(text_data)
        self.commands[text_data['command']](self, text_data)

    def send_chat_message(self, message):
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

    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))

