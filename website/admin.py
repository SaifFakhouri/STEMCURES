# Install required package first:
# pip install django-ratelimit

# STEMCURES/settings.py - Add these settings
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
]

# Rate limiting configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Admin URL obfuscation (optional but recommended)
ADMIN_URL = 'secure-admin-panel-2024/'  # Change from 'admin/'

# ==============================================================
# website/views.py - Add rate limiting to views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django_ratelimit.decorators import ratelimit
from .forms import ContactForm
from .models import ContactSubmission
import logging

logger = logging.getLogger(__name__)

def index(request):
    """Render the main page"""
    return render(request, 'index.html')

@require_http_methods(["GET", "POST"])
@csrf_protect
@ratelimit(key='ip', rate='5/h', method='POST', block=True)  # 5 submissions per hour per IP
def contact_submit(request):
    """Handle contact form submission with rate limiting"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            try:
                submission = form.save()
                
                # Send email notification
                try:
                    send_notification_email(submission)
                except Exception as e:
                    logger.error(f"Email notification failed: {e}")
                
                success_msg = 'Thank you for your interest in STEM CURES! We will contact you soon.'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': success_msg})
                
                messages.success(request, success_msg)
                return redirect('index')
                
            except Exception as e:
                logger.error(f"Form submission error: {e}")
                error_msg = 'An error occurred. Please try again later.'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_msg}, status=500)
                
                messages.error(request, error_msg)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'index.html', {'form': form})

def send_notification_email(submission):
    """Send email notification when form is submitted"""
    subject = f'New Contact Form Submission from {submission.name[:100]}'
    message = f"""
    New contact form submission received:
    
    Name: {submission.name}
    Email: {submission.email}
    Interest: {submission.get_interest_display()}
    Message: {submission.message[:500]}
    
    Submitted at: {submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.CONTACT_EMAIL]
    
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

# ==============================================================
# website/admin.py - Secure admin with rate limiting
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.http import HttpResponse
from django.core.cache import cache
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import ContactSubmission

class RateLimitedLoginView(auth_views.LoginView):
    """Custom login view with rate limiting"""
    
    @method_decorator(ratelimit(key='ip', rate='5/15m', method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'interest', 'submitted_at', 'is_read']
    list_filter = ['interest', 'is_read', 'submitted_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'interest')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Metadata', {
            'fields': ('submitted_at', 'is_read'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} submission(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} submission(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

# ==============================================================
# STEMCURES/urls.py - Update URLs with obfuscated admin
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from website.admin import RateLimitedLoginView

# Obfuscate admin URL
admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    path(admin_url, admin.site.urls),
    path('', include('website.urls')),
    
    # Custom rate-limited admin login
    path(f'{admin_url}login/', RateLimitedLoginView.as_view(
        template_name='admin/login.html'
    ), name='admin_login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)