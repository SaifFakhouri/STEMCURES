# website/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache
from .models import ContactSubmission
import re
import logging

logger = logging.getLogger(__name__)

def home(request):
    """Render the main page"""
    return render(request, 'home.html')

def faculty(request):
    """Render the faculty page"""
    return render(request, 'faculty.html')

def faculty_profile(request, slug):
    """Render individual faculty profile pages"""
    profile_templates = {
        'saif': 'profile-saif.html',
    }
    
    template_name = profile_templates.get(slug)
    if not template_name:
        from django.http import Http404
        raise Http404("Faculty member not found")
    
    return render(request, template_name)

def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@require_http_methods(["GET", "POST"])
@csrf_protect
def contact_submit(request):
    """Handle contact form submission with manual rate limiting"""
    if request.method == 'POST':
        # Manual rate limiting - check BEFORE processing form
        client_ip = get_client_ip(request)
        cache_key = f'contact_ratelimit_{client_ip}'
        
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 3:
            # Rate limit exceeded
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Too many requests. Please try again in an hour.'
                }, status=429)
            
            return render(request, 'home.html', {
                'errors': {'general': 'Too many form submissions. Please try again in an hour.'}
            })
        
        # Increment attempts counter (expires in 1 hour)
        cache.set(cache_key, attempts + 1, 3600)
        
        # Collect form data
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'interest': request.POST.get('interest', '').strip(),
            'message': request.POST.get('message', '').strip()
        }
        
        # Initialize errors dictionary
        errors = {}
        
        # Validate name
        if not form_data['name']:
            errors['name'] = 'Please enter your full name'
        elif len(form_data['name']) < 2:
            errors['name'] = 'Name must be at least 2 characters'
        elif len(form_data['name']) > 100:
            errors['name'] = 'Name is too long (maximum 100 characters)'
            
        # Validate email with regex
        if not form_data['email']:
            errors['email'] = 'Please enter your email address'
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, form_data['email']):
                errors['email'] = 'Please enter a valid email address'
        
        # Validate interest
        if not form_data['interest']:
            errors['interest'] = 'Please select how you would like to help'
        elif form_data['interest'] not in ['volunteer', 'donate', 'partner', 'other']:
            errors['interest'] = 'Please select a valid option'
            
        # Validate message
        if not form_data['message']:
            errors['message'] = 'Please enter a message'
        elif len(form_data['message']) < 10:
            errors['message'] = 'Message must be at least 10 characters'
        elif len(form_data['message']) > 1000:
            errors['message'] = 'Message is too long (maximum 1000 characters)'
        
        # If there are errors
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            return render(request, 'home.html', {
                'errors': errors,
                'form_data': form_data
            })
        
        # If validation passes, save to database
        try:
            submission = ContactSubmission.objects.create(
                name=form_data['name'],
                email=form_data['email'],
                interest=form_data['interest'],
                message=form_data['message']
            )
            
            # Send email notification
            try:
                send_notification_email(submission)
            except Exception as e:
                logger.error(f"Email notification failed: {e}")
            
            # For AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your interest in STEM CURES! We will contact you soon.'
                })
            
            messages.success(request, 'Thank you for your interest in STEM CURES! We will contact you soon.')
            return redirect('home')
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {'general': 'An error occurred. Please try again.'}
                }, status=500)
            
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'home.html', {'form_data': form_data})
    
    return redirect('home')

# TEST ENDPOINT - REMOVE AFTER TESTING
@csrf_exempt
@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def test_ratelimit(request):
    """Test endpoint to verify rate limiting works - DELETE IN PRODUCTION"""
    if request.method == 'POST':
        client_ip = request.META.get('REMOTE_ADDR')
        return JsonResponse({
            'success': True,
            'message': f'Request from {client_ip} succeeded',
            'attempt': request.POST.get('attempt', '?')
        })
    return JsonResponse({'error': 'Use POST'}, status=400)

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