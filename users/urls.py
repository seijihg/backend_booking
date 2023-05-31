from django.urls import path
from users.views import CustomRegisterView, CustomLoginView, UserDetails, UserListView

app_name = "users"


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
