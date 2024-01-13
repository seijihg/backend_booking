from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from datetime import datetime

from appointment.serializers import AppointmentSerializer
from appointment.serializers import Appointment


# Create your views here.
class AppointmentListCreateAPIView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Access query parameters using self.request.GET
        date = self.request.GET.get("date")  # Example: ?date=2023-06-14
        if date:
            provided_date = datetime.strptime(date, "%Y-%m-%d")
            queryset = queryset.filter(appointment_time__date=provided_date)

        return queryset


class AppointmentDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
