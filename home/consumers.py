from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime
from channels.db import database_sync_to_async
import uuid
from django.db.models import Q
from .models import Messages, Group

MESSAGE_MAX_LENGTH = 50

class ChatConsumer(AsyncWebsocketConsumer):

    # Users stored here temporarily
    USERS_CONNECTED = {}

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        if self.scope["user"].is_authenticated:
            await self.accept()
            self.USERS_CONNECTED[self.user.username] = self.user.username

            # All the users is notified about new user joining
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "new_user_joined",
                    "data": self.USERS_CONNECTED,
                    "fromUser": self.user.username,
                },
            )

        else:
            await self.accept()
            await self.send(text_data=json.dumps({
                "msg_type": 'ERROR_OCCURED',
                "error_message": "UN_AUTHENTICATED",
                "user": self.user.username,
            }))

            await self.close(code=4001)

    async def disconnect(self, code):

        # Firing signals to other user about user who just disconneted
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "disconnected",
                "fromUser": self.user.username,
            },
        )

        # User data is cleared and discarded from the room
        del self.USERS_CONNECTED[self.user.username]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('msg_type')
        fromUser= data.get('fromUser')
        print(msg_type)

        if msg_type == 'TEXT_MESSAGE':
            message = data.get('message')

            if len(message) <= MESSAGE_MAX_LENGTH:
                msg_id = uuid.uuid4()

                await self.save_text_message(msg_id,message)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'msg_id' : str(msg_id),
                        'fromUser': fromUser,
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'msg_type': 'ERROR_OCCURED',
                    'error_message': "MESSAGE_OUT_OF_LENGTH",
                    'message': message,
                    'timestampe': str(datetime.now()),
                    'fromUser': fromUser,
                }))

        elif msg_type == "offer":
            offer = data.get('offer')
            is_video = data.get('is_video')
            toUser = data.get('toUser')

            # to notify the callee we sent an event to the group name
            # and their's groun name is the name
            msg_id = uuid.uuid4()
            await self.channel_layer.group_send(
                     self.room_group_name,
                    {
                    'type': 'user_calling',
                    'fromUser': fromUser,
                    'offer': offer,
                    'toUser': toUser,
                    'msg_id' : str(msg_id),
                    'is_video': is_video
                    }
                )
            
            # mess = f'Calling by {fromUser}'
            # await self.channel_layer.group_send(
            #         self.room_group_name,
            #         {
            #             'type': 'chat_message',
            #             'message': mess,
            #             'msg_id' : str(msg_id),
            #             'fromUser': fromUser,
            #         }
            #     )            
            # current_user_id = await self.save_text_message(msg_id,mess)

        elif msg_type == "answer":
            answer = data.get('answer')
            toUser = data.get('toUser')
            # has received call from someone now notify the calling user
            # we can notify to the group with the caller name
            
            await self.channel_layer.group_send(
                     self.room_group_name,
                    {
                    'type': 'user_answer_call',
                    'answer': answer,
                    'fromUser': fromUser,
                    'toUser': toUser,
                    }
                )

        elif msg_type == "candidate":
            candidate = data.get('candidate')
            toUser = data.get('toUser')
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'ICEcandidate',
                    'candidate': candidate,
                    'fromUser': fromUser,
                    'toUser':toUser
                    }
                )

        elif msg_type == "stop":
            await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                    'type': 'stop_message',
                    'fromUser': fromUser,
                    }
                )        

    # Receive message from room group
    async def new_user_joined(self, event):
        await self.send(
            json.dumps(
                {
                    "msg_type": "users_connected",
                    "fromUser": event["fromUser"],
                    "users_connected": event["data"]
                }
            )
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'msg_type': 'TEXT_MESSAGE',
            'message': event['message'],
            'timestampe': str(datetime.now()),
            'msg_id' : event["msg_id"],
            'fromUser':  event["fromUser"],
        }))
    
    async def user_calling(self, event):

        await self.send(text_data=json.dumps({
            'msg_type': 'offer',
            'offer': event['offer'],
            'fromUser': event["fromUser"],
            'toUser': event['toUser'],
            'is_video': event['is_video']
        }))

    async def user_answer_call(self, event):

        await self.send(text_data=json.dumps({
            'msg_type': 'answer',
            'answer': event['answer'],
            'fromUser':  event["fromUser"],
            'toUser': event['toUser'],
        }))

    async def ICEcandidate(self, event):
        await self.send(text_data=json.dumps({
            'msg_type': 'candidate',
            'candidate': event['candidate'],
            'fromUser':  event["fromUser"],
            'toUser': event['toUser'],
        }))
    
    async def stop_message(self, event):
        await self.send(text_data=json.dumps({
            'msg_type': 'stop',
            'fromUser':  event["fromUser"],
        }))

    async def disconnected(self, event):
        await self.send(text_data=json.dumps({
                    "msg_type": "disconnected",
                    "fromUser": event["fromUser"],
        }))

    @database_sync_to_async
    def save_text_message(self,msg_id,message):
        session_name = self.room_group_name[5:]

        session_inst = Group.objects.filter(Q(group_name = session_name))

        if session_inst.exists():
            session_inst = session_inst.first()
            message_json = {
                "msg": message,
                "timestamp": str(datetime.now()),
            }
            Messages.objects.create(id = msg_id,parent_group=session_inst, parent_user=self.user, message_detail=message_json)
