from django.urls import path
from salon.views import SalonListCreateAPIView

app_name = "salon"


urlpatterns = [
    path("", SalonListCreateAPIView.as_view(), name="register"),
]
