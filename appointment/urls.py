from django.urls import path
from appointment.views import AppointmentListCreateAPIView

app_name = "appointment"


urlpatterns = [
    path("", AppointmentListCreateAPIView.as_view(), name="appointments"),
]
