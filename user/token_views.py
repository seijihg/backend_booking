"""
Custom token views that handle cookie-based authentication.
"""

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .cookie_config import get_cookie_settings, set_auth_cookies


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that handles both cookie-based and
    header-based refresh tokens.
    """

    def post(self, request, *args, **kwargs):
        # First try to get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token')

        # If not in cookie, try from request data (for backward compatibility)
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"detail": "No refresh token provided"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Create a refresh token instance
            refresh = RefreshToken(refresh_token)

            # Generate new access token
            access_token = refresh.access_token

            response_data = {
                "access": str(access_token),
                "refresh": str(refresh),
            }

            response = JsonResponse(response_data, status=status.HTTP_200_OK)

            # Set new cookies with environment-appropriate settings
            set_auth_cookies(response, str(access_token), str(refresh))

            return response

        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    Logout view that clears authentication cookies.
    """

    def post(self, request, *args, **kwargs):
        response = JsonResponse(
            {"detail": "Successfully logged out"}, status=status.HTTP_200_OK
        )

        # Get cookie settings for the current environment
        cookie_settings = get_cookie_settings()

        # Clear cookies by setting them with max_age=0
        response.set_cookie(
            key='token',
            value='',
            max_age=0,
            httponly=cookie_settings['httponly'],
            secure=cookie_settings['secure'],
            samesite=cookie_settings['samesite'],
            domain=cookie_settings['domain'],
        )

        response.set_cookie(
            key='refresh_token',
            value='',
            max_age=0,
            httponly=cookie_settings['httponly'],
            secure=cookie_settings['secure'],
            samesite=cookie_settings['samesite'],
            domain=cookie_settings['domain'],
        )

        return response
