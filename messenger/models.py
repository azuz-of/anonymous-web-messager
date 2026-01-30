import uuid
import string
import random
from django.db import models
from django.utils import timezone
from django.core.validators import MaxLengthValidator, MinLengthValidator


def generate_room_code():
    """Generate a unique 6-character alphanumeric room code."""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=6))
        if not Room.objects.filter(code=code).exists():
            return code


class Session(models.Model):
    """Anonymous user session model."""
    session_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nickname = models.CharField(max_length=30, validators=[MaxLengthValidator(30)])
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_banned = models.BooleanField(default=False)
    banned_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sessions'
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_banned', 'banned_until']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nickname} ({self.session_token})"

    def is_active(self):
        """Check if session is still active (not expired)."""
        if self.is_banned:
            if self.banned_until and self.banned_until > timezone.now():
                return False
            elif not self.banned_until:  # Permanent ban
                return False
        # Session expires after 24 hours of inactivity
        if (timezone.now() - self.last_active).total_seconds() > 86400:
            return False
        return True


class Room(models.Model):
    """Chat room model."""
    code = models.CharField(max_length=8, unique=True, default=generate_room_code, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    owner_session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, related_name='owned_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    message_retention_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'rooms'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code} ({self.name or 'Unnamed'})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_room_code()
        super().save(*args, **kwargs)


class Message(models.Model):
    """Chat message model."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, related_name='messages')
    content = models.TextField(validators=[MaxLengthValidator(1000)])
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    reported_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['session']),
            models.Index(fields=['is_deleted', 'timestamp']),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.session.nickname if self.session else 'Unknown'} in {self.room.code}"


class AuditLog(models.Model):
    """Security audit log model."""
    EVENT_TYPES = [
        ('login', 'Session Created'),
        ('room_create', 'Room Created'),
        ('room_join', 'Room Joined'),
        ('message_send', 'Message Sent'),
        ('rate_limit', 'Rate Limit Hit'),
        ('admin_action', 'Admin Action'),
        ('session_ban', 'Session Banned'),
        ('message_report', 'Message Reported'),
        ('room_delete', 'Room Deleted'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['session']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.timestamp}"


class BannedSession(models.Model):
    """Banned session tracking model."""
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='bans')
    reason = models.TextField()
    banned_by = models.CharField(max_length=100)  # Admin username or 'system'
    banned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # None for permanent ban

    class Meta:
        db_table = 'banned_sessions'
        indexes = [
            models.Index(fields=['session', 'expires_at']),
            models.Index(fields=['banned_at']),
        ]
        ordering = ['-banned_at']

    def __str__(self):
        return f"Ban for {self.session.nickname} by {self.banned_by}"

    def is_active(self):
        """Check if ban is still active."""
        if self.expires_at is None:
            return True  # Permanent ban
        return self.expires_at > timezone.now()
