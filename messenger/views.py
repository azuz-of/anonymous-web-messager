from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Session, Room, Message, AuditLog, BannedSession
from .serializers import (
    SessionSerializer, RoomSerializer, MessageSerializer,
    CreateSessionSerializer, CreateRoomSerializer, JoinRoomSerializer,
    ReportMessageSerializer, AuditLogSerializer, BannedSessionSerializer
)
from .utils import get_client_ip, get_session_from_token, log_audit_event, sanitize_input


@api_view(['POST'])
def create_session(request):
    """Create a new anonymous session."""
    serializer = CreateSessionSerializer(data=request.data)
    if serializer.is_valid():
        ip_address = get_client_ip(request)
        
        # Create session
        session = Session.objects.create(
            nickname=serializer.validated_data['nickname'],
            ip_address=ip_address
        )
        
        # Log audit event
        log_audit_event('login', session=session, ip_address=ip_address)
        
        return Response({
            'session_token': str(session.session_token),
            'nickname': session.nickname,
            'created_at': session.created_at
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def validate_session(request):
    """Validate a session token."""
    token = request.query_params.get('token')
    if not token:
        return Response({'error': 'Token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    session = get_session_from_token(token)
    if session:
        serializer = SessionSerializer(session)
        return Response(serializer.data)
    
    return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def create_room(request):
    """Create a new chat room."""
    token = request.headers.get('X-Session-Token') or request.data.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = CreateRoomSerializer(data=request.data)
    if serializer.is_valid():
        room = Room.objects.create(
            name=serializer.validated_data.get('name', ''),
            owner_session=session,
            message_retention_days=serializer.validated_data.get('message_retention_days', 30),
            max_participants=serializer.validated_data.get('max_participants')
        )
        
        # Log audit event
        log_audit_event('room_create', session=session, room=room, ip_address=get_client_ip(request))
        
        serializer_response = RoomSerializer(room)
        return Response(serializer_response.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def join_room(request):
    """Join a room by code."""
    token = request.headers.get('X-Session-Token') or request.data.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = JoinRoomSerializer(data=request.data)
    if serializer.is_valid():
        room_code = serializer.validated_data['room_code']
        try:
            room = Room.objects.get(code=room_code, is_active=True)
            
            # Check max participants
            if room.max_participants:
                participant_count = room.messages.values('session').distinct().count()
                if participant_count >= room.max_participants:
                    return Response({'error': 'Room is full'}, status=status.HTTP_403_FORBIDDEN)
            
            # Log audit event
            log_audit_event('room_join', session=session, room=room, ip_address=get_client_ip(request))
            
            serializer_response = RoomSerializer(room)
            return Response(serializer_response.data)
        except Room.DoesNotExist:
            log_audit_event('room_join', session=session, ip_address=get_client_ip(request),
                          details={'room_code': room_code, 'error': 'Room not found'})
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_room(request, code):
    """Get room details."""
    try:
        room = Room.objects.get(code=code.upper(), is_active=True)
        serializer = RoomSerializer(room)
        return Response(serializer.data)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_room_messages(request, code):
    """Get message history for a room."""
    try:
        room = Room.objects.get(code=code.upper(), is_active=True)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 50))
    
    messages = Message.objects.filter(room=room, is_deleted=False).order_by('-timestamp')
    paginator = Paginator(messages, page_size)
    page_obj = paginator.get_page(page)
    
    serializer = MessageSerializer(page_obj, many=True)
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'page': page,
        'page_size': page_size,
        'total_pages': paginator.num_pages
    })


@api_view(['POST'])
def send_message(request):
    """Send a message via REST API (alternative to WebSocket)."""
    token = request.headers.get('X-Session-Token') or request.data.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    room_code = request.data.get('room_code')
    content = request.data.get('content', '').strip()
    
    if not room_code or not content:
        return Response({'error': 'room_code and content required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(code=room_code.upper(), is_active=True)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Validate and sanitize content
    sanitized_content = sanitize_input(content, max_length=1000)
    if not sanitized_content:
        return Response({'error': 'Message content cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create message
    message = Message.objects.create(
        room=room,
        session=session,
        content=sanitized_content
    )
    
    # Log audit event
    log_audit_event('message_send', session=session, room=room, ip_address=get_client_ip(request))
    
    serializer = MessageSerializer(message)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def report_message(request, message_id):
    """Report a message for moderation."""
    token = request.headers.get('X-Session-Token') or request.data.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        message = Message.objects.get(id=message_id, is_deleted=False)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ReportMessageSerializer(data=request.data)
    if serializer.is_valid():
        message.reported_count += 1
        message.save(update_fields=['reported_count'])
        
        # Log audit event
        log_audit_event('message_report', session=session, room=message.room,
                       ip_address=get_client_ip(request),
                       details={'message_id': message_id, 'reason': serializer.validated_data.get('reason', '')})
        
        return Response({'message': 'Message reported successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def block_session(request):
    """Block a session (room owner only)."""
    token = request.headers.get('X-Session-Token') or request.data.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    room_code = request.data.get('room_code')
    target_session_token = request.data.get('target_session_token')
    
    if not room_code or not target_session_token:
        return Response({'error': 'room_code and target_session_token required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(code=room_code.upper(), is_active=True)
        if room.owner_session != session:
            return Response({'error': 'Only room owner can block sessions'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        target_session = Session.objects.get(session_token=target_session_token)
        target_session.is_banned = True
        target_session.save(update_fields=['is_banned'])
        
        # Create ban record
        BannedSession.objects.create(
            session=target_session,
            reason=request.data.get('reason', 'Blocked by room owner'),
            banned_by=session.nickname
        )
        
        # Log audit event
        log_audit_event('session_ban', session=session, room=room,
                       ip_address=get_client_ip(request),
                       details={'target_session': str(target_session_token)})
        
        return Response({'message': 'Session blocked successfully'}, status=status.HTTP_200_OK)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    except Session.DoesNotExist:
        return Response({'error': 'Target session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_reports(request):
    """Get reported messages (room owner only)."""
    token = request.headers.get('X-Session-Token') or request.query_params.get('session_token')
    if not token:
        return Response({'error': 'Session token required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    session = get_session_from_token(token)
    if not session:
        return Response({'error': 'Invalid or expired session'}, status=status.HTTP_401_UNAUTHORIZED)
    
    room_code = request.query_params.get('room_code')
    if not room_code:
        return Response({'error': 'room_code required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        room = Room.objects.get(code=room_code.upper(), is_active=True)
        if room.owner_session != session:
            return Response({'error': 'Only room owner can view reports'}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        reported_messages = Message.objects.filter(
            room=room,
            reported_count__gt=0,
            is_deleted=False
        ).order_by('-reported_count', '-timestamp')
        
        serializer = MessageSerializer(reported_messages, many=True)
        return Response(serializer.data)
    except Room.DoesNotExist:
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
