from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from .models import AuditLog
import time


class RateLimitMiddleware:
    """Rate limiting middleware for API endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)
        
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Rate limit rules
        rate_limits = {
            '/api/session/create/': {'limit': 5, 'window': 3600},  # 5 per hour
            '/api/rooms/create/': {'limit': 3, 'window': 3600},   # 3 per hour
            '/api/messages/send/': {'limit': 10, 'window': 60},   # 10 per minute
        }
        
        # Check rate limits
        for path, config in rate_limits.items():
            if request.path.startswith(path):
                cache_key = f"ratelimit:{ip_address}:{path}"
                count = cache.get(cache_key, 0)
                
                if count >= config['limit']:
                    # Log rate limit hit
                    AuditLog.objects.create(
                        event_type='rate_limit',
                        ip_address=ip_address,
                        details={'path': request.path, 'limit': config['limit'], 'window': config['window']}
                    )
                    return JsonResponse(
                        {'error': 'Rate limit exceeded. Please try again later.'},
                        status=429
                    )
                
                # Increment counter
                cache.set(cache_key, count + 1, config['window'])
                break
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware:
    """Add security headers to responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (adjust for your needs)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp
        
        return response
