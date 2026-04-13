from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json

from accounts.models import User
from .models import (DailyPrompt, PromptAnswer, ConversationStarter,
                     Connection, Message, Notification, Report, BlockedUser)





def profile_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.profile_complete:
            return redirect('onboarding_step', step=request.user.setup_step + 1)
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@profile_required
def discover_view(request):
    user = request.user
    region_filter = request.GET.get('region', '')

    # Exclude blocked, already connected, self
    blocked_ids = list(BlockedUser.objects.filter(blocker=user).values_list('blocked_id', flat=True))
    blocked_by_ids = list(BlockedUser.objects.filter(blocked=user).values_list('blocker_id', flat=True))
    connected_a = list(Connection.objects.filter(user_a=user).values_list('user_b_id', flat=True))
    connected_b = list(Connection.objects.filter(user_b=user).values_list('user_a_id', flat=True))
    starter_sent = list(ConversationStarter.objects.filter(from_user=user, status='pending').values_list('to_user_id', flat=True))

    exclude_ids = set([user.id] + blocked_ids + blocked_by_ids + connected_a + connected_b + starter_sent)

    profiles = User.objects.filter(
        profile_complete=True,
        is_active=True,
        is_banned=False,
    ).exclude(id__in=exclude_ids)

    if region_filter and region_filter != 'open':
        profiles = profiles.filter(region=region_filter)

    # Compute vibe scores and sort
    profiles_with_scores = []
    for p in profiles[:30]:
        score = user.compute_vibe_score(p)
        profiles_with_scores.append((p, score))

    profiles_with_scores.sort(key=lambda x: x[1]['total'], reverse=True)

    # Today's prompt
    today = timezone.localdate()
    try:
        today_prompt = DailyPrompt.objects.get(active_date=today)
        already_answered = PromptAnswer.objects.filter(user=user, prompt=today_prompt).exists()
    except DailyPrompt.DoesNotExist:
        today_prompt = None
        already_answered = False

    return render(request, 'core/discover.html', {
        'profiles': profiles_with_scores,
        'today_prompt': today_prompt,
        'already_answered': already_answered,
        'region_filter': region_filter,
        'region_choices': [('','All India'),('north','North'),('south','South'),('east','East'),('west','West'),('central','Central'),('northeast','Northeast')],
    })


@profile_required
@require_POST
def submit_prompt_answer(request):
    data = json.loads(request.body)
    prompt_id = data.get('prompt_id')
    answer_text = data.get('answer_text', '').strip()

    if not answer_text or len(answer_text) < 10:
        return JsonResponse({'error': 'Write at least a sentence'}, status=400)

    try:
        prompt = DailyPrompt.objects.get(id=prompt_id)
    except DailyPrompt.DoesNotExist:
        return JsonResponse({'error': 'Prompt not found'}, status=404)

    PromptAnswer.objects.update_or_create(
        user=request.user, prompt=prompt,
        defaults={'answer_text': answer_text}
    )
    return JsonResponse({'success': True})


