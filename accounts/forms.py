from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, INTEREST_CHOICES, AVATAR_COLORS

STATES = [
    ('','Select state'),
    ('Andhra Pradesh','Andhra Pradesh'), ('Assam','Assam'), ('Bihar','Bihar'),
    ('Chhattisgarh','Chhattisgarh'), ('Delhi','Delhi'), ('Goa','Goa'),
    ('Gujarat','Gujarat'), ('Haryana','Haryana'), ('Himachal Pradesh','Himachal Pradesh'),
    ('Jharkhand','Jharkhand'), ('Karnataka','Karnataka'), ('Kerala','Kerala'),
    ('Madhya Pradesh','Madhya Pradesh'), ('Maharashtra','Maharashtra'),
    ('Manipur','Manipur'), ('Meghalaya','Meghalaya'), ('Mizoram','Mizoram'),
    ('Nagaland','Nagaland'), ('Odisha','Odisha'), ('Punjab','Punjab'),
    ('Rajasthan','Rajasthan'), ('Sikkim','Sikkim'), ('Tamil Nadu','Tamil Nadu'),
    ('Telangana','Telangana'), ('Tripura','Tripura'), ('Uttar Pradesh','Uttar Pradesh'),
    ('Uttarakhand','Uttarakhand'), ('West Bengal','West Bengal'), ('Other','Other'),
]

class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Min. 8 characters'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['full_name', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        if p1 and len(p1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        user.avatar_initials = user.get_initials()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class Step1BasicForm(forms.ModelForm):
    COLOR_CHOICES = [(c, c) for c in AVATAR_COLORS]
    avatar_color = forms.ChoiceField(choices=COLOR_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['full_name', 'age', 'gender', 'pronouns', 'avatar_color']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'age': forms.NumberInput(attrs={'min': 18, 'max': 35, 'placeholder': 'Your age'}),
            'pronouns': forms.TextInput(attrs={'placeholder': 'e.g. she/her, he/him'}),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 18:
            raise forms.ValidationError('You must be 18 or older to use VibeMatch.')
        return age


class Step2AcademicForm(forms.ModelForm):
    GRAD_YEARS = [('', 'Select year')] + [(y, y) for y in range(2025, 2032)]

    class Meta:
        model = User
        fields = ['college_name', 'stream', 'year_of_study', 'graduation_year', 'city', 'state', 'region']
        widgets = {
            'college_name': forms.TextInput(attrs={'placeholder': 'e.g. IIT Delhi, BITS Pilani, LPU'}),
            'city': forms.TextInput(attrs={'placeholder': 'Your city'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['state'] = forms.ChoiceField(choices=STATES)
        self.fields['graduation_year'] = forms.ChoiceField(
            choices=self.GRAD_YEARS, required=False
        )


class Step3PersonalityForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['love_language', 'humor_style', 'communication_style', 'relationship_goal', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'A few sentences about yourself...', 'rows': 3, 'maxlength': 300}),
        }


class Step4InterestsForm(forms.Form):
    interests = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def clean_interests(self):
        interests = self.cleaned_data.get('interests', [])
        if len(interests) < 3:
            raise forms.ValidationError('Please select at least 3 interests.')
        if len(interests) > 8:
            raise forms.ValidationError('Please select at most 8 interests.')
        return interests


class Step5PreferencesForm(forms.ModelForm):
    preferred_gender_choices = forms.MultipleChoiceField(
        choices=[('male','Men'), ('female','Women'), ('non-binary','Non-binary'), ('all','Anyone')],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='I am interested in'
    )

    class Meta:
        model = User
        fields = ['preferred_region', 'age_min', 'age_max', 'long_distance_ready']
        widgets = {
            'age_min': forms.NumberInput(attrs={'min': 18, 'max': 35}),
            'age_max': forms.NumberInput(attrs={'min': 18, 'max': 35}),
        }


class Step6IcebreakerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['icebreaker']
        widgets = {
            'icebreaker': forms.Textarea(attrs={
                'placeholder': 'Something fun, honest, or a little weird about you...',
                'rows': 3, 'maxlength': 200
            }),
        }

    def clean_icebreaker(self):
        icebreaker = self.cleaned_data.get('icebreaker', '')
        if len(icebreaker.strip()) < 20:
            raise forms.ValidationError('Write at least 20 characters.')
        return icebreaker


class EditProfileForm(forms.ModelForm):
    interests_list = forms.MultipleChoiceField(
        choices=INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Interests'
    )

    class Meta:
        model = User
        fields = ['bio', 'icebreaker', 'love_language', 'humor_style',
                  'communication_style', 'relationship_goal', 'long_distance_ready', 'photo']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'maxlength': 300}),
            'icebreaker': forms.Textarea(attrs={'rows': 3, 'maxlength': 200}),
        }
