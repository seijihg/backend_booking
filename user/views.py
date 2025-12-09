from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from django.conf import settings
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from user.serializers import UserCreateSerializer, UserSerializer

from .helpers import generate_tokens
from .models import ExtendedUser


# Create your views here.
class CustomRegisterView(RegisterView):
    serializer_class = UserCreateSerializer

    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save(request=self.request)
            user_serializer = UserSerializer(user)
            tokens = generate_tokens(user)

            response_data = {
                "user": user_serializer.data,
                "access_token": tokens["access_token"],
            }

            response = Response(response_data, status=status.HTTP_201_CREATED)

            # ✅ Set access token cookie (named "token" to match frontend)
            response.set_cookie(
                "token",
                tokens["access_token"],
                httponly=True,
                secure=True,
                samesite="None",  # Required for cross-origin (different subdomains)
                domain=settings.COOKIE_DOMAIN,
                max_age=3600,
            )

            # ✅ Set refresh token cookie
            response.set_cookie(
                "refresh_token",
                tokens["refresh_token"],
                httponly=True,
                secure=True,
                samesite="None",  # Required for cross-origin (different subdomains)
                domain=settings.COOKIE_DOMAIN,
                max_age=604800,
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(LoginView):
    def get_response(self):
        response = super().get_response()
        if response.status_code == status.HTTP_200_OK:
            # Exclude tokens from the response data
            response.data.pop("access_token", None)
            response.data.pop("refresh_token", None)
        return response

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = generate_tokens(user)
            response = super().post(request, *args, **kwargs)

            user_serializer = UserSerializer(user)
            response.data["user"] = user_serializer.data

            # ✅ Set access token cookie (named "token" to match frontend)
            response.set_cookie(
                "token",
                tokens["access_token"],
                httponly=True,
                secure=True,
                samesite="None",  # Required for cross-origin (different subdomains)
                domain=settings.COOKIE_DOMAIN,
                max_age=3600,
            )

            # ✅ Set refresh token cookie
            response.set_cookie(
                "refresh_token",
                tokens["refresh_token"],
                httponly=True,
                secure=True,
                samesite="None",  # Required for cross-origin (different subdomains)
                domain=settings.COOKIE_DOMAIN,
                max_age=604800,
            )

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(ListAPIView):
    # permission_classes = [permissions.IsAdminUser]  # Field is_staff = True
    def get(self, request):
        salon_id = request.query_params.get("salon")
        users = ExtendedUser.objects.filter(salons=salon_id)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserDetails(APIView):
    # permission_classes = [IsTokenOwnerOrAdmin]

    def get(self, request, pk):
        try:
            user = ExtendedUser.objects.get(pk=pk)
        except ExtendedUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(user)

        return Response(data={"user": serializer.data})

    def patch(self, request, pk):
        try:
            user = ExtendedUser.objects.get(pk=pk)
        except ExtendedUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(
            user, data=request.data, partial=True
        )  # set partial=True to update a data partially

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