@profile_required
@require_POST
def send_starter(request):
    data = json.loads(request.body)
    to_user_id = data.get('to_user_id')
    starter_text = data.get('starter_text', '').strip()

    if not starter_text or len(starter_text) < 10:
        return JsonResponse({'error': 'Write a meaningful starter'}, status=400)

    try:
        to_user = User.objects.get(id=to_user_id, profile_complete=True, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    if ConversationStarter.objects.filter(from_user=request.user, to_user=to_user).exists():
        return JsonResponse({'error': 'You already sent them a starter!'}, status=400)

    ConversationStarter.objects.create(
        from_user=request.user, to_user=to_user, starter_text=starter_text
    )
    Notification.objects.create(
        user=to_user, notif_type='new_starter',
        title=f'{request.user.full_name} sent you a conversation starter!',
        body=starter_text[:80],
    )
    return JsonResponse({'success': True})


@profile_required
def chat_list_view(request):
    user = request.user
    connections = Connection.objects.filter(
        user_a=user, status__in=['chatting','vibe_check','matched','friends']
    ).select_related('user_b') | Connection.objects.filter(
        user_b=user, status__in=['chatting','vibe_check','matched','friends']
    ).select_related('user_a')
    connections = connections.order_by('-last_message_at', '-created_at')

    # Pending starters received
    starters = ConversationStarter.objects.filter(
        to_user=user, status='pending'
    ).select_related('from_user').order_by('-created_at')

    # Unread message counts
    conn_data = []
    for conn in connections:
        other = conn.get_other_user(user)
        unread = conn.messages.filter(is_read=False, is_deleted=False).exclude(sender=user).count()
        conn_data.append({'conn': conn, 'other': other, 'unread': unread})

    return render(request, 'core/chat_list.html', {
        'conn_data': conn_data, 'starters': starters
    })


@profile_required
@require_POST
def accept_starter(request, starter_id):
    starter = get_object_or_404(ConversationStarter, id=starter_id, to_user=request.user, status='pending')
    starter.status = 'accepted'
    starter.save()

    # Create connection (user_a is always the one with lower id for consistency)
    user_a, user_b = sorted([starter.from_user, request.user], key=lambda u: u.id)
    conn, created = Connection.objects.get_or_create(
        user_a=user_a, user_b=user_b,
        defaults={
            'status': 'chatting',
            'initiated_by': starter.from_user,
            'vibe_check_due': timezone.now() + timedelta(days=7),
        }
    )
    # Notify the sender
    Notification.objects.create(
        user=starter.from_user, notif_type='new_starter',
        title=f'{request.user.full_name} accepted your starter!',
        body='Start the conversation now.',
        connection=conn,
    )
    return redirect('chat', connection_id=conn.id)


@profile_required
@require_POST
def decline_starter(request, starter_id):
    starter = get_object_or_404(ConversationStarter, id=starter_id, to_user=request.user)
    starter.status = 'declined'
    starter.save()
    return redirect('chat_list')


@profile_required
def chat_view(request, connection_id):
    user = request.user
    conn = get_object_or_404(Connection, id=connection_id)

    if conn.user_a != user and conn.user_b != user:
        return redirect('chat_list')

    other = conn.get_other_user(user)

    # Mark messages as read
    conn.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    # Check if vibe check is due
    show_vibe_check = (
        (conn.is_vibe_check_due() or conn.status == 'vibe_check') and
        not conn.vibe_check_resolved and
        not conn.get_my_vibe_response(user)
    )

    my_response = conn.get_my_vibe_response(user)

    messages_qs = conn.messages.filter(is_deleted=False).select_related('sender')

    return render(request, 'core/chat.html', {
        'conn': conn, 'other': other,
        'messages': messages_qs,
        'show_vibe_check': show_vibe_check,
        'my_vibe_response': my_response,
        'photos_revealed': conn.photos_revealed,
    })


@profile_required
@require_POST
def submit_vibe_check(request, connection_id):
    conn = get_object_or_404(Connection, id=connection_id)
    if conn.user_a != request.user and conn.user_b != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    data = json.loads(request.body)
    response = data.get('response')
    if response not in ['explore_more', 'stay_friends', 'end']:
        return JsonResponse({'error': 'Invalid response'}, status=400)

    if conn.user_a == request.user:
        conn.user_a_vibe_response = response
    else:
        conn.user_b_vibe_response = response

    conn.status = 'vibe_check'
    conn.save()

    if conn.user_a_vibe_response and conn.user_b_vibe_response:
        conn.resolve_vibe_check()
        other = conn.get_other_user(request.user)
        if conn.status == 'matched':
            Notification.objects.create(user=other, notif_type='match', title="It's a match! 💕", body=f"You and {request.user.full_name} both want to explore more.", connection=conn)
            Notification.objects.create(user=request.user, notif_type='match', title="It's a match! 💕", body=f"You and {other.full_name} both want to explore more.", connection=conn)

    return JsonResponse({'success': True, 'status': conn.status})


@profile_required
@require_POST
def request_reveal(request, connection_id):
    conn = get_object_or_404(Connection, id=connection_id)
    if conn.user_a != request.user and conn.user_b != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if conn.user_a == request.user:
        conn.user_a_reveal_requested = True
    else:
        conn.user_b_reveal_requested = True

    if conn.user_a_reveal_requested and conn.user_b_reveal_requested:
        conn.photos_revealed = True
        other = conn.get_other_user(request.user)
        Notification.objects.create(user=other, notif_type='reveal_accepted', title='Photos revealed! 📸', body='Both of you agreed to reveal photos.', connection=conn)

    conn.save()
    return JsonResponse({'success': True, 'revealed': conn.photos_revealed})


@profile_required
@require_POST
def report_user(request):
    data = json.loads(request.body)
    reported_id = data.get('reported_id')
    reason = data.get('reason')
    details = data.get('details', '')
    connection_id = data.get('connection_id')

    try:
        reported = User.objects.get(id=reported_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    conn = None
    if connection_id:
        try:
            conn = Connection.objects.get(id=connection_id)
        except Connection.DoesNotExist:
            pass

    Report.objects.create(reporter=request.user, reported=reported, reason=reason, details=details, connection=conn)
    return JsonResponse({'success': True})


@profile_required
@require_POST
def block_user(request):
    data = json.loads(request.body)
    blocked_id = data.get('blocked_id')
    try:
        blocked = User.objects.get(id=blocked_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    BlockedUser.objects.get_or_create(blocker=request.user, blocked=blocked)
    # End any connection
    Connection.objects.filter(user_a=request.user, user_b=blocked).update(status='blocked')
    Connection.objects.filter(user_a=blocked, user_b=request.user).update(status='blocked')
    return JsonResponse({'success': True})


@profile_required
def profile_view(request):
    u = request.user
    personality_items = [
        ('Love language', u.get_love_language_display() if u.love_language else None),
        ('Humor', u.get_humor_style_display() if u.humor_style else None),
        ('Looking for', u.get_relationship_goal_display() if u.relationship_goal else None),
        ('Comms style', u.get_communication_style_display() if u.communication_style else None),
    ]
    return render(request, 'core/profile.html', {
        'profile_user': u,
        'personality_items': personality_items,
    })


@profile_required
def notifications_view(request):
    notifs = request.user.notifications.all()[:30]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifs})


@profile_required
def settings_view(request):
    u = request.user
    account_items = [
        ('Email', u.email),
        ('Name', u.full_name),
        ('College', u.college_name),
        ('Joined', u.date_joined.strftime('%B %Y')),
    ]
    return render(request, 'core/settings.html', {'account_items': account_items})


@profile_required
def unread_count(request):
    unread_notifs = request.user.notifications.filter(is_read=False).count()
    unread_messages = Message.objects.filter(
        connection__in=Connection.objects.filter(user_a=request.user) | Connection.objects.filter(user_b=request.user),
        is_read=False,
        is_deleted=False,
    ).exclude(sender=request.user).count()
    return JsonResponse({'notifications': unread_notifs, 'messages': unread_messages})


# Fix landing view to pass steps context
def landing_view(request):
    if request.user.is_authenticated and request.user.profile_complete:
        return redirect('discover')
    steps = [
        (1, 'Build your personality profile', 'Add interests, values, love language. No appearance fields.'),
        (2, 'Get verified with college email', 'Only genuine Indian college students aged 18+ can join.'),
        (3, 'Browse by vibe, not face', 'Discover people by interests, stream, region, and vibe score.'),
        (4, 'Send a conversation starter', 'Pick from smart suggestions or write your own.'),
        (5, 'Chat for 7 days', 'Talk, share daily prompts, really get to know each other.'),
        (6, 'The 7-day vibe check', 'Both decide — explore more, stay friends, or part ways gracefully.'),
    ]
    return render(request, 'core/landing.html', {'steps': steps})
