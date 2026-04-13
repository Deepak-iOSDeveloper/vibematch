from django.contrib import admin
from .models import DailyPrompt, PromptAnswer, Connection, Message, Notification, Report, BlockedUser, ConversationStarter

@admin.register(DailyPrompt)
class DailyPromptAdmin(admin.ModelAdmin):
    list_display = ['active_date', 'category', 'prompt_text']
    list_filter = ['category']

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['user_a', 'user_b', 'status', 'created_at', 'vibe_check_due']
    list_filter = ['status']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reported', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason']
    actions = ['mark_reviewed']

    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')

admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(BlockedUser)
admin.site.register(ConversationStarter)
admin.site.register(PromptAnswer)
