from django.urls import path
from user.views import (
    CustomRegisterView,
    CustomLoginView,
    CustomerDetailView,
    UserDetails,
    UserListView,
    CustomerListCreateAPIView,
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
    path("customers/", CustomerListCreateAPIView.as_view(), name="customers"),
    path("customers/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
]
