from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('onboarding/<int:step>/', views.onboarding_view, name='onboarding_step'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('deactivate/', views.deactivate_view, name='deactivate'),
]
