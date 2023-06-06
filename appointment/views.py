from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from appointment.serializers import AppointmentSerializer
from appointment.serializers import Appointment


# Create your views here.
class AppointmentListCreateAPIView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
