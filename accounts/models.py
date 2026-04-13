from django.contrib.auth.models import AbstractUser
from django.db import models

INTEREST_CHOICES = [
    ('AI/ML','AI/ML'), ('Startups','Startups'), ('Photography','Photography'),
    ('Reading','Reading'), ('Gaming','Gaming'), ('Travel','Travel'),
    ('Cooking','Cooking'), ('Music','Music'), ('Movies','Movies'),
    ('Fitness','Fitness'), ('Art & Design','Art & Design'), ('Research','Research'),
    ('Philosophy','Philosophy'), ('Writing','Writing'), ('Dance','Dance'),
    ('Astronomy','Astronomy'), ('Anime','Anime'), ('Cricket','Cricket'),
    ('Chess','Chess'), ('Hiking','Hiking'), ('Podcasts','Podcasts'),
    ('Finance','Finance'), ('Politics','Politics'), ('Fashion','Fashion'),
    ('Yoga','Yoga'), ('Comedy','Comedy'), ('Theatre','Theatre'),
    ('Volunteering','Volunteering'), ('Languages','Languages'), ('Mythology','Mythology'),
]

GENDER_CHOICES = [
    ('male','Male'), ('female','Female'),
    ('non-binary','Non-binary'), ('prefer_not_to_say','Prefer not to say'),
]

LOVE_LANGUAGE_CHOICES = [
    ('words','Words of affirmation'), ('acts','Acts of service'),
    ('gifts','Receiving gifts'), ('time','Quality time'), ('touch','Physical touch'),
]

HUMOR_CHOICES = [
    ('dry','Dry'), ('sarcastic','Sarcastic'), ('silly','Silly'),
    ('witty','Witty'), ('dark','Dark'), ('wholesome','Wholesome'),
]

COMMS_CHOICES = [
    ('texter','Text person'), ('caller','Phone calls'),
    ('voice_notes','Voice notes'), ('all_good',"All's good"),
]

GOAL_CHOICES = [
    ('serious','Serious relationship'), ('casual','Casual dating'),
    ('friendship','Friendship'), ('study_partner','Study partner'),
    ('see_what_happens','See what happens'),
]

REGION_CHOICES = [
    ('open','All India'), ('north','North India'), ('south','South India'),
    ('east','East India'), ('west','West India'), ('central','Central India'),
    ('northeast','Northeast India'),
]

YEAR_CHOICES = [(i, f'Year {i}') for i in range(1, 7)]

STREAM_CHOICES = [
    ('Computer Science','Computer Science'),
    ('Electronics & Communication','Electronics & Communication'),
    ('Mechanical Engineering','Mechanical Engineering'),
    ('Civil Engineering','Civil Engineering'),
    ('Electrical Engineering','Electrical Engineering'),
    ('Information Technology','Information Technology'),
    ('Business Administration','Business Administration'),
    ('Economics','Economics'), ('Psychology','Psychology'),
    ('Law','Law'), ('Medicine','Medicine'), ('Architecture','Architecture'),
    ('Arts & Humanities','Arts & Humanities'), ('Science','Science'),
    ('Commerce','Commerce'), ('Other','Other'),
]

AVATAR_COLORS = [
    '#D4537E','#1D9E75','#378ADD','#BA7517','#7F77DD','#E24B4A',
]

class User(AbstractUser):
    # Basic
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    pronouns = models.CharField(max_length=30, blank=True)

    # Academic
    college_name = models.CharField(max_length=150, blank=True)
    stream = models.CharField(max_length=60, choices=STREAM_CHOICES, blank=True)
    year_of_study = models.IntegerField(choices=YEAR_CHOICES, null=True, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)

    # Location
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default='open')

    # Profile content
    bio = models.TextField(max_length=300, blank=True)
    icebreaker = models.TextField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    avatar_color = models.CharField(max_length=10, default='#D4537E')
    avatar_initials = models.CharField(max_length=3, blank=True)

    # Interests stored as comma-separated
    interests = models.TextField(blank=True, help_text="Comma-separated interests")

    # Personality
    love_language = models.CharField(max_length=20, choices=LOVE_LANGUAGE_CHOICES, blank=True)
    humor_style = models.CharField(max_length=20, choices=HUMOR_CHOICES, blank=True)
    communication_style = models.CharField(max_length=20, choices=COMMS_CHOICES, blank=True)
    relationship_goal = models.CharField(max_length=25, choices=GOAL_CHOICES, blank=True)

    # Preferences
    preferred_gender = models.TextField(blank=True, help_text="Comma-separated genders")
    preferred_region = models.CharField(max_length=20, default='open')
    age_min = models.IntegerField(default=18)
    age_max = models.IntegerField(default=30)
    long_distance_ready = models.BooleanField(default=False)

    # Status
    is_verified = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)
    setup_step = models.IntegerField(default=0)
    is_banned = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)

    # Stats
    daily_prompt_streak = models.IntegerField(default=0)

    def get_interests_list(self):
        if not self.interests:
            return []
        return [i.strip() for i in self.interests.split(',') if i.strip()]

    def set_interests_list(self, interests_list):
        self.interests = ','.join(interests_list)

    def get_preferred_gender_list(self):
        if not self.preferred_gender:
            return []
        return [g.strip() for g in self.preferred_gender.split(',') if g.strip()]

    def get_initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif parts:
            return parts[0][:2].upper()
        return 'VM'

    def compute_vibe_score(self, other_user):
        my_interests = set(self.get_interests_list())
        other_interests = set(other_user.get_interests_list())
        shared = my_interests & other_interests
        interests_score = min(len(shared) * 10, 50)
        values_score = 20 if self.love_language and self.love_language == other_user.love_language else 0
        humor_score = 15 if self.humor_style and self.humor_style == other_user.humor_style else 0
        goal_score = 15 if self.relationship_goal and self.relationship_goal == other_user.relationship_goal else 0
        total = min(interests_score + values_score + humor_score + goal_score, 100)
        return {
            'total': total,
            'interests': interests_score,
            'values': values_score + goal_score,
            'humor': humor_score,
            'shared_interests': list(shared),
        }

    def __str__(self):
        return f"{self.full_name} ({self.username})"

    class Meta:
        db_table = 'accounts_user'
