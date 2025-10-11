"""
Cookie configuration helper for environment-specific settings.
"""

from django.conf import settings


def get_cookie_settings():
    """
    Returns environment-specific cookie settings.

    For development/localhost:
    - secure=False (allows HTTP)
    - domain=None (uses current domain)
    - samesite='Lax' (works without HTTPS)

    For production:
    - secure=True (HTTPS only)
    - domain='.lichnails.co.uk' (share across subdomains)
    - samesite='None' (cross-origin support)
    """
    # Primary check: Are we in development mode?
    is_development = settings.DEBUG or settings.DEVELOPMENT_MODE

    # Secondary check: Is this explicitly a production domain?
    # This ensures that even if localhost is in ALLOWED_HOSTS for some reason,
    # we still use production settings when the domain is production
    is_production_domain = any(
        'lichnails.co.uk' in host for host in settings.ALLOWED_HOSTS
    )

    if is_development and not is_production_domain:
        # Development/localhost settings
        return {
            'httponly': True,
            'secure': False,  # Allow HTTP in development
            'samesite': 'Lax',  # Works without HTTPS
            'domain': None,  # Use current domain (localhost)
        }
    else:
        # Production settings
        return {
            'httponly': True,
            'secure': True,  # HTTPS only in production
            'samesite': 'None',  # Required for cross-origin
            'domain': '.lichnails.co.uk',  # Share across subdomains
        }


def set_auth_cookies(response, access_token, refresh_token):
    """
    Sets authentication cookies with environment-appropriate settings.

    Args:
        response: Django HTTP response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    cookie_settings = get_cookie_settings()

    # Set access token cookie (named "token" to match frontend)
    response.set_cookie(
        key='token', value=access_token, max_age=3600, **cookie_settings  # 1 hour
    )

    # Set refresh token cookie
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=604800,  # 7 days
        **cookie_settings,
    )

    return response
