"""
Celery tasks for background jobs.
If Celery is not available, use Django management commands instead.
"""
from django.utils import timezone
from datetime import timedelta
from .models import Message, Room, AuditLog


def cleanup_old_messages():
    """
    Clean up messages older than their room's retention period.
    This function can be called by Celery or as a management command.
    """
    deleted_count = 0
    rooms_processed = 0
    
    rooms = Room.objects.filter(is_active=True)
    
    for room in rooms:
        rooms_processed += 1
        retention_days = room.message_retention_days
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        old_messages = Message.objects.filter(
            room=room,
            timestamp__lt=cutoff_date,
            is_deleted=False
        )
        
        count = old_messages.count()
        if count > 0:
            old_messages.update(is_deleted=True)
            deleted_count += count
            
            # Log cleanup event
            AuditLog.objects.create(
                event_type='admin_action',
                room=room,
                details={
                    'action': 'cleanup_messages',
                    'count': count,
                    'retention_days': retention_days
                }
            )
    
    return {
        'deleted_count': deleted_count,
        'rooms_processed': rooms_processed
    }
