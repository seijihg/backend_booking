from django.urls import path

from salon.views import SalonDetailUpdateDeleteView, SalonListCreateAPIView

app_name = "salon"


urlpatterns = [
    path("", SalonListCreateAPIView.as_view(), name="salons"),
    path(
        "<int:pk>/",
        SalonDetailUpdateDeleteView.as_view(),
        name="salon_detail_update_delete",
    ),
]
