import arrow
from rest_framework import serializers

from appointment.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"

    def validate_appointment_time(self, appointment_time):
        if appointment_time < arrow.utcnow():
            raise serializers.ValidationError(
                "The appointment time cannot be in the past."
            )
        return appointment_time
