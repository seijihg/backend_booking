"""booking_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


def health_check(request):
    """Simple health check endpoint for AWS ALB/ECS"""
    return JsonResponse({"status": "healthy"}, status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("users/", include("user.urls")),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("salons/", include("salon.urls")),
    path("appointments/", include("appointment.urls")),
    path("customers/", include("customer.urls")),
]
