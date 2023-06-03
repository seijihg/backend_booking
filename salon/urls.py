from django.urls import path
from salon.views import SalonListCreateAPIView, SalonDetailUpdateDeleteView

app_name = "salon"


urlpatterns = [
    path("", SalonListCreateAPIView.as_view(), name="register"),
    path(
        "<int:pk>/",
        SalonDetailUpdateDeleteView.as_view(),
        name="salon_detail_update_delete",
    ),
]
