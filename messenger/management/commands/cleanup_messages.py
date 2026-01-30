from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from messenger.models import Message, Room, AuditLog


class Command(BaseCommand):
    help = 'Clean up messages older than their room\'s retention period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        deleted_count = 0
        rooms_processed = 0
        
        # Get all active rooms
        rooms = Room.objects.filter(is_active=True)
        
        for room in rooms:
            rooms_processed += 1
            retention_days = room.message_retention_days
            cutoff_date = timezone.now() - timedelta(days=retention_days)
            
            # Find messages older than retention period
            old_messages = Message.objects.filter(
                room=room,
                timestamp__lt=cutoff_date,
                is_deleted=False
            )
            
            count = old_messages.count()
            if count > 0:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Would delete {count} message(s) from room {room.code} '
                            f'(retention: {retention_days} days)'
                        )
                    )
                else:
                    old_messages.update(is_deleted=True)
                    deleted_count += count
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Deleted {count} message(s) from room {room.code}'
                        )
                    )
                    
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
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry run complete. Would process {rooms_processed} room(s).'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCleanup complete. Deleted {deleted_count} message(s) from {rooms_processed} room(s).'
                )
            )
