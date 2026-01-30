from django.urls import path
from . import views

urlpatterns = [
    # Session management
    path('api/session/create/', views.create_session, name='create_session'),
    path('api/session/validate/', views.validate_session, name='validate_session'),
    
    # Room management
    path('api/rooms/create/', views.create_room, name='create_room'),
    path('api/rooms/join/', views.join_room, name='join_room'),
    path('api/rooms/<str:code>/', views.get_room, name='get_room'),
    path('api/rooms/<str:code>/messages/', views.get_room_messages, name='get_room_messages'),
    
    # Messaging
    path('api/messages/send/', views.send_message, name='send_message'),
    path('api/messages/<int:message_id>/report/', views.report_message, name='report_message'),
    
    # Moderation
    path('api/moderation/block-session/', views.block_session, name='block_session'),
    path('api/moderation/reports/', views.get_reports, name='get_reports'),
]
