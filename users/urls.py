from django.urls import path
from users.views import CustomRegisterView, CustomLoginView, UserDetail

app_name = "users"


urlpatterns = [
    path("register/", CustomRegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path(
        "<int:pk>/",
        UserDetail.as_view(),
        name="user-detail-api",
    ),
]
