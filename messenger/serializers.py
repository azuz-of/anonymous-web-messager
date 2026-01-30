from rest_framework import serializers
from .models import Session, Room, Message, AuditLog, BannedSession
import html


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model."""
    
    class Meta:
        model = Session
        fields = ['session_token', 'nickname', 'created_at', 'last_active']
        read_only_fields = ['session_token', 'created_at', 'last_active']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model."""
    owner_nickname = serializers.CharField(source='owner_session.nickname', read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = ['code', 'name', 'owner_session', 'owner_nickname', 'created_at', 
                  'message_retention_days', 'is_active', 'max_participants', 'participant_count']
        read_only_fields = ['code', 'created_at']
    
    def get_participant_count(self, obj):
        """Get count of unique sessions that have sent messages in this room."""
        return obj.messages.values('session').distinct().count()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    session_nickname = serializers.CharField(source='session.nickname', read_only=True)
    room_code = serializers.CharField(source='room.code', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'room_code', 'session', 'session_nickname', 
                  'content', 'timestamp', 'is_deleted', 'reported_count']
        read_only_fields = ['id', 'timestamp', 'is_deleted', 'reported_count']
    
    def validate_content(self, value):
        """Sanitize and validate message content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        # HTML escape to prevent XSS
        sanitized = html.escape(value.strip())
        if len(sanitized) > 1000:
            raise serializers.ValidationError("Message content cannot exceed 1000 characters.")
        return sanitized


class CreateSessionSerializer(serializers.Serializer):
    """Serializer for creating a new session."""
    nickname = serializers.CharField(max_length=30, min_length=1)
    
    def validate_nickname(self, value):
        """Sanitize nickname."""
        sanitized = html.escape(value.strip())
        if len(sanitized) > 30:
            raise serializers.ValidationError("Nickname cannot exceed 30 characters.")
        if not sanitized:
            raise serializers.ValidationError("Nickname cannot be empty.")
        return sanitized


class CreateRoomSerializer(serializers.Serializer):
    """Serializer for creating a new room."""
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    message_retention_days = serializers.IntegerField(default=30, min_value=1, max_value=365)
    max_participants = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    
    def validate_name(self, value):
        """Sanitize room name."""
        if value:
            return html.escape(value.strip())
        return value


class JoinRoomSerializer(serializers.Serializer):
    """Serializer for joining a room."""
    room_code = serializers.CharField(max_length=8, min_length=6)
    
    def validate_room_code(self, value):
        """Validate and normalize room code."""
        return value.upper().strip()


class ReportMessageSerializer(serializers.Serializer):
    """Serializer for reporting a message."""
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_reason(self, value):
        """Sanitize report reason."""
        if value:
            return html.escape(value.strip())
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    session_nickname = serializers.CharField(source='session.nickname', read_only=True)
    room_code = serializers.CharField(source='room.code', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'event_type', 'event_type_display', 'session', 'session_nickname',
                  'room', 'room_code', 'ip_address', 'details', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class BannedSessionSerializer(serializers.ModelSerializer):
    """Serializer for BannedSession model."""
    session_nickname = serializers.CharField(source='session.nickname', read_only=True)
    
    class Meta:
        model = BannedSession
        fields = ['id', 'session', 'session_nickname', 'reason', 'banned_by',
                  'banned_at', 'expires_at']
        read_only_fields = ['id', 'banned_at']
