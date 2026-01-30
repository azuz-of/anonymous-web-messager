from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Session, Room, Message, AuditLog, BannedSession


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'session_token', 'ip_address', 'is_banned', 'created_at', 'last_active']
    list_filter = ['is_banned', 'created_at']
    search_fields = ['nickname', 'session_token', 'ip_address']
    readonly_fields = ['session_token', 'created_at', 'last_active']
    actions = ['ban_sessions', 'unban_sessions']
    
    def ban_sessions(self, request, queryset):
        """Ban selected sessions."""
        count = 0
        for session in queryset:
            if not session.is_banned:
                session.is_banned = True
                session.save()
                BannedSession.objects.create(
                    session=session,
                    reason='Banned by admin',
                    banned_by=request.user.username
                )
                count += 1
        self.message_user(request, f'{count} session(s) banned successfully.')
    ban_sessions.short_description = "Ban selected sessions"
    
    def unban_sessions(self, request, queryset):
        """Unban selected sessions."""
        count = 0
        for session in queryset:
            if session.is_banned:
                session.is_banned = False
                session.banned_until = None
                session.save()
                count += 1
        self.message_user(request, f'{count} session(s) unbanned successfully.')
    unban_sessions.short_description = "Unban selected sessions"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'owner_nickname', 'message_count', 'participant_count', 
                   'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['code', 'created_at']
    actions = ['deactivate_rooms', 'activate_rooms']
    
    def owner_nickname(self, obj):
        return obj.owner_session.nickname if obj.owner_session else 'N/A'
    owner_nickname.short_description = 'Owner'
    
    def message_count(self, obj):
        return obj.messages.filter(is_deleted=False).count()
    message_count.short_description = 'Messages'
    
    def participant_count(self, obj):
        return obj.messages.values('session').distinct().count()
    participant_count.short_description = 'Participants'
    
    def deactivate_rooms(self, request, queryset):
        """Deactivate selected rooms."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} room(s) deactivated successfully.')
    deactivate_rooms.short_description = "Deactivate selected rooms"
    
    def activate_rooms(self, request, queryset):
        """Activate selected rooms."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} room(s) activated successfully.')
    activate_rooms.short_description = "Activate selected rooms"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room_code', 'session_nickname', 'content_preview', 
                   'reported_count', 'is_deleted', 'timestamp']
    list_filter = ['is_deleted', 'reported_count', 'timestamp']
    search_fields = ['content', 'room__code', 'session__nickname']
    readonly_fields = ['timestamp']
    actions = ['delete_messages', 'restore_messages', 'clear_reports']
    
    def room_code(self, obj):
        return obj.room.code
    room_code.short_description = 'Room'
    
    def session_nickname(self, obj):
        return obj.session.nickname if obj.session else 'Unknown'
    session_nickname.short_description = 'Sender'
    
    def content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = 'Content'
    
    def delete_messages(self, request, queryset):
        """Soft delete selected messages."""
        count = queryset.update(is_deleted=True)
        self.message_user(request, f'{count} message(s) deleted successfully.')
    delete_messages.short_description = "Delete selected messages"
    
    def restore_messages(self, request, queryset):
        """Restore selected messages."""
        count = queryset.update(is_deleted=False)
        self.message_user(request, f'{count} message(s) restored successfully.')
    restore_messages.short_description = "Restore selected messages"
    
    def clear_reports(self, request, queryset):
        """Clear report counts for selected messages."""
        count = queryset.update(reported_count=0)
        self.message_user(request, f'{count} message(s) report counts cleared.')
    clear_reports.short_description = "Clear report counts"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'session_nickname', 'room_code', 'ip_address', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['session__nickname', 'room__code', 'ip_address']
    readonly_fields = ['event_type', 'session', 'room', 'ip_address', 'details', 'timestamp']
    
    def session_nickname(self, obj):
        return obj.session.nickname if obj.session else 'N/A'
    session_nickname.short_description = 'Session'
    
    def room_code(self, obj):
        return obj.room.code if obj.room else 'N/A'
    room_code.short_description = 'Room'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BannedSession)
class BannedSessionAdmin(admin.ModelAdmin):
    list_display = ['session_nickname', 'reason', 'banned_by', 'banned_at', 'expires_at', 'is_active']
    list_filter = ['banned_at', 'expires_at']
    search_fields = ['session__nickname', 'banned_by', 'reason']
    readonly_fields = ['banned_at']
    
    def session_nickname(self, obj):
        return obj.session.nickname
    session_nickname.short_description = 'Session'
    
    def is_active(self, obj):
        if obj.expires_at is None:
            return obj.session.is_banned
        return obj.expires_at > timezone.now() and obj.session.is_banned
    is_active.boolean = True
    is_active.short_description = 'Active'


# Custom Admin Dashboard View
class MessengerAdminSite(admin.AdminSite):
    site_header = "Anonymous Messenger Administration"
    site_title = "Messenger Admin"
    index_title = "Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='messenger_dashboard'),
            path('dashboard/stats/', self.admin_view(self.stats_api), name='messenger_stats'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view."""
        context = {
            **self.each_context(request),
            'title': 'Messenger Dashboard',
        }
        return render(request, 'admin/messenger_dashboard.html', context)
    
    def stats_api(self, request):
        """API endpoint for dashboard statistics."""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            'total_sessions': Session.objects.count(),
            'active_sessions_24h': Session.objects.filter(last_active__gte=last_24h).count(),
            'banned_sessions': Session.objects.filter(is_banned=True).count(),
            'total_rooms': Room.objects.count(),
            'active_rooms': Room.objects.filter(is_active=True).count(),
            'total_messages': Message.objects.filter(is_deleted=False).count(),
            'messages_24h': Message.objects.filter(timestamp__gte=last_24h, is_deleted=False).count(),
            'reported_messages': Message.objects.filter(reported_count__gt=0, is_deleted=False).count(),
            'audit_logs_24h': AuditLog.objects.filter(timestamp__gte=last_24h).count(),
            'rate_limit_hits_24h': AuditLog.objects.filter(
                event_type='rate_limit',
                timestamp__gte=last_24h
            ).count(),
            'recent_rooms': list(Room.objects.filter(is_active=True)
                                .order_by('-created_at')[:10]
                                .values('code', 'name', 'created_at', 'message_retention_days')),
            'recent_audit_logs': list(AuditLog.objects
                                     .order_by('-timestamp')[:20]
                                     .values('event_type', 'timestamp', 'ip_address',
                                            'session__nickname', 'room__code')),
        }
        return JsonResponse(stats)


# Use custom admin site (optional - can use default admin.site instead)
# admin_site = MessengerAdminSite(name='messenger_admin')
# For now, we'll use the default admin.site and add custom views

# Add custom dashboard to default admin
admin.site.site_header = "Anonymous Messenger Administration"
admin.site.site_title = "Messenger Admin"
admin.site.index_title = "Dashboard"
