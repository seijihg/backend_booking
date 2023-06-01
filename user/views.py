from django.http import JsonResponse
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework.pagination import PageNumberPagination


from user.serializers import UserCreateSerializer, UserSerializer
from user.permissions import IsTokenOwner
from .models import ExtendedUser
from .helpers import generate_tokens


# Create your views here.
class CustomRegisterView(RegisterView):
    serializer_class = UserCreateSerializer

    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save(self.request)
            user_serializer = UserSerializer(user)
            tokens = generate_tokens(user)

            response_data = {
                "user": user_serializer.data,
                "access_token": tokens["access_token"],
            }

            response = JsonResponse(response_data, status=status.HTTP_201_CREATED)
            # Set refresh token as an HTTP-only cookie
            response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True)

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
            response.data["access_token"] = tokens["access_token"]
            response.set_cookie("refresh_token", tokens["refresh_token"], httponly=True)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    # permission_classes = [permissions.IsAdminUser]  # Field is_staff = True
    pagination_class = PageNumberPagination

    def get(self, request):
        users = ExtendedUser.objects.all()
        paginator = self.pagination_class()
        paginated_users = paginator.paginate_queryset(users, request)

        serializer = UserSerializer(paginated_users, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserDetails(APIView):
    permission_classes = [IsTokenOwner, permissions.IsAdminUser]

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
