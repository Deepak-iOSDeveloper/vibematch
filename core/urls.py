from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('discover/', views.discover_view, name='discover'),
    path('discover/send-starter/', views.send_starter, name='send_starter'),
    path('discover/prompt-answer/', views.submit_prompt_answer, name='submit_prompt_answer'),
    path('chats/', views.chat_list_view, name='chat_list'),
    path('chats/<int:connection_id>/', views.chat_view, name='chat'),
    path('chats/starter/<int:starter_id>/accept/', views.accept_starter, name='accept_starter'),
    path('chats/starter/<int:starter_id>/decline/', views.decline_starter, name='decline_starter'),
    path('chats/<int:connection_id>/vibe-check/', views.submit_vibe_check, name='vibe_check'),
    path('chats/<int:connection_id>/reveal/', views.request_reveal, name='request_reveal'),
    path('report/', views.report_user, name='report_user'),
    path('block/', views.block_user, name='block_user'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('settings/', views.settings_view, name='settings'),
    path('api/unread/', views.unread_count, name='unread_count'),
]
