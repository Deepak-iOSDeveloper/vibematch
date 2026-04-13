from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import DailyPrompt

class Command(BaseCommand):
    help = 'Seeds daily prompts into the database'

    def handle(self, *args, **options):
        today = timezone.localdate()
        prompts = [
            ('What is something you changed your mind about in the last year?', 'values', 0),
            ('If you could master one skill overnight, what would it be and why?', 'fun', 1),
            ('What does your ideal Saturday look like?', 'random', 2),
            ('What kind of work makes you lose track of time?', 'values', 3),
            ('What is a hot take you have that most people disagree with?', 'opinion', 4),
            ('What is one thing you want to build or create before you turn 30?', 'future', 5),
            ('Describe yourself in exactly three words.', 'random', 6),
            ('What is a book, podcast, or video that genuinely changed how you think?', 'values', 7),
            ('What topic could you talk about for hours without getting bored?', 'fun', 8),
            ('If your life had a soundtrack, what genre would it be?', 'random', 9),
            ('What does success mean to you right now?', 'deep', 10),
            ('What is something small that makes you genuinely happy?', 'fun', 11),
            ('What is your relationship with ambition — driven or burnt out?', 'deep', 12),
            ('If you could have coffee with any living person, who and why?', 'random', 13),
            ('What is something you are actively trying to get better at?', 'values', 14),
            ('What is the best advice you have ever received?', 'values', 15),
            ('What fear have you overcome that you are most proud of?', 'deep', 16),
            ('What makes you laugh out loud every single time?', 'fun', 17),
            ('If you had a free year and unlimited money, what would you do?', 'future', 18),
            ('What is something most people get wrong about you?', 'random', 19),
            ('What subject did you hate in school that you now find interesting?', 'opinion', 20),
            ('What is the most useful thing you taught yourself?', 'values', 21),
            ('What does your morning routine say about you?', 'random', 22),
            ('What is a cause you care about deeply and why?', 'deep', 23),
            ('What three things are you grateful for today?', 'values', 24),
            ('What is something you are still figuring out about yourself?', 'deep', 25),
            ('If you could live anywhere in India for a year, where and why?', 'future', 26),
            ('What skill do you have that most people do not know about?', 'random', 27),
            ('What is the most interesting conversation you have had recently?', 'fun', 28),
            ('What does your ideal relationship look like?', 'values', 29),
        ]

        from django.utils.timezone import timedelta
        from datetime import date
        created = 0
        for text, category, offset in prompts:
            active_date = today + timedelta(days=offset)
            _, was_created = DailyPrompt.objects.get_or_create(
                active_date=active_date,
                defaults={'prompt_text': text, 'category': category}
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded {created} new daily prompts.'))
