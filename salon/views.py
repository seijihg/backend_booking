from rest_framework.generics import ListCreateAPIView

from salon.models import Salon
from salon.serializers import SalonSerializer


# Create your views here.
class SalonListCreateAPIView(ListCreateAPIView):
    queryset = Salon.objects.all()
    serializer_class = SalonSerializer
