from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['full_name', 'email', 'college_name', 'profile_complete', 'is_banned', 'date_joined']
    list_filter = ['profile_complete', 'is_banned', 'gender', 'region']
    search_fields = ['full_name', 'email', 'college_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('full_name', 'age', 'gender', 'pronouns', 'bio', 'icebreaker', 'photo', 'avatar_color', 'avatar_initials')}),
        ('Academic', {'fields': ('college_name', 'stream', 'year_of_study', 'graduation_year', 'city', 'state', 'region')}),
        ('Personality', {'fields': ('interests', 'love_language', 'humor_style', 'communication_style', 'relationship_goal')}),
        ('Preferences', {'fields': ('preferred_gender', 'preferred_region', 'age_min', 'age_max', 'long_distance_ready')}),
        ('Status', {'fields': ('is_verified', 'profile_complete', 'setup_step', 'is_banned')}),
    )
