# website/middleware.py
from django.http import JsonResponse, HttpResponse
from django_ratelimit.exceptions import Ratelimited

class RateLimitMiddleware:
    """Custom middleware to handle rate limit exceptions"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Too many requests. Please try again later.'
                }, status=429)
            
            # Return HTML error page
            return HttpResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Too Many Requests</title>
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 50px;
                            background: #f5f5f5;
                        }
                        .error-box {
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            max-width: 500px;
                            margin: 0 auto;
                        }
                        h1 { color: #e74c3c; }
                        p { color: #555; line-height: 1.6; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h1>Too Many Requests</h1>
                        <p>You have exceeded the rate limit. Please wait a few minutes before trying again.</p>
                        <p><a href="/">Return to Home</a></p>
                    </div>
                </body>
                </html>
                """,
                status=429
            )
        return None