"""
URL configuration for STEMCURES project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# STEMCURES/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import never_cache
from django_ratelimit.decorators import ratelimit

# Get the secure admin URL from settings
admin_url = getattr(settings, 'ADMIN_URL', 'adminstemcures/')

# Rate-limited login view
rate_limited_login = ratelimit(
    key='ip', 
    rate='5/15m', 
    method='POST', 
    block=True
)(never_cache(auth_views.LoginView.as_view()))

urlpatterns = [
    # Secure admin URL with rate-limited login
    path(admin_url, admin.site.urls),
    path(f'{admin_url}login/', rate_limited_login, name='admin_login'),
    
    # Main website URLs
    path('', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)