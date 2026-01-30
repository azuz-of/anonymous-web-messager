import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.utils import timezone
from .models import Session, Room, Message, AuditLog
from .utils import sanitize_input, log_audit_event


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        # Parse query string for session token
        query_string = self.scope.get('query_string', b'').decode()
        self.session_token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                self.session_token = param.split('=', 1)[1]
                break
        
        # Validate session
        self.session = await self.get_session(self.session_token)
        if not self.session:
            await self.close()
            return
        
        # Get room
        self.room = await self.get_room(self.room_code)
        if not self.room or not self.room.is_active:
            await self.close()
            return
        
        # Check if session is banned
        if self.session.is_banned:
            if self.session.banned_until and self.session.banned_until > timezone.now():
                await self.close()
                return
            elif not self.session.banned_until:  # Permanent ban
                await self.close()
                return
        
        # Join room group
        self.room_group_name = f'chat_{self.room_code}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Log connection
        await self.log_audit_async('room_join', self.session, self.room)
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle message received from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message."""
        content = data.get('content', '').strip()
        
        # Validate and sanitize
        if not content or len(content) > 1000:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message content'
            }))
            return
        
        # Rate limiting check
        cache_key = f"ratelimit:ws:{self.session.session_token}"
        count = cache.get(cache_key, 0)
        if count >= 10:  # 10 messages per minute
            await self.log_audit_async('rate_limit', self.session, self.room, 
                                      {'source': 'websocket'})
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Rate limit exceeded. Please slow down.'
            }))
            return
        
        cache.set(cache_key, count + 1, 60)  # 60 seconds
        
        # Sanitize content
        sanitized_content = sanitize_input(content, max_length=1000)
        
        # Save message to database
        message = await self.save_message(sanitized_content)
        
        if message:
            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message['id'],
                        'session_nickname': self.session.nickname,
                        'content': sanitized_content,
                        'timestamp': message['timestamp'],
                    }
                }
            )
            
            # Log message sent
            await self.log_audit_async('message_send', self.session, self.room)
    
    async def handle_typing(self, data):
        """Handle typing indicator."""
        # Broadcast typing indicator to room group (excluding sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'nickname': self.session.nickname,
                'is_typing': data.get('is_typing', False)
            }
        )
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator back to the sender
        if event['nickname'] != self.session.nickname:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'nickname': event['nickname'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def get_session(self, token):
        """Get session from token."""
        try:
            session = Session.objects.get(session_token=token)
            if not session.is_active():
                return None
            # Update last_active
            session.last_active = timezone.now()
            session.save(update_fields=['last_active'])
            return session
        except Session.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_room(self, code):
        """Get room by code."""
        try:
            return Room.objects.get(code=code, is_active=True)
        except Room.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        message = Message.objects.create(
            room=self.room,
            session=self.session,
            content=content
        )
        return {
            'id': message.id,
            'timestamp': message.timestamp.isoformat()
        }
    
    @database_sync_to_async
    def log_audit_async(self, event_type, session=None, room=None, details=None):
        """Log audit event asynchronously."""
        ip_address = None
        if hasattr(self.scope, 'client'):
            ip_address = self.scope['client'][0] if self.scope.get('client') else None
        
        AuditLog.objects.create(
            event_type=event_type,
            session=session,
            room=room,
            ip_address=ip_address,
            details=details or {}
        )
