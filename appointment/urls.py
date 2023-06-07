from django.urls import path
from appointment.views import (
    AppointmentListCreateAPIView,
    AppointmentDetailUpdateDeleteView,
)

app_name = "appointment"


urlpatterns = [
    path("", AppointmentListCreateAPIView.as_view(), name="appointments"),
    path(
        "<int:pk>/",
        AppointmentDetailUpdateDeleteView.as_view(),
        name="appointment_detail_update_delete",
    ),
]
