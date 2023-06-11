from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from salon.models import Salon
from salon.serializers import SalonSerializer


# Create your views here.
class SalonListCreateAPIView(ListCreateAPIView):
    queryset = Salon.objects.all()
    serializer_class = SalonSerializer


class SalonDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = Salon.objects.all()
    serializer_class = SalonSerializer
