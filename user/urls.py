from django.urls import path

from user.views import (
    CustomLoginView,
    CustomRegisterView,
    UserDetails,
    UserListView,
)

app_name = "user"


urlpatterns = [
    path("register/", CustomRegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("", UserListView.as_view(), name="user-list"),
    path(
        "<int:pk>/",
        UserDetails.as_view(),
        name="user-details",
    ),
]
