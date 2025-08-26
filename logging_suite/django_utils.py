# logging_suite/django_utils.py
"""
Django-specific utilities for logging_suite
"""

import threading
from typing import Any, Optional, Dict
from contextlib import contextmanager

# Thread-local storage for request context
_local = threading.local()


def get_current_request():
    """
    Get the current Django request from thread-local storage

    Returns:
        Django request object or None if not available
    """
    return getattr(_local, 'current_request', None)


def set_current_request(request):
    """
    Set the current Django request in thread-local storage

    Args:
        request: Django request object
    """
    _local.current_request = request


def clear_current_request():
    """Clear the current Django request from thread-local storage"""
    if hasattr(_local, 'current_request'):
        delattr(_local, 'current_request')


def get_request_context(request=None) -> Dict[str, Any]:
    """
    Extract logging context from Django request

    Args:
        request: Django request object (uses current request if None)

    Returns:
        Dictionary with request context for logging
    """
    if request is None:
        request = get_current_request()

    if request is None:
        return {}

    context = {
        'request_method': request.method,
        'request_path': request.path,
        'request_id': getattr(request, 'id', None) or id(request),
    }

    # Add user information if available
    if hasattr(request, 'user') and request.user:
        if hasattr(request.user, 'is_authenticated'):
            if request.user.is_authenticated:
                context['user_id'] = getattr(request.user, 'id', None)
                context['username'] = getattr(request.user, 'username', None)
                context['user_authenticated'] = True
            else:
                context['user_authenticated'] = False
        else:
            # Fallback for older Django versions
            context['user_id'] = getattr(request.user, 'id', None)
            context['username'] = getattr(request.user, 'username', None)

    # Add session information if available
    if hasattr(request, 'session') and request.session:
        context['session_key'] = request.session.session_key

    # Add remote address
    context['remote_addr'] = get_client_ip(request)

    # Add user agent
    context['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:200]  # Truncate

    # Add referer
    referer = request.META.get('HTTP_REFERER')
    if referer:
        context['referer'] = referer[:200]  # Truncate

    return context


def get_client_ip(request) -> str:
    """
    Get the client IP address from Django request

    Args:
        request: Django request object

    Returns:
        Client IP address string
    """
    # Check for forwarded headers first (for reverse proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
        return ip

    # Check other common headers
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip

    # Fall back to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', 'unknown')


@contextmanager
def django_request_context(request):
    """
    Context manager to temporarily set Django request context

    Args:
        request: Django request object

    Example:
        with django_request_context(request):
            logger.info("Processing request")  # Will include request context
    """
    previous_request = get_current_request()
    set_current_request(request)
    try:
        yield request
    finally:
        if previous_request is not None:
            set_current_request(previous_request)
        else:
            clear_current_request()


def create_django_logger_context(request=None, **additional_context) -> Dict[str, Any]:
    """
    Create a comprehensive logging context for Django applications

    Args:
        request: Django request object (uses current request if None)
        **additional_context: Additional context to include

    Returns:
        Dictionary with comprehensive Django logging context
    """
    context = {}

    # Add request context
    request_context = get_request_context(request)
    context.update(request_context)

    # Add Django-specific context
    try:
        from django.conf import settings
        context['django_debug'] = getattr(settings, 'DEBUG', False)
        context['django_environment'] = getattr(settings, 'ENVIRONMENT', 'unknown')
    except ImportError:
        pass

    # Add additional context
    context.update(additional_context)

    return context


def get_django_app_context() -> Dict[str, Any]:
    """
    Get context information about the Django application

    Returns:
        Dictionary with Django app context
    """
    context = {}

    try:
        from django.conf import settings

        # Basic Django info
        context['django_debug'] = getattr(settings, 'DEBUG', False)
        context['django_secret_key_set'] = bool(getattr(settings, 'SECRET_KEY', None))

        # Database info (without sensitive details)
        databases = getattr(settings, 'DATABASES', {})
        if databases:
            default_db = databases.get('default', {})
            context['database_engine'] = default_db.get('ENGINE', 'unknown')
            context['database_name'] = default_db.get('NAME', 'unknown')

        # Installed apps (count only for privacy)
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        context['installed_apps_count'] = len(installed_apps)

        # Custom apps (non-Django apps)
        custom_apps = [app for app in installed_apps if not app.startswith('django.')]
        context['custom_apps_count'] = len(custom_apps)

        # Environment indicator
        context['environment'] = getattr(settings, 'ENVIRONMENT', 'unknown')

    except ImportError:
        context['django_available'] = False

    return context


class DjangoLoggingContextProcessor:
    """
    Processor to automatically add Django context to log entries
    """

    def __init__(self, include_request: bool = True, include_user: bool = True):
        """
        Initialize Django context processor

        Args:
            include_request: Whether to include request information
            include_user: Whether to include user information
        """
        self.include_request = include_request
        self.include_user = include_user

    def process_log_entry(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process log entry to add Django context

        Args:
            log_data: Original log data

        Returns:
            Log data with Django context added
        """
        processed = log_data.copy()

        # Get current request
        request = get_current_request()
        if request is None:
            return processed

        # Add request context
        if self.include_request:
            django_context = get_request_context(request)

            # Filter out user info if not wanted
            if not self.include_user:
                django_context = {k: v for k, v in django_context.items()
                                  if not k.startswith('user_')}

            # Add to log data
            existing_context = processed.get('context', {})
            existing_context.update(django_context)
            processed['context'] = existing_context

        return processed


def setup_django_logging_integration():
    """
    Set up Django logging integration with logging_suite

    This function configures logging_suite to work optimally with Django
    """
    try:
        from django.conf import settings
        from . import configure_for_django

        # Configure logging_suite for Django
        configure_for_django()

        # Add Django-specific processor if processors are available
        try:
            from .processors import DefaultProcessors
            from .factory import LoggerFactory

            # Create a Django-aware processor
            processor = DefaultProcessors.create_production_processor()
            django_processor = DjangoLoggingContextProcessor()

            # This would need to be integrated into the processor pipeline
            # Implementation depends on how processors are structured

        except ImportError:
            pass  # Processors not available

        print("✓ Django logging integration configured")

    except ImportError:
        print("⚠ Django not available - skipping Django integration")


def get_model_logging_context(instance) -> Dict[str, Any]:
    """
    Get logging context for a Django model instance

    Args:
        instance: Django model instance

    Returns:
        Dictionary with model context for logging
    """
    context = {}

    if not hasattr(instance, '_meta'):
        return context

    meta = instance._meta

    context.update({
        'app_label': meta.app_label,
        'model_name': meta.model_name,
        'model_verbose_name': str(meta.verbose_name),
    })

    # Add primary key if available
    if hasattr(instance, 'pk') and instance.pk:
        context['instance_pk'] = str(instance.pk)

    # Add string representation (truncated)
    try:
        context['instance_str'] = str(instance)[:100]
    except Exception:
        context['instance_str'] = f"<{meta.model_name}>"

    return context


# Export all Django utilities
__all__ = [
    'get_current_request',
    'set_current_request',
    'clear_current_request',
    'get_request_context',
    'get_client_ip',
    'django_request_context',
    'create_django_logger_context',
    'get_django_app_context',
    'DjangoLoggingContextProcessor',
    'setup_django_logging_integration',
    'get_model_logging_context'
]