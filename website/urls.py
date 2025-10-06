from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact_submit, name='contact_submit'),
    path('faculty/', views.faculty, name='faculty'),
    path('faculty/<slug:slug>/', views.faculty_profile, name='faculty_profile'),
    path('test-ratelimit/', views.test_ratelimit, name='test_ratelimit'),  # REMOVE IN PRODUCTION
]