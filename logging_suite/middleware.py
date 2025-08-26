# logging_suite/middleware.py
"""
Django middleware for logging_suite request context management
"""

import time
import uuid
from typing import Callable, Any
from .django_utils import set_current_request, clear_current_request, get_request_context
from .factory import LoggerFactory


class LoggingContextMiddleware:
    """
    Django middleware that manages request context for logging_suite

    This middleware:
    - Sets the current request in thread-local storage
    - Adds request ID for tracking
    - Logs request start/end with timing
    - Handles request context cleanup
    """

    def __init__(self, get_response: Callable = None):
        """
        Initialize the middleware

        Args:
            get_response: Django get_response callable
        """
        self.get_response = get_response
        self.logger = LoggerFactory.create_logger('django.middleware.logging')

        # Configuration
        self.log_requests = True
        self.log_responses = True
        self.log_slow_requests = True
        self.slow_request_threshold = 2.0  # seconds
        self.include_request_body = False  # For security reasons
        self.include_response_content = False  # For performance reasons

    def __call__(self, request):
        """
        Process request through the middleware

        Args:
            request: Django request object

        Returns:
            Django response object
        """
        # Add request ID for tracking
        if not hasattr(request, 'id'):
            request.id = str(uuid.uuid4())

        # Set request in thread-local storage
        set_current_request(request)

        # Record request start time
        start_time = time.time()

        # Log request start
        if self.log_requests:
            self._log_request_start(request)

        try:
            # Process request through Django
            response = self.get_response(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Log request completion
            if self.log_responses:
                self._log_request_end(request, response, processing_time)

            # Log slow requests
            if self.log_slow_requests and processing_time > self.slow_request_threshold:
                self._log_slow_request(request, response, processing_time)

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time

            # Log request failure
            self._log_request_error(request, e, processing_time)

            # Re-raise the exception
            raise

        finally:
            # Always clean up thread-local storage
            clear_current_request()

    def _log_request_start(self, request):
        """Log the start of request processing"""
        context = get_request_context(request)
        context.update({
            'action': 'request_start',
            'request_size_bytes': self._get_request_size(request),
        })

        if self.include_request_body and hasattr(request, 'body'):
            try:
                # Only log small request bodies and sanitize them
                body = request.body
                if len(body) < 1000:  # Only small bodies
                    context['request_body'] = body.decode('utf-8', errors='ignore')[:500]
            except Exception:
                pass

        self.logger.info(
            f"Request started: {request.method} {request.path}",
            **context
        )

    def _log_request_end(self, request, response, processing_time: float):
        """Log the successful completion of request processing"""
        context = get_request_context(request)
        context.update({
            'action': 'request_complete',
            'status_code': response.status_code,
            'processing_time_seconds': round(processing_time, 4),
            'processing_time_ms': round(processing_time * 1000, 2),
            'response_size_bytes': self._get_response_size(response),
            'success': True,
        })

        # Add response content for small responses (if enabled)
        if self.include_response_content and hasattr(response, 'content'):
            try:
                content = response.content
                if len(content) < 500:  # Only very small responses
                    context['response_content'] = content.decode('utf-8', errors='ignore')[:200]
            except Exception:
                pass

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = 'error'
        elif response.status_code >= 400:
            log_level = 'warning'
        elif processing_time > self.slow_request_threshold:
            log_level = 'warning'
        else:
            log_level = 'info'

        log_method = getattr(self.logger, log_level)
        log_method(
            f"Request completed: {request.method} {request.path} -> {response.status_code} ({processing_time:.3f}s)",
            **context
        )

    def _log_request_error(self, request, exception: Exception, processing_time: float):
        """Log request processing errors"""
        context = get_request_context(request)
        context.update({
            'action': 'request_error',
            'processing_time_seconds': round(processing_time, 4),
            'processing_time_ms': round(processing_time * 1000, 2),
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'success': False,
        })

        self.logger.error(
            f"Request failed: {request.method} {request.path} -> {type(exception).__name__} ({processing_time:.3f}s)",
            **context
        )

    def _log_slow_request(self, request, response, processing_time: float):
        """Log slow request performance warning"""
        context = get_request_context(request)
        context.update({
            'action': 'slow_request_warning',
            'status_code': response.status_code,
            'processing_time_seconds': round(processing_time, 4),
            'processing_time_ms': round(processing_time * 1000, 2),
            'threshold_seconds': self.slow_request_threshold,
            'performance_warning': True,
        })

        self.logger.warning(
            f"Slow request detected: {request.method} {request.path} took {processing_time:.3f}s (threshold: {self.slow_request_threshold}s)",
            **context
        )

    def _get_request_size(self, request) -> int:
        """Get the size of the request in bytes"""
        try:
            if hasattr(request, 'body'):
                return len(request.body)
            return 0
        except Exception:
            return 0

    def _get_response_size(self, response) -> int:
        """Get the size of the response in bytes"""
        try:
            if hasattr(response, 'content'):
                return len(response.content)
            return 0
        except Exception:
            return 0


class RequestTimingMiddleware:
    """
    Simpler middleware focused only on request timing

    Use this if you only want basic timing without full context management
    """

    def __init__(self, get_response: Callable = None):
        self.get_response = get_response
        self.logger = LoggerFactory.create_logger('django.request.timing')

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        processing_time = time.time() - start_time

        # Only log slow requests
        if processing_time > 1.0:
            self.logger.warning(
                f"Slow request: {request.method} {request.path}",
                processing_time_seconds=processing_time,
                status_code=response.status_code,
                path=request.path,
                method=request.method
            )

        return response


class LoggingConfigurationMiddleware:
    """
    Middleware to configure logging per request based on request properties

    This can be useful for enabling debug logging for specific users or requests
    """

    def __init__(self, get_response: Callable = None):
        self.get_response = get_response
        self.logger = LoggerFactory.create_logger('django.logging.config')

    def __call__(self, request):
        # Store original configuration
        original_config = None
        should_restore = False

        try:
            # Check if this request should have special logging
            if self._should_enable_debug_logging(request):
                # Temporarily enable debug logging
                from .config import configure_global_logging, get_global_config
                original_config = get_global_config()

                configure_global_logging(
                    level='DEBUG',
                    tracing_enabled=True,
                    pretty_json=True
                )
                should_restore = True

                self.logger.info(
                    "Enabled debug logging for request",
                    request_path=request.path,
                    user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None
                )

            # Process request
            response = self.get_response(request)

            return response

        finally:
            # Restore original configuration if needed
            if should_restore and original_config:
                from .config import configure_global_logging
                configure_global_logging(**original_config)

    def _should_enable_debug_logging(self, request) -> bool:
        """
        Determine if debug logging should be enabled for this request

        Args:
            request: Django request object

        Returns:
            True if debug logging should be enabled
        """
        # Enable debug logging for staff users
        if hasattr(request, 'user') and hasattr(request.user, 'is_staff'):
            if request.user.is_staff:
                return True

        # Enable debug logging if debug parameter is present
        if request.GET.get('debug_logging') == 'true':
            return True

        # Enable debug logging for specific paths
        debug_paths = ['/admin/', '/api/debug/']
        if any(request.path.startswith(path) for path in debug_paths):
            return True

        return False


# Django settings integration
def configure_django_middleware_settings():
    """
    Generate Django middleware settings for logging_suite

    Returns:
        Dictionary with recommended middleware configuration
    """
    return {
        'MIDDLEWARE': [
            # Add LoggingSuite middleware near the top
            'LoggingSuite.middleware.LoggingContextMiddleware',

            # Standard Django middleware
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',

            # Optional: Add timing middleware for performance monitoring
            # 'LoggingSuite.middleware.RequestTimingMiddleware',

            # Optional: Add configuration middleware for per-request logging control
            # 'LoggingSuite.middleware.LoggingConfigurationMiddleware',
        ]
    }


# Export middleware classes
__all__ = [
    'LoggingContextMiddleware',
    'RequestTimingMiddleware',
    'LoggingConfigurationMiddleware',
    'configure_django_middleware_settings'
]