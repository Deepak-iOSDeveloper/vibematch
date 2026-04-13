from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import SignUpForm, LoginForm, Step1BasicForm, Step2AcademicForm, Step3PersonalityForm, Step4InterestsForm, Step5PreferencesForm, Step6IcebreakerForm, EditProfileForm
from .models import User

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('discover')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created! Let\'s build your profile.')
            return redirect('onboarding_step', step=1)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SignUpForm()
    return render(request, 'accounts/auth.html', {'form': form, 'mode': 'signup'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('discover')
    if request.method == 'POST':
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '')
            if not user.profile_complete:
                return redirect('onboarding_step', step=user.setup_step + 1)
            return redirect(next_url or 'discover')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/auth.html', {'mode': 'login'})


def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def onboarding_view(request, step):
    user = request.user
    step = int(step)

    if step == 1:
        form_class = Step1BasicForm
    elif step == 2:
        form_class = Step2AcademicForm
    elif step == 3:
        form_class = Step3PersonalityForm
    elif step == 4:
        form_class = Step4InterestsForm
    elif step == 5:
        form_class = Step5PreferencesForm
    elif step == 6:
        form_class = Step6IcebreakerForm
    else:
        return redirect('discover')

    if request.method == 'POST':
        if step == 4:
            form = Step4InterestsForm(request.POST)
            if form.is_valid():
                user.set_interests_list(form.cleaned_data['interests'])
                user.setup_step = step
                user.save()
                return redirect('onboarding_step', step=step + 1)
        elif step == 5:
            form = Step5PreferencesForm(request.POST, instance=user)
            if form.is_valid():
                u = form.save(commit=False)
                genders = request.POST.getlist('preferred_gender_choices')
                u.preferred_gender = ','.join(genders)
                u.setup_step = step
                u.save()
                return redirect('onboarding_step', step=step + 1)
        elif step == 6:
            form = Step6IcebreakerForm(request.POST, instance=user)
            if form.is_valid():
                u = form.save(commit=False)
                u.avatar_initials = u.get_initials()
                u.setup_step = 6
                u.profile_complete = True
                u.save()
                messages.success(request, 'Profile created! Welcome to VibeMatch 🎉')
                return redirect('discover')
        else:
            form = form_class(request.POST, instance=user)
            if form.is_valid():
                u = form.save(commit=False)
                u.setup_step = step
                u.avatar_initials = u.get_initials()
                u.save()
                return redirect('onboarding_step', step=step + 1)

        # form invalid — fall through to render with errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
    else:
        if step == 4:
            initial = {'interests': user.get_interests_list()}
            form = Step4InterestsForm(initial=initial)
        elif step == 5:
            initial = {'preferred_gender_choices': user.get_preferred_gender_list()}
            form = Step5PreferencesForm(instance=user, initial=initial)
        else:
            form = form_class(instance=user)

    from .models import AVATAR_COLORS
    STEP_NAMES = {1:'Basics', 2:'Academic', 3:'Personality', 4:'Interests', 5:'Preferences', 6:'Icebreaker'}
    STATES = [('','Select state'),('Andhra Pradesh','Andhra Pradesh'),('Assam','Assam'),('Bihar','Bihar'),('Chhattisgarh','Chhattisgarh'),('Delhi','Delhi'),('Goa','Goa'),('Gujarat','Gujarat'),('Haryana','Haryana'),('Himachal Pradesh','Himachal Pradesh'),('Jharkhand','Jharkhand'),('Karnataka','Karnataka'),('Kerala','Kerala'),('Madhya Pradesh','Madhya Pradesh'),('Maharashtra','Maharashtra'),('Manipur','Manipur'),('Meghalaya','Meghalaya'),('Odisha','Odisha'),('Punjab','Punjab'),('Rajasthan','Rajasthan'),('Tamil Nadu','Tamil Nadu'),('Telangana','Telangana'),('Uttar Pradesh','Uttar Pradesh'),('Uttarakhand','Uttarakhand'),('West Bengal','West Bengal'),('Other','Other')]
    ICEBREAKERS = [
        "I once tried to build an app in 48 hours and spent 47 of them debugging one line.",
        "If you can name 3 obscure facts about something random, we are going to get along great.",
        "Currently in a situationship with coffee — it gives me anxiety but I cannot quit.",
        "Ask me about the one time I accidentally emailed my professor instead of my friend.",
    ]
    return render(request, 'accounts/onboarding.html', {
        'form': form, 'step': step, 'step_name': STEP_NAMES.get(step, ''),
        'total_steps': 6, 'steps': range(1, 7),
        'avatar_colors': AVATAR_COLORS,
        'states': STATES,
        'grad_years': range(2025, 2032),
        'selected_interests': user.get_interests_list(),
        'selected_pref_genders': user.get_preferred_gender_list(),
        'pref_gender_choices': [('male','Men'),('female','Women'),('non-binary','Non-binary'),('all','Anyone')],
        'region_choices': [('open', 'All India'), ('north', 'North India'), ('south', 'South India'),
                           ('east', 'East India'), ('west', 'West India'), ('central', 'Central India'),
                           ('northeast', 'Northeast India')],
        'icebreaker_examples': ICEBREAKERS,
    })


@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            u = form.save(commit=False)
            interests = request.POST.getlist('interests_list')
            if interests:
                u.set_interests_list(interests)
            u.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = EditProfileForm(instance=user, initial={'interests_list': user.get_interests_list()})
    return render(request, 'accounts/edit_profile.html', {'form': form, 'user': user})

@login_required
def deactivate_view(request):
    request.user.is_active = False
    request.user.save()
    logout(request)
    return redirect('landing')
