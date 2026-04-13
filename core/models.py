from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class DailyPrompt(models.Model):
    prompt_text = models.TextField()
    category = models.CharField(max_length=20, choices=[
        ('values','Values'), ('fun','Fun'), ('future','Future'),
        ('opinion','Opinion'), ('random','Random'), ('deep','Deep'),
    ])
    active_date = models.DateField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.active_date}: {self.prompt_text[:60]}"

    class Meta:
        ordering = ['active_date']


class PromptAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompt_answers')
    prompt = models.ForeignKey(DailyPrompt, on_delete=models.CASCADE)
    answer_text = models.TextField(max_length=500)
    answered_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'prompt']

    def __str__(self):
        return f"{self.user} answered {self.prompt}"


class ConversationStarter(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starters_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starters_received')
    starter_text = models.TextField(max_length=300)
    status = models.CharField(max_length=10, default='pending', choices=[
        ('pending','Pending'), ('accepted','Accepted'), ('declined','Declined'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'to_user']

    def __str__(self):
        return f"{self.from_user} → {self.to_user}: {self.status}"


class Connection(models.Model):
    STATUS_CHOICES = [
        ('chatting','Chatting'), ('vibe_check','Vibe Check'),
        ('matched','Matched'), ('friends','Friends'),
        ('ended','Ended'), ('blocked','Blocked'),
    ]
    VIBE_RESPONSE_CHOICES = [
        ('explore_more','Explore more'),
        ('stay_friends','Stay friends'),
        ('end','End'),
    ]

    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_a')
    user_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_b')
    status = models.CharField(max_length=15, default='chatting', choices=STATUS_CHOICES)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_connections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Vibe check (day 7)
    vibe_check_due = models.DateTimeField(null=True, blank=True)
    user_a_vibe_response = models.CharField(max_length=15, blank=True, choices=VIBE_RESPONSE_CHOICES)
    user_b_vibe_response = models.CharField(max_length=15, blank=True, choices=VIBE_RESPONSE_CHOICES)
    vibe_check_resolved = models.BooleanField(default=False)

    # Photo reveal
    user_a_reveal_requested = models.BooleanField(default=False)
    user_b_reveal_requested = models.BooleanField(default=False)
    photos_revealed = models.BooleanField(default=False)

    # Cache
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.CharField(max_length=100, blank=True)
    message_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user_a', 'user_b']

    def get_other_user(self, user):
        return self.user_b if self.user_a == user else self.user_a

    def get_my_vibe_response(self, user):
        return self.user_a_vibe_response if self.user_a == user else self.user_b_vibe_response

    def days_active(self):
        return (timezone.now() - self.created_at).days

    def days_until_vibe_check(self):
        if self.vibe_check_due:
            delta = self.vibe_check_due - timezone.now()
            return max(0, delta.days)
        return None

    def is_vibe_check_due(self):
        return self.vibe_check_due and timezone.now() >= self.vibe_check_due

    def resolve_vibe_check(self):
        a = self.user_a_vibe_response
        b = self.user_b_vibe_response
        if a and b:
            if a == 'explore_more' and b == 'explore_more':
                self.status = 'matched'
            elif a == 'end' or b == 'end':
                self.status = 'ended'
            else:
                self.status = 'friends'
            self.vibe_check_resolved = True
            self.save()

    def __str__(self):
        return f"{self.user_a} ↔ {self.user_b} [{self.status}]"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text','Text'), ('system','System'),
    ]
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField(max_length=1000)
    message_type = models.CharField(max_length=10, default='text', choices=MESSAGE_TYPES)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:40]}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('new_starter','New Starter'), ('new_message','New Message'),
        ('vibe_check','Vibe Check'), ('reveal_request','Reveal Request'),
        ('reveal_accepted','Reveal Accepted'), ('match','Match'), ('system','System'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    connection = models.ForeignKey(Connection, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}: {self.title}"


class Report(models.Model):
    REASON_CHOICES = [
        ('harassment','Harassment or bullying'),
        ('inappropriate_content','Inappropriate content'),
        ('fake_profile','Fake profile'),
        ('spam','Spam'),
        ('underage','Appears to be underage'),
        ('other','Other'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    connection = models.ForeignKey(Connection, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, default='pending', choices=[
        ('pending','Pending'), ('reviewed','Reviewed'), ('resolved','Resolved'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reporter} reported {self.reported}: {self.reason}"


class BlockedUser(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['blocker', 'blocked']

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"
