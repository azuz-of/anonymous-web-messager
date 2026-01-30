"""Utility functions for the messenger app."""
import html
from django.utils import timezone
from .models import Session, AuditLog


def sanitize_input(text, max_length=None):
    """Sanitize user input to prevent XSS attacks."""
    if not text:
        return ""
    sanitized = html.escape(text.strip())
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_session_from_token(token):
    """Get session from token, checking if it's active."""
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


def log_audit_event(event_type, session=None, room=None, ip_address=None, details=None):
    """Helper function to create audit log entries."""
    AuditLog.objects.create(
        event_type=event_type,
        session=session,
        room=room,
        ip_address=ip_address,
        details=details or {}
    )
